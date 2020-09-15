import requests
from datetime import datetime, timedelta
import argparse


def authenticat(username, password):
    url = "https://api.crimsonhexagon.com/api/authenticate"
    querystring = { 
        "username": username, 
        "noExpiration": "true", 
        "password": password 
    }
    response = requests.request("GET", url, params=querystring)
    return response.json()

def get_twitter_posts(auth, monitor_id, start, end):
    url = "https://api.crimsonhexagon.com/api/monitor/posts"
    querystring = {
        "auth": auth["auth"],
        "id": monitor_id,
        "start": start,
        "end": end,
        "extendLimit": True
    }
    res = requests.request("GET", url, params=querystring)
    res = res.json()
    return res

def write_twitter_posts(posts, filepath):
    with open(filepath, "wt") as fh:
        for post in posts:
            fh.write(post["url"] + "\n")

def main():
    args = parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    days = end_date - start_date
    auth = authenticat(args.username, args.password)
    for i in range(days.days):
        start = (start_date + timedelta(days = i)).strftime("%Y-%m-%d")
        end = (start_date + timedelta(days = i + 1)).strftime("%Y-%m-%d")
        posts = get_twitter_posts(
            auth,
            args.monitor_id,
            start,
            end
        )["posts"]
        filename = args.output_dir + "/" + start + "_" + end + ".txt"
        write_twitter_posts(posts, filename)
        print(f"posts url saved: {start} to {end}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--username", type=str,
        help="Crimson Hexagon username"
    )
    parser.add_argument(
        "-p", "--password", type=str,
        help="password"
    )
    parser.add_argument(
        "-i", "--monitor-id", type=str,
        help="Monitor ID"
    )
    parser.add_argument(
        "-s", "--start-date", type=str,
        help="Start date, must be YYYY-MM-DD"
    )
    parser.add_argument(
        "-e", "--end-date", type=str,
        help="End date, must be YYYY-MM-DD"
    )
    parser.add_argument(
        "-o", "--output-dir", type=str,
        help="Output directory"
    )
    return parser.parse_args()

if __name__ == "__main__":
    main()
