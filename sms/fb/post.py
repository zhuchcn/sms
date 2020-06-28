import pyppeteer
import asyncio
from random import randint, random
from datetime import datetime
import re
import csv

from utils import disable_timeout_pyppeteer

disable_timeout_pyppeteer()

class FacebookPost():
    browser = None
    page = None
    logedIn = False
    launchArgs = {
        "headless": True,
        "ignoreHTTPSErrors": True,
        #"executablePath": '/Applications/Google Chrome.app'
        #"dumpio": True,
        # "logLevel": 10, # https://www.loggly.com/ultimate-guide/python-logging-basics/
        "args": ['--window-size=1400, 800']
    }

    def __init__(self, launchArgs={"headless": True}):
        for key in launchArgs.keys():
            self.launchArgs[key] = launchArgs[key]
    
    async def __aenter__(self):
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    async def launch(self):
        self.browser = await pyppeteer.launch(self.launchArgs)
    
    async def close(self):
        await self.browser.close()

    async def openPage(self, url):
        self.page = await self.browser.newPage()
        await self.page.goto(url)
        await self.page.setViewport({'width': 1400, 'height': 800})
        if not await self.pageIsAvailable():
            raise ValueError("Page not available.")
        if not self.logedIn:
            await self.loginDismiss()

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

        await self.page.waitForSelector("._5hn6")
        await self.page.querySelectorEval("._5hn6", """
            node => node.setAttribute("style", "display: none;")
        """)

    async def pageIsAvailable(self):
        try:
            div = await self.page.waitForSelector("._585n._3-8n")
            msg = await div.querySelectorEval(
                "div._585r._50f4", "node => node.textContent"
            )
            if msg == "You must log in to continue.":
                return False
            return True
        except asyncio.TimeoutError:
            return True

    async def fetch(self, url):
        await self.openPage(url)
        post = await self.getPost()
        return {
            "url": url,
            "content": await self.getPostMsg(post),
            "timestamp": await self.getPostDate(post),
            "reactions_count": await self.getReactionsCount(post),
            "comments_count": await self.getPostCommentsCount(post),
            "shares_count": await self.getPostSharesCount(post)
        }

    async def getPost(self):
        return await self.page.querySelector(".userContentWrapper")
    
    async def getPostMsg(self, post):
        postMessageDiv = await post.querySelector(
            "div[data-testid='post_message']"
        )
        if postMessageDiv is None:
            return None
        try:
            return await postMessageDiv.querySelectorEval(
                "p", 'node => node.textContent'
            )
        except pyppeteer.errors.ElementHandleError:
            return None
    
    async def getPostDate(self, post):
        timestamp =  await post.querySelectorEval(
            ".timestampContent", 
            "node => node.parentElement.getAttribute('title')"
        )
        timestamp = datetime.strptime(timestamp, "%A, %B %d, %Y at %I:%M %p")
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    async def getReactionsCount(self, post):
        reactionSpan = await post.querySelector(
            "a span._3dlh._3dli span[data-hover='tooltip']"
        )
        if reactionSpan is None:
            return 0

        await reactionSpan.hover()
        await self.page.mouse.move(0,0)
        await reactionSpan.hover()

        await self.page.waitForSelector(
            "a span._3dlh._3dli span[data-hover='tooltip'][id]",
            timeout = 10000
        )
        reactionId = await post.querySelectorEval(
            "a span._3dlh._3dli span[data-hover='tooltip'][id]",
            'node => node.getAttribute("id")'
        )
 
        await reactionSpan.hover()
        await self.page.querySelector(f"#{reactionId}")
        await self.page.waitForSelector(
            f"[data-ownerid='{reactionId}'] ul.uiList._4kg",
            timeout=10000
        )
        lis = await self.page.querySelectorAllEval(
            f"[data-ownerid='{reactionId}'] ul.uiList._4kg li",
            """nodes => {
                let lis = []
                for(let i = 0; i < nodes.length; i++) {
                    lis.push(nodes[i].textContent)
                }
                return lis
            }"""
        )
        if bool(re.match("^and [0-9,]+ more…$", lis[-1])):
            more = re.sub("^.+ ([0-9,]+) .+$", '\\1', lis[-1])
            more = re.sub(",", "", more)
            more = int(more)
            return len(lis) - 1  + more
        return len(lis)
    
    async def getPostSharesCount(self, post):
        sharesCountSpan = await post.querySelector(
            "span._355t._4vn2[data-hover='tooltip']"
        )
        if sharesCountSpan is None:
            return 0
        await sharesCountSpan.hover()
        await self.page.mouse.move(0,0)
        await sharesCountSpan.hover()
        await self.page.waitForSelector(
            "span._355t._4vn2[data-hover='tooltip'][id]"
        )
        sharesCountId = await post.querySelectorEval(
            "span._355t._4vn2[data-hover='tooltip']",
            'node => node.getAttribute("id")'
        )
        await self.page.querySelector(f"#{sharesCountId}")
        await self.page.waitForSelector(
            f"[data-ownerid='{sharesCountId}'] ul.uiList._4kg"
        )
        lis = await self.page.querySelectorAllEval(
            f"[data-ownerid='{sharesCountId}'] ul.uiList._4kg li",
            """nodes => {
                let lis = []
                for(let i = 0; i < nodes.length; i++) {
                    lis.push(nodes[i].textContent)
                }
                return lis
            }"""
        )
        if bool(re.match("^and [0-9,]+ more…$", lis[-1])):
            moreShares = re.sub("^.+ ([0-9,]+) .+$", '\\1', lis[-1])
            moreShares = re.sub(",", "", moreShares)
            moreShares = int(moreShares)
            return len(lis) - 1  + moreShares
        return len(lis)

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
        lis = await self.page.querySelectorAllEval(
            f"[data-ownerid='{commentsCountId}'] ul.uiList._4kg li",
            """nodes => {
                let lis = []
                for(let i = 0; i < nodes.length; i++) {
                    lis.push(nodes[i].textContent)
                }
                return lis
            }"""
        )
        if bool(re.match("^and [0-9,]+ more…$", lis[-1])):
            more = re.sub("^.+ ([0-9,]+) .+$", '\\1', lis[-1])
            more = re.sub(",", "", more)
            more = int(more)
            return len(lis) - 1  + more
        return len(lis)
    
    async def login(self, email, password):
        loginPage = await self.browser.newPage()
        await loginPage.setViewport({'width': 1400, 'height': 800})
        await loginPage.goto("https://www.facebook.com")
        await loginPage.querySelectorEval(
            "#email", f"node => node.setAttribute('value', '{email}')"
        )
        await loginPage.querySelectorEval(
            "#pass", f"node => node.setAttribute('value', '{password}')"
        )
        await asyncio.wait([
            loginPage.click("#loginbutton"),
            loginPage.waitForNavigation()
        ])
        self.logedIn = True
        
        