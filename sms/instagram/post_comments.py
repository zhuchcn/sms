import asyncio
from pyppeteer import launch
from random import randint, random
import argparse
import os
import csv
import re


_PAGE_UNAVAILABLE_ERROR = "Sorry, this page isn't available."
_PAGE_CANT_OPEN_ERROR = "Page can't be opened."

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

class InstagramPostComments():
    browser = None
    page = None
    comments = {}
    post = {
        "postId": None,
        "url": None,
        "username": None,
        "likeCount": None,
        "postContent": None,
        "commentCount": None,
    }
    launchArgs = {
        "headless": True,
        "ignoreHTTPSErrors": True,
        #"executablePath": '/Applications/Google Chrome.app'
        #"dumpio": True,
        # "logLevel": 10, # https://www.loggly.com/ultimate-guide/python-logging-basics/
        "args": ['--window-size=1366, 850']
    }

    def __init__(self, url=None, postId=None, launchArgs = {"headless": True}):
        if url:
            if url.startswith("www"):
                url = "https://" + url
            if not url.startswith("https://www.instagram.com/p/"):
                raise ValueError(f"InstagramPostComments(): url {url} invalid")
            self.post["url"] = url
            self.post["postId"] = re.sub(
                "^https://www.instagram.com/p/(\S+?)/{0,1}$", r'\1', url
            )
        elif postId:
            self.post["url"] = f"https://www.instagram.com/p{postId}/"
            self.post["postId"] = postId
        else:
            raise ValueError(
        "InstagramPostComments(): at least one of url or postId must be given."
        )
        for key in self.launchArgs.keys():
            if key in launchArgs.keys():
                self.launchArgs[key] = launchArgs[key]
    
    async def __aenter__(self):
        await self.launch()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    async def launch(self):
        self.browser = await launch(self.launchArgs)
        self.page = await self.browser.newPage()
        await self.page.goto(self.post["url"])
        await self.page.setViewport({'width': 1366, "height": 750})
        h2Error = await self.page.querySelector("div.error-container h2")
        if h2Error:
            h2Error = await h2Error.getProperty("textContent")
            h2Error = await h2Error.jsonValue()
            if h2Error == _PAGE_UNAVAILABLE_ERROR:
                await self.close()
                raise ValueError(h2Error)
        while True:
            try:
                await self.page.waitForSelector("button.dCJp8.afkep", timeout = 1000)
                await self.page.click("button.dCJp8.afkep", {'delay': random() * 300})
            except asyncio.TimeoutError as e:
                break
        if await self.pageIsEmpty():
            await self.close()
            raise ValueError(_PAGE_CANT_OPEN_ERROR)

    async def getPost(self):
        username = await self.page.querySelector("div.e1e1d a")
        username = await username.getProperty("textContent")
        username = await username.jsonValue()
        
        likeCount = await self.page.querySelector(".Nm9Fw button.sqdOP.yWX7d span")
        if likeCount is None:
            likeCount = await self.page.querySelector(".Nm9Fw button.sqdOP.yWX7d")
        if likeCount is None:
            likeCount = 0
        else:
            likeCount = await likeCount.getProperty("textContent")
            likeCount = await likeCount.jsonValue()
            likeCount = re.sub(",", "",likeCount)
            likeCount = re.sub(" like", "",likeCount)
            likeCount = int(likeCount)

        postContent = await self.page.querySelector("[role=\"button\"].ZyFrc .C4VMK span, h1")
        if postContent:
            postContent = await postContent.getProperty("textContent")
            postContent = await postContent.jsonValue()
        else:
            postContent = None

        self.post["username"] = username
        self.post["likeCount"] = likeCount
        self.post["postContent"] = postContent
    
    async def getComments(self):
        commentUls = await self.page.querySelectorAll("ul.Mr508")
        self.comments = []
        if len(commentUls) == 0:
            self.post["commentCount"] = 0
            return

        for ul in commentUls:
            user = await ul.querySelector("h3._6lAjh")
            user = await user.getProperty("textContent")
            user = await user.jsonValue()
            comment = await ul.querySelector("div.C4VMK span")
            comment = await comment.getProperty("textContent")
            comment = await comment.jsonValue()
            self.comments.append({
                'postId': self.post["postId"], 'user': user, "comment": comment
            })
        self.post["commentCount"] = len(self.comments)
    
    async def close(self):
        await self.browser.close()
    
    async def pageIsEmpty(self):
        isEmpty = await self.page.evaluate('''()=>{
            const root = document.querySelector("#react-root")
            return root.innerHTML === ""
        }''')
        if isEmpty:
            return True
        
        res = await self.page.querySelector("main ._07DZ3")
        if res is not None:
            res = await res.getProperty("textContent")
            res = await res.jsonValue()
            if re.search("this page isn't available", res):
                return True
        
        return False


