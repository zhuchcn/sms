import tweepy
import os
import nltk
import string
import csv
import re
from .Lexica import Lexica

class TwitterLexica():
    def __init__(self, screen_name, max_tweets=200, count=200):
        self.api_setup()
        self.lexica = Lexica()
        self.user_name = screen_name
        self.tweets = self.get_tweets(screen_name, max_tweets, count)
        
    def __repr__(self):
        return f"<TwitterLexica: {self.user_name}>"
    
    def api_setup(self):

        consumer_key = os.environ.get("CONSUMER_KEY")
        consumer_secrete = os.environ.get("CONSUMER_SECRETE")
        access_key = os.environ.get("ACCESS_KEY")
        access_secrete = os.environ.get("ACCESS_SECRETE")

        if consumer_key is None :
            raise ValueError("CONSUMER_KEY is not found. See -h/--help.")
        if consumer_secrete is None:
            raise ValueError("CONSUMER_SECRETE is not found. See -h/--help.")
        if access_key is None:
            raise ValueError("ACCESS_KEY is not found. See -h/--help.")
        if access_secrete is None:
            raise ValueError("ACCESS_SECRETE is not found. See -h/--help.")

        auth = tweepy.OAuthHandler(consumer_key, consumer_secrete)
        auth.set_access_token(access_key, access_secrete)
        self.api = tweepy.API(auth)

    def get_tweets(self, screen_name, max_tweets, count=200):
        max_request = 10
        alltweets = []

        new_tweets = self.fetch_tweets(screen_name, count)
        if len(new_tweets) == 0:
            print(f"user {screen_name} has 0 tweets")
            return alltweets
        
        oldest = new_tweets[-1][0] - 1
        new_tweets = [tweet for tweet in new_tweets \
                    if not tweet[2].startswith('RT @')]
        alltweets.extend(new_tweets)

        i = 0
        while len(new_tweets) > 0:
            new_tweets = self.fetch_tweets(screen_name, count, max_id=oldest)    
            if len(new_tweets) == 0:
                print(f"user {screen_name} has 0 tweets")
                return alltweets

            oldest = new_tweets[-1][0] - 1
            new_tweets = [tweet for tweet in new_tweets \
                        if not tweet[2].startswith('RT @')]
            alltweets.extend(new_tweets)
            
            if(len(alltweets) > max_tweets):
                alltweets = alltweets[:max_tweets]
                return alltweets
            
            i += 1
            if i >= max_request:
                return alltweets

    def fetch_tweets(self, screen_name, count, **kwargs):
        new_tweets = self.api.user_timeline(
            screen_name=screen_name,
            count=count,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True,
            **kwargs
        )
        new_tweets = [
            (tweet.id, tweet.created_at, tweet.text) \
                for tweet in new_tweets
        ]
        return new_tweets
    
    def get_freq(self):
        strings = [tweet[2] for tweet in self.tweets]
        strings = [re.sub("http?:\/\/.*[\r\n]*", "", s) for s in strings]
        strings = [re.sub("\/\/.*[\r\n]*", "", s) for s in strings]
        strings = [re.sub("``", "", s) for s in strings]
        words = nltk.word_tokenize(''.join(strings))
        punctuations = list(string.punctuation)
        punctuations.append("''")
        words = [word for word in words if not word in punctuations]
        words = [word.lower() for word in words]
        freqs = nltk.FreqDist(words)
        return freqs
        
    
    def predict(self):
        freqs = self.get_freq()
        total_freq = sum([freqs[key] for key in freqs])

        age = self.lexica.age["_intercept"]
        for key, val in freqs.items():
            weight = self.lexica.age.get(key)
            if not weight:
                continue
            age += weight * val / total_freq

        gender = self.lexica.gender["_intercept"]
        for key, val in freqs.items():
            weight = self.lexica.gender.get(key)
            if not weight:
                continue
            gender += weight * val / total_freq

        return(age, gender)
    
    def save_twitters(self, output_dir):
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        path = os.path.join(output_dir, f"{self.user_name}.csv")
        with open(path,"w") as f: 
            writer = csv.writer(f)
            writer.writerow(["id","created_at","text"])
            if self.tweets:
                writer.writerows(self.tweets)