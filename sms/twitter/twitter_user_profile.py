import tweepy
import pandas as pd
import os
import re
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secrete = os.environ.get("CONSUMER_SECRETE")
access_key = os.environ.get("ACCESS_KEY")
access_secrete = os.environ.get("ACCESS_SECRETE")

auth = tweepy.OAuthHandler(consumer_key, consumer_secrete)
auth.set_access_token(access_key, access_secrete)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def processUserSample(inpath, outpath):
    userSample = pd.read_excel(inpath)
    userSample = userSample[userSample["User"].notnull()]
    screen_names = [re.sub("^@", "", name) for name in userSample["User"]]
    usersData = None
    i = 0
    totalUsers = userSample.shape[0]
    while i < totalUsers :
        _next = i + 100
        if _next > totalUsers:
            _next = totalUsers
        sn = screen_names[i:_next]
        if usersData is None:
            usersData = api.lookup_users(screen_names=sn)
        else:
            usersData.extend(api.lookup_users(screen_names=sn))
        i = _next
    
    screen_names = [sn.lower() for sn in screen_names]
    usersData = {user.screen_name.lower(): user for user in usersData}
    usersDataDf = {
        "id_str": [],
        "name": [],
        "url": [],
        "description": [],
        "location": [],
        "created_at": [],
        "favourites_count": [],
        "followers_count": [],
        "friends_count": [],
        "listed_count": [],
        "profile_background_image_url": [],
        "profile_background_image_url_https": [],
        "profile_banner_url": [],
        "profile_image_url": [],
        "profile_image_url_https": [],
        "statuses_count": [],
        "verified": []
    }
    for user in screen_names:
        for key in usersDataDf.keys():
            if user in usersData:
                if key in dir(usersData[user]):
                    usersDataDf[key].append(usersData[user].__getattribute__(key))
                    if key == "created_at":
                        usersDataDf[key][-1] = usersDataDf[key][-1].strftime("%Y-%M-%d %H:%M:%S")
                else:
                    usersDataDf[key].append(None)
            else:
                usersDataDf[key].append(None)

    userSample["url"] = [url.replace("twitter.com/@", "twitter.com/") for url in userSample["url"]]
    userSample = userSample.rename(columns = {"url": "url_id"})
    usersDataDf = pd.DataFrame(usersDataDf)
    userSample = pd.concat([userSample[["User", "url_id"]], usersDataDf], axis=1)
    userSample.to_excel(outpath)

# def lookupUsers(users):
#     try:
#         usersData = api.lookup_users(screen_names=users)
#     except tweepy.TweepError as e:
#         if e.api_code == 63:
#             return "User has been suspended."
#         elif e.api_code == 50:
#             return "User not found."
#         else:
#             raise tweepy.TweepError(e)
#     return usersData

def main():
    #print("usersample1")
    #processUserSample("usersample1(urls).xlsx", "usersample1(urls)_bio.xlsx")
    print("usersample2")
    processUserSample("usersample2(urls).xlsx", "usersample2(urls)_bio.xlsx")
    print("usersample4")
    processUserSample("usersample4(urls).xlsx", "usersample4(urls)_bio.xlsx")


if __name__ == "__main__":
    main()