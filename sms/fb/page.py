import pyppeteer
import asyncio
from random import randint, random
from datetime import datetime
import re
import csv


# In the current version of pyppeteer, the browser is closed for every ~20 
# seconds. This bug isn't fixed yet. The following work around is provided by:
# https://github.com/pyppeteer/pyppeteer2/issues/6
def disable_timeout_pyppeteer():
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect
    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method

disable_timeout_pyppeteer()

class FacebookPage():
    pageName = ""
    afterDate = ""
    browser = None
    page = None
    launchArgs = {
        "headless": True,
        "ignoreHTTPSErrors": True,
        #"executablePath": '/Applications/Google Chrome.app'
        #"dumpio": True,
        # "logLevel": 10, # https://www.loggly.com/ultimate-guide/python-logging-basics/
        "args": ['--window-size=1400, 800']
    }
    posts = []

    def __init__(self, pageName, afterDate, launchArgs = {"headless": True}):
        self.pageName = pageName
        self.afterDate = afterDate
        for key in launchArgs.keys():
            self.launchArgs[key] = launchArgs[key]
    
    async def __aenter__(self):
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    async def launch(self):
        self.browser = await pyppeteer.launch(self.launchArgs)
        self.page = await self.browser.newPage()
        await self.page.goto(f"https://www.facebook.com/{self.pageName}/posts")
        await self.page.setViewport({'width': 1400, 'height': 800})
    
    async def close(self):
        await self.browser.close()
    
    async def fetchAll(self, fetchComments=False):
        self.fetchComments = fetchComments
        await self.loadPostsByDate()
        await self.loginDismiss()
        posts = await self.getAllPosts()
        for post in posts:
            postDate = await self.getPostDate(post)
            if postDate < self.afterDate:
                return
            await self.fetch(post)

    async def fetch(self, post):
        postMsg = await self.getPostMsg(post)
        if postMsg is None:
            return
        newPost = {}
        newPost["postMsg"] = postMsg
        newPost["datetime"] = await self.getPostDate(post)
        newPost["url"] = await self.getPostUrl(post)
        newPost["id"] = newPost["url"].split('/')[-1]
        newPost["reactionsCount"] = await self.getPostReactionsCount(post)
        newPost["commentsCount"] = await self.getPostCommentsCount(post)
        newPost["sharesCount"] = await self.getPostSharesCount(post)
        if self.fetchComments:
            if newPost["commentCount"] == 0:
                newPost["comments"] = []
            else:
                newPost["comments"] = await self.getPostComments(post)
        self.posts.append(newPost)
    
    async def loadPostsByDate(self):
        scrollFrom = 0
        while True:
            lastPost = (await self.page.querySelectorAll("._427x"))[-1]
            lastPostTime = await self.getPostDate(lastPost)
            if lastPostTime < self.afterDate:
                break

            try:
                await self.page.waitForSelector(".uiMorePagerPrimary", timeout = 1000)
            except asyncio.TimeoutError:
                break

            scrollTo = await self.page.evaluate(
                '''() => { return document.body.scrollHeight }'''
            )
            await self.page.evaluate(f'''() => {{
                window.scrollBy({scrollFrom}, {scrollTo});
            }}''')
            scrollFrom = scrollTo

    async def loginDismiss(self):
        await self.page.evaluate('''() => {
            window.scrollBy(0, document.body.scrollHeight/2);
        }''')
        # FIXME: login dialog dismiss button is not recognized normally
        while True:
            await asyncio.sleep(0.1)
            dialogStyle = await self.page.querySelectorEval(
                "._62uh", 'node => node.getAttribute("style")'
            )
            if dialogStyle is not None:
                await asyncio.sleep(0.1)
                break
                
        await self.page.mouse.move(0,0)
        await self.page.click("#expanding_cta_close_button")
    
    async def getAllPosts(self):
        return await self.page.querySelectorAll(
            "._4-u2.mbm._4mrt._5jmm._5pat._5v3q._7cqq._4-u8"
        )

    async def getPostDate(self, post):
        subtitleDiv = await post.querySelector("._5pcp._5lel._2jyu._232_")
        timestamp = await subtitleDiv.querySelectorEval("abbr", '''node => {
            return node.getAttribute("title")
        }''')
        return datetime.strptime(timestamp, "%A, %B %d, %Y at %I:%M %p")
    
    async def getPostMsg(self, post):
        postMessageDiv = await post.querySelector(
            "div[data-testid='post_message']"
        )
        if postMessageDiv is None:
            return None
        return await postMessageDiv.querySelectorEval("p", 'node => node.textContent')
    
    async def getPostUrl(self, post):
        url = await post.querySelectorEval(
            ".l_c3pyo2v0u._5eit.i_c3pynyi2f.clearfix span.z_c3pyo1brp  a._5pcq",
            'node => node.getAttribute("href")'
        )
        url = url.split("?")[0]
        if url.endswith("/"):
            url = re.sub("/$", "", url)
        return f"https://www.facebook.com{url}"
    
    async def getPostReactionsCount(self, post):
        reactionSpan = await post.querySelector("a span._3dlh._3dli span[data-hover='tooltip']")
        if reactionSpan is None:
            return 0
        await reactionSpan.hover()
        await self.page.mouse.move(0,0)
        await reactionSpan.hover()
        await self.page.waitForSelector("a span._3dlh._3dli span[data-hover='tooltip'][id]")
        reactionId = await post.querySelectorEval(
            "a span._3dlh._3dli  span[data-hover='tooltip'][id]",
            'node => node.getAttribute("id")'
        )
        await reactionSpan.hover()
        await self.page.querySelector(f"#{reactionId}")
        await self.page.waitForSelector(
            f"[data-ownerid='{reactionId}'] ul.uiList._4kg",
            timeout=10000
        )
        lis = await self.page.querySelectorAll(f"[data-ownerid='{reactionId}'] ul.uiList._4kg li")
        if len(lis) < 20:
            return len(lis)
        else:
            more = await self.page.querySelectorEval(
                f"[data-ownerid='{reactionId}'] ul.uiList._4kg",
                "node => node.lastChild.textContent"
            )
            more = re.sub("^.+ ([0-9,]+) .+$", '\\1', more)
            more = re.sub(",", "", more)
            more = int(more)
            return 19 + more
    
    async def getPostSharesCount(self, post):
        sharesCountSpan = await post.querySelector("span._355t._4vn2[data-hover='tooltip']")
        if sharesCountSpan is None:
            return 0
        await sharesCountSpan.hover()
        await self.page.mouse.move(0,0)
        await sharesCountSpan.hover()
        await self.page.waitForSelector("span._355t._4vn2[data-hover='tooltip'][id]")
        sharesCountId = await post.querySelectorEval(
            "span._355t._4vn2[data-hover='tooltip']",
            'node => node.getAttribute("id")'
        )
        await self.page.querySelector(f"#{sharesCountId}")
        await self.page.waitForSelector(f"[data-ownerid='{sharesCountId}'] ul.uiList._4kg")
        lis = await self.page.querySelectorAll(f"[data-ownerid='{sharesCountId}'] ul.uiList._4kg li")
        if len(lis) < 5:
           return len(lis)
        else:
           moreShares = await self.page.querySelectorEval(
               f"[data-ownerid='{sharesCountId}'] ul.uiList._4kg",
               "node => node.lastChild.textContent"
           )
           moreShares = re.sub("^.+ ([0-9,]+) .+$", '\\1', moreShares)
           moreShares = re.sub(",", "", moreShares)
           moreShares = int(moreShares)
           return 4 + moreShares

    async def getPostCommentsCount(self, post):
        commentsCountSpan = await post.querySelector(
            "span._1whp._4vn2[data-hover='tooltip']"
        )
        if commentsCountSpan is None:
            return 0
        await commentsCountSpan.hover()
        await self.page.mouse.move(0,0)
        await commentsCountSpan.hover()
        await self.page.waitForSelector("span._1whp._4vn2[data-hover='tooltip'][id]")
        commentsCountId = await post.querySelectorEval(
            "span._1whp._4vn2[data-hover='tooltip']",
            'node => node.getAttribute("id")'
        )
        await self.page.querySelector(f"#{commentsCountId}")
        try:
            await self.page.waitForSelector(
                f"[data-ownerid='{commentsCountId}'] ul.uiList._4kg"
            )
        except asyncio.TimeoutError as e:
            await self.page.waitForSelector(
                f"[data-ownerid='{commentsCountId}'] .tooltipContent>div>div"
            )
            tooltipContent = await self.page.querySelectorEval(
                f"[data-ownerid='{commentsCountId}'] .tooltipContent>div>div",
                "node => node.textContent"
            )
            if tooltipContent == "No visible comments":
                return 0
            else:
                raise asyncio.TimeoutError(e)
        lis = await self.page.querySelectorAll(f"[data-ownerid='{commentsCountId}'] ul.uiList._4kg li")
        if len(lis) < 20:
            return len(lis)
        else:
            moreComments = await self.page.querySelectorEval(
                f"[data-ownerid='{commentsCountId}'] ul.uiList._4kg",
                "node => node.lastChild.textContent"
            )
            moreComments = re.sub("^.+ ([0-9,]+) .+$", '\\1', moreComments)
            moreComments = re.sub(",", "", moreComments)
            moreComments = int(moreComments)
            return 19 + moreComments
    
    async def getPostComments(self, post):
        postFetchId = await post.querySelectorEval(
            '._4-u2.mbm._4mrt._5jmm._5pat._5v3q._7cqq._4-u8',
            'node => node.getAttribute("id")'
        )
        while True:
            try:
                await self.page.waitForSelector(
                    f"#{postFetchId} ._7a94._7a9d a._4sxc._42ft",
                    timeout = 1000
                )
                moreCommentsBtn = await self.page.querySelector(
                    f"#{postFetchId} ._7a94._7a9d a._4sxc._42ft"
                )
                await self.page.click(f"#{postFetchId} ._7a94._7a9d a._4sxc._42ft")
            except asyncio.TimeoutError:
                break
            except pyppeteer.errors.ElementHandleError:
                break
            except pyppeteer.errors.PageError:
                break
        commentSpans = await post.querySelectorAll("[aria-label='Comment'] span._3l3x")
        comments = []
        for commentSpan in commentSpans:
            seeMoreBtn = await commentSpan.querySelector("a._5v47.fss[role='button']")
            if seeMoreBtn is not None:
                await seeMoreBtn.click({'delay': random()*300})
                moreSpan = await commentSpan.querySelector("span>span>span")
                while moreSpan is None:
                    await asyncio.sleep(0.1)
                    moreSpan = await commentSpan.querySelector("span>span>span")
                texts = await commentSpan.querySelectorAllEval(
                    ":scope>span",  """nodes => {
                        let texts;
                        texts = [];
                        for(let i = 0; i < nodes.length; i++){
                            texts.push(nodes[i].textContent);
                        }
                        return texts
                    }"""
                )
                comment = " ".join(texts)
            else:
                try:
                    comment = await commentSpan.querySelectorEval(
                        'span', 'node => node.textContent'
                    )
                except pyppeteer.errors.ElementHandleError:
                    continue
            comments.append(comment)
            return comments
