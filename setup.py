from setuptools import setup, find_packages


setup(
    name = 'sms',
    version = '0.1.0',
    author = 'Chenghao Zhu',
    author_email = 'zhuchcn@gmail.com',
    install_requires = [
        "nltk",
        "numpy",
        "pandas",
        "python-dateutil",
        "tweepy",
        "pyppeteer",
        "asyncio",
        "pathos"
    ],
    packages = find_packages(exclude=['tests']),
    package_data = {
        "sms": ["twitter_lexica/lexica/*.csv"]
    },
    entry_points = {
        'console_scripts': [
            'instagram-image=sms.instagram.get_instagram_image:main',
            'instagram-postComments=sms.instagram.post_comments:mainWrapper',
            'twitter-lexica=sms.twitter_lexica.predict:main',
            'sms-fb=sms.fb.__main__:main'
        ]
    }
)