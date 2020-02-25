from setuptools import setup, find_packages


setup(
    name = 'sms',
    version = '0.1.0',
    author = 'Chenghao Zhu',
    author_email = 'zhuchcn@gmail.com',
    install_requires = [
        "nltk==3.4.5",
        "numpy==1.17.2",
        "pandas==0.25.1",
        "python-dateutil==2.8.0",
        "python-dotenv==0.10.3",
        "tweepy==3.8.0",
        "pathos"
    ],
    packages = find_packages(exclude=['tests']),
    package_data = {
        "sms": ["twitter_lexica/lexica/*.csv"]
    },
    entry_points = {
        'console_scripts': [
            'get_instagram_image = sms.instagram.get_instagram_image:main',
            'twitter_lexica = sms.twitter_lexica.predict:main'
        ]
    }
)