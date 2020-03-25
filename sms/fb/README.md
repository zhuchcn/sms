## Command line usage:

+ get help:

```bash
sms-fb --help
```

+ Two subcommands available, `sms-fb post` and `sms-fb page`. The former gets data of each post from a page, while the later gets the post data from a given url.

+ Save posts of a single page

```bash
sms-fb page -n saveyourlungs -o output.txt
```

+ Save posts of a single page after a specific date

```bash
sms-fb page -n saveyourlungs -d 2020-01-01 -o output.txt
```

+ You can also put the page name of the facebook pages that you would like to get posts into a file as a input.

```bash
sms-fb page -i namelist.txt -o output.txt
```

+ To get post data from a url:

```bash
sms-fb post urls.txt posts.csv
```