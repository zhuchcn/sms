# Twitter Lexica

This script predicts the age and gender using their recent tweets. The prediction model used is from the [lexica](https://github.com/wwbp/lexica) project developed by the World Well-Being Project.

## Twitter API

The valid Twitter API keys are required in order to retrieve user's tweets from twitter. The API keys must be set in the shell environment from you terminal. Run the following code on terminal and replace the placeholders to your own key values.

```bash
export CONSUMER_KEY="XXX"
export CONSUMER_SECRETE="XXX"
export ACCESS_KEY="XXX"
export ACCESS_SECRETE="XXX"
```

## Usage

To predict a single user:

```
twitter-lexica -s @realDonaldTrump
```

To predict a list of user, use a txt file with each user name in a row.
```
twitter-lexica -i users.txt -o predict.txt
```

To save all tweets used, use a directory
```
twitter-lexica -i users.txt -o predict.txt -d user_twitters
```

To save the output log
```
twitter-lexica -i test.txt -o predict.txt -d user_twitters > log.txt
```

To get help
```
twitter-lexica --help
```