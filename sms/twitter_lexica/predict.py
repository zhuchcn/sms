import re
import os
from pandas import read_csv
import argparse
from tweepy import TweepError

from .TwitterLexica import TwitterLexica


def parse_args():
    parser = argparse.ArgumentParser(
        prog="twitter-lexica",
        description = """
    Predict Twitter user's age and gender using Lexica
    (https://github.com/wwbp/lexica).

    Twitter's python API tweepy (https://www.tweepy.org/) is used
    to request data. Four shell environmental variables MUST be
    set in order to let tweepy run successfully using the commands
    below in your terminal (replace place holders to your own value).

    export CONSUMER_KEY=\"your_value\"
    export CONSUMER_SECRETE=\"your_value\"
    export ACCESS_KEY=\"your_value\"
    export ACCESS_SECRETE=\"your_value\"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-s", "--screen-name", type=str, default=None,
        help="Twitter user name"
    )
    parser.add_argument(
        "-i", "--input-file", type=str, default=None,
        help="TXT file with each twitter user name on each line"
    )
    parser.add_argument(
        '-o', '--output-file', type=str, default=None,
        help="The output file for predicted Age and Gender"
    )
    parser.add_argument(
        '-d', '--output-dir', default=None,
        help="""
        The diractory to save user twitters. Twitters won't save if this is not 
        given
        """
    )
    parser.add_argument(
        '-m', '--max-tweets', default=200, type=int,
        help="Max number of most recent twitters to use."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    if args.screen_name:
        if args.input_file:
            print("The input file is ignored")
        try:
            tl = TwitterLexica(args.screen_name, args.max_tweets)
            if args.output_dir:
                tl.save_twitters(args.output_dir)
            age, gender = tl.predict() if tl.tweets else (None, None)
        except TweepError as e:
            if e.api_code == 34:
                print(f"user {args['screen_name']} was not found")
            else:
                print(e)
            tl = None
            age, gender = None, None
            
        if args.output_file:
            if tl is None:
                num_tweets = 0
            elif tl.tweets:
                num_tweets = len(tl.tweets)
            else:
                num_tweets = 0
            with open(args.output_file, "w") as fh:
                fh.write("user name\tnum tweets\tage\tgender\n")
                fh.write(f"{args.screen_name}\t{num_tweets}\t{age}\t{gender}\n")
        elif tl is not None:
            print(f"""Username: {tl.user_name}
Lexica prediction base on {len(tl.tweets) if tl.tweets else 0} tweets:
    Age: {age},
    Gender: {gender}""")

    elif args.input_file:
        if not args.output_file:
            raise ValueError("--output-file must not be None")
        
        with open(args.output_file, "w") as fh:
            fh.write("user name\tnum tweets\tage\tgender\n")
        
        with open(args.input_file,"r") as fh:
            for line in fh:
                screen_name = line.rstrip()
                screen_name = re.sub('^"|"$', "", screen_name)
                screen_name = re.sub("^'|'$", "", screen_name)
                
                if not screen_name.startswith("@"):
                    continue
                try:
                    tl = TwitterLexica(screen_name, args.max_tweets)
                    if args.output_dir:
                        tl.save_twitters(args.output_dir)

                    age, gender = tl.predict() if tl.tweets else (None, None)

                except TweepError as e:
                    if e.api_code == 34:
                        print(f"user {screen_name} was not found")
                    else:
                        print(e)
                    age, gender = None, None
                    tl = None

                with open(args.output_file, "a") as fh:
                    if tl is None:
                        num_tweets = 0
                    elif tl.tweets:
                        num_tweets = len(tl.tweets)
                    else:
                        num_tweets = 0
                    fh.write(f"{screen_name}\t{num_tweets}\t{age}\t{gender}\n")
                print(f"user {screen_name} was saved")
                if args.output_dir:
                    if tl is not None:
                        tl.save_twitters(args.output_dir)

if __name__ == "__main__":          
    main()            
