import asyncio
from pyppeteer import launch
from random import randint, random
import argparse
import os
import csv


class InstagramPostComments():
    url = None
    browser = None
    page = None
    comments = {}
    post = {
        "username": None,
        "likeCount": None,
        "postContent": None,
        "commentCount": None
    }

    def __init__(self, url):
        self.url = url
    
    async def __aenter__(self):
        await self.launch()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    async def launch(self):
        self.browser = await launch()
        self.page = await self.browser.newPage()
        try:
            await self.page.goto(self.url)
        except pyppeteer.error as e:
            print(self.url)
            raise e
        while True:
            try:
                await self.page.waitForSelector("button.dCJp8.afkep", timeout = 1000)
                await self.page.click("button.dCJp8.afkep", {'delay': random() * 300})
            except asyncio.TimeoutError as e:
                break

    async def getPost(self):
        username = await self.page.querySelector("div.e1e1d a")
        username = await username.getProperty("textContent")
        username = await username.jsonValue()
        
        likeCount = await self.page.querySelector("button.sqdOP.yWX7d span")
        likeCount = await likeCount.getProperty("textContent")
        likeCount = await likeCount.jsonValue()
        likeCount = int(likeCount.replace(",", ""))

        postContent = await self.page.querySelector("[role=\"button\"].ZyFrc .C4VMK span")
        postContent = await postContent.getProperty("textContent")
        postContent = await postContent.jsonValue()

        self.post["username"] = username
        self.post["likeCount"] = likeCount
        self.post["postContent"] = postContent
    
    async def getComments(self):
        commentUls = await self.page.querySelectorAll("ul.Mr508")
        self.comments = []
        for ul in commentUls:
            user = await ul.querySelector("h3._6lAjh")
            user = await user.getProperty("textContent")
            user = await user.jsonValue()
            comment = await ul.querySelector("div.C4VMK span")
            comment = await comment.getProperty("textContent")
            comment = await comment.jsonValue()
            self.comments.append({'user': user, "comment": comment})
        self.post["commentCount"] = len(self.comments)
    
    async def close(self):
        await self.browser.close()


async def getPostComments(url):
    async with InstagramPostComments(url) as ipc:
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
        '-f', '--force', action="store_true",
        help="Whether to overwrite the csv files for posts and comments."
    )
    parser.add_argument(
        '-d', '--delay', type=int,
        help="Number of seconds to delay between requests."
    )
    args = parser.parse_args()

    if not args.force:
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
    
    with open(args.input_path, "rt") as fh:
        with open(args.file_posts, "w", newline="") as file_posts, \
            open(args.file_comments, 'w', newline="") as file_comments:
            posts_fieldnames = ["username", "likeCount",
                               "postContent", "commentCount"]
            postsWriter = csv.DictWriter(
                file_posts, fieldnames=posts_fieldnames,
                quoting=csv.QUOTE_ALL
            )
            postsWriter.writeheader()

            comments_fieldnames = ["user", "comment"]
            commentsWriter = csv.DictWriter(
                file_comments, fieldnames=comments_fieldnames,
                quoting=csv.QUOTE_ALL
            )
            commentsWriter.writeheader()
            for l in fh:
                ipc = await getPostComments(l.rstrip())
                postsWriter.writerow(ipc.post)
                commentsWriter.writerows(ipc.comments)
                if args.delay > 0:
                    print(f"sleeping for {args.delay} seconds..")
                    await asyncio.sleep(args.delay)

def mainWrapper():
    asyncio.run(main())

if __name__ == "__main__":
    mainWrapper()