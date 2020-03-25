from .post import FacebookPost
import asyncio
from datetime import datetime
import argparse
import csv


async def getPost(url):
    async with FacebookPost(url) as fb:
        await fb.openPage()
        return await fb.fetchData()

def parse_args(subparsers):
    parser = subparsers.add_parser(
        name="post",
        description="get posts from url",
        help="get posts from url"
    )
    parser.set_defaults(func=mainWrapper)
    parser.add_argument(
        "input_file", type=str, help="""List of urls to facebook pages. Must
        be a text file. Each line must has only one url."""
    )
    parser.add_argument(
        "output_file", type=str, help="Output csv path."
    )

async def main(args):
    with open(args.input_file, "rt") as ih, \
            open (args.output_file, "wt") as oh:
        writer = csv.DictWriter(
            oh, ["url", "content", "timestamp", "reactions_count", 
            "comments_count", "shares_count"],
            quoting=csv.QUOTE_NONNUMERIC
        )
        writer.writeheader()
        for line in ih:
            url = line.rstrip()
            try:
                post = await getPost(url)
                print(f"{url} saved")
                writer.writerow(post)
            except ValueError as e:
                if e.args[0] == "Page not available.":
                    print(f"{url} inavailable")
                else:
                    raise ValueError(e)


def mainWrapper(args):
    asyncio.run(main(args))