async def getPostComments(url, launchArgs = {"headless": True}):
    async with InstagramPostComments(url, launchArgs=launchArgs) as ipc:
        await ipc.getPost()
        await ipc.getComments()
        return ipc


async def main():
    parser = argparse.ArgumentParser(
        description="Get Instagram post and comments"
    )
    parser.add_argument(
        '-i', '--input-path', type=str,
        help="Path to the input file. Must be a text file with post url in " +
             "row. The pattern of urls must be https://www.instagram.com/p/xxx/"
    )
    parser.add_argument(
        '-p', '--file-posts', type=str,
        help="The output csv file for posts."
    )
    parser.add_argument(
        '-c', '--file-comments', type=str,
        help="The output csv file for comments."
    )
    parser.add_argument(
        '-r', '--resume', action="store_true",
        help="Resume stopped job."
    )
    parser.add_argument(
        '-f', '--force', action="store_true",
        help="Whether to overwrite the csv files for posts and comments."
    )
    parser.add_argument(
        '-d', '--delay', type=int,
        help="Number of seconds to delay between requests."
    )
    parser.add_argument(
        '-n', '--non-headless', action="store_false",
        help="Whether to run in a non-headless mode."
    )
    parser.add_argument(
        '-u', '--user-data-dir', type=str,
        help="Path to a user data directory."
    )
    parser.add_argument(
        '--no-sandbox', action="store_true",
        help="will be parsed to launchArgs"
    )

    args = parser.parse_args()

    # launch arguments
    launchArgs = {"headless": args.non_headless}
    if args.no_sandbox:
        launchArgs["args"] = ["--no-sandbox"]
        
    if args.user_data_dir:
        launchArgs["userDataDir"] = args.user_data_dir

    if args.force and args.resume:
        raise parser.error("can't use both -f/--force and -r/--resume")

    if not args.force and not args.resume:
        if os.path.isfile(args.file_posts):
            raise parser.error(
                "-p/--file-posts: file already exists. " +
                "Use -f/--force to overwrite."
            )
        if os.path.isfile(args.file_comments):
            raise parser.error(
                "-p/--file-comments: file already exists. " +
                "Use -f/--force to overwrite."
            )
            
    if args.resume:
        with open(args.file_posts, newline="") as csvfile:
            spamreader = csv.reader(csvfile, delimiter=",", quotechar='"')
            for row in spamreader:
                resumeUrl = row[1]

    if args.force:
        if os.path.isfile(args.file_posts):
            os.remove(args.file_posts)
        if os.path.isfile(args.file_comments):
            os.remove(args.file_comments)
    
    with open(args.input_path, "rt") as fh, \
            open(args.file_posts, "a", newline="") as file_posts, \
            open(args.file_comments, 'a', newline="") as file_comments:
        posts_fieldnames = ["postId", "url", "username", "likeCount",
                            "postContent", "commentCount"]
        postsWriter = csv.DictWriter(
            file_posts, fieldnames=posts_fieldnames,
            quoting=csv.QUOTE_ALL
        )
        comments_fieldnames = ["postId", "user", "comment"]
        commentsWriter = csv.DictWriter(
            file_comments, fieldnames=comments_fieldnames,
            quoting=csv.QUOTE_ALL
        )

        if not args.resume:
            commentsWriter.writeheader()
            postsWriter.writeheader()

        resumeUrlFound = False
        for l in fh:
            url = l.rstrip()
            if args.resume:
                if resumeUrlFound is False:
                    if url != resumeUrl:
                        continue
                    else:
                        resumeUrlFound = True
                        continue
            
            try:
                ipc = await getPostComments(url, launchArgs=launchArgs)
            except ValueError as e:
                if str(e) == _PAGE_UNAVAILABLE_ERROR:
                    print(f"the url {url} is not available.", flush=True)
                    continue
                if str(e) == _PAGE_CANT_OPEN_ERROR:
                    print(f"the url {url} can't be opened.", flush=True)
                    continue
                else:
                    raise e

            postsWriter.writerow(ipc.post)
            commentsWriter.writerows(ipc.comments)
            if args.delay > 0:
                delay_add = (random() - 0.5) * args.delay / 2
                print(f"sleeping for {args.delay} + {delay_add} seconds..", flush=True)
                await asyncio.sleep(args.delay + delay_add)

def mainWrapper():
    asyncio.run(main())

if __name__ == "__main__":
    mainWrapper()