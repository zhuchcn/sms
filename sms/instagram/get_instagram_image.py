import requests
import re
import argparse
import os
import math
from pathos.multiprocessing import ProcessingPool as Pool


class InstagramImageCrawler():
    baseurl = "https://api.instagram.com/oembed/?url="
    input_path = None
    output_dir = None
    nthreads = 1
    prefix_index = False
    verbose = False

    def __init__(self, input_path, output_path, nthreads, verbose, prefix_index):
        self.input_path = input_path
        self.output_dir = output_path
        self.nthreads = nthreads
        self.verbose = verbose
        self.prefix_index = prefix_index
        self.crawl_images()
    
    def crawl_images(self):
        if self.prefix_index:
            line_count = 0
            with open(self.input_path, "rt") as fh:
                for l in fh:
                    line_count += 1
            index_width = int(math.log10(line_count)) + 1
        with open(self.input_path, "rt") as fh:
            i = 1
            if self.nthreads == 1:
                for line in fh:
                    prefix = format(i, f"0{index_width}d") + "_" \
                                    if self.prefix_index else None
                    self.get_image(line.rstrip(), prefix)
                    i += 1
            else:
                urls = []
                prefixs = []
                for line in fh:
                    urls.append(line.rstrip())
                    prefixs.append(format(i, f"0{index_width}d") + "_" \
                                   if self.prefix_index else None)
                    i += 1
                    if len(urls) == self.nthreads:
                        Pool().map(self.get_image, urls, prefixs)
                        urls = []
                        prefixs = []
                Pool().map(self.get_image, urls, prefixs)

    def get_image(self, url, prefix):
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
        output_file = post_id + ".jpg"
        if prefix:
            output_file = prefix + output_file
        output_file = os.path.join(self.output_dir, output_file)
        with open(output_file, "wb") as fh:
            fh.write(res.content)
        if self.verbose:
            print(f"{url} image saved")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-path', type=str)
    parser.add_argument('-o', '--output-path', type=str)
    parser.add_argument('-n', "--nthreads", type=int, default=1)
    parser.add_argument('-p', '--prefix-index', action="store_true")
    parser.add_argument('-v', '--verbose', action="store_true")
    args = parser.parse_args()

    if not os.path.isdir(args.output_path):
        raise argparse.ArgumentTypeError("-o/--output-path does not exist.")

    if args.nthreads < 0:
        raise argparse.ArgumentTypeError("-n/--nthreads must be larger than 0.")

    InstagramImageCrawler(args.input_path, args.output_path, args.nthreads, 
                          args.verbose, args.prefix_index)

if __name__ == "__main__":
    main()
    