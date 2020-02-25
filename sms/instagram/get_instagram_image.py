import requests
import re
import argparse
import os
from pathos.multiprocessing import ProcessingPool as Pool


class InstagramImageCrawler():
    baseurl = "https://api.instagram.com/oembed/?url="
    input_path = None
    output_dir = None
    nthreads = 1
    verbose = False

    def __init__(self, input_path, output_path, nthreads, verbose):
        self.input_path = input_path
        self.output_dir = output_path
        self.nthreads = nthreads
        self.verbose = verbose
        self.crawl_images()
    
    def crawl_images(self):
        with open(self.input_path, "rt") as fh:
            if self.nthreads == 1:
                for line in fh:
                    self.get_image(line.rstrip())
            else:
                urls = []
                for line in fh:
                    urls.append(line.rstrip())
                    if len(urls) == self.nthreads:
                        Pool().map(self.get_image, urls)
                        urls = []
                Pool().map(self.get_image, urls)

    def get_image(self, url):
        res = requests.get(f"{self.baseurl}{url}")
        if res.status_code != 200:
            if self.verbose:
                print(f"{url} not found")
            return
        res = requests.get(res.json()["thumbnail_url"])
        if res.status_code != 200:
            if self.verbose:
                print(f"{url} not found")
            return
        
        post_id = re.sub("^https://www.instagram.com/p/(.+)/", "\\1", url)
        output_file = os.path.join(self.output_dir, post_id + ".jpg")
        with open(output_file, "wb") as fh:
            fh.write(res.content)
        if self.verbose:
            print(f"{url} image saved")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-path', type=str)
    parser.add_argument('-o', '--output-path', type=str)
    parser.add_argument('-n', "--nthreads", type=int, default=1)
    parser.add_argument('-v', '--verbose', action="store_true")
    args = parser.parse_args()

    if not os.path.isdir(args.output_path):
        raise argparse.ArgumentTypeError("-o/--output-path does not exist.")

    if args.nthreads < 0:
        raise argparse.ArgumentTypeError("-n/--nthreads must be larger than 0.")

    InstagramImageCrawler(args.input_path, args.output_path, args.nthreads, 
                          args.verbose)

if __name__ == "__main__":
    main()
    