from .get_page_posts import parse_args as parser_get_page_posts
from .get_post_from_url import parse_args as parser_get_post_from_url
import argparse
import sys


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="commands", dest="command")
    parser_get_page_posts(subparsers)
    parser_get_post_from_url(subparsers)
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()