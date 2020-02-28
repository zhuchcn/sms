# Get instagram posts, comments, and images

Download instagram post images. The images being downloaded are pretty small.

## instagram-image

The urls.txt must be a text file with only url in each row.

```bash
instagram-image -i urls.txt -o imgs/
```

Use multiple threads (fast!)

```bash
instagram-image -i urls.txt -o imgs/ -n 6
```

Prepend a numeric index to image names

```bash
instagram-image -i urls.txt -o imgs/ -p
```

Print out logging messages while running

```bash
instagram-image -i urls.txt -o imgs/ -v
```

You can of course redirect the logging messages.

```bash
instagram-image -i urls.txt -o imgs/ -v > log.txt
```

Get help

```bash
instagram-image -h
```

## instagram-postComments

Basic usage:

```bash
instagram-postComments -i urls.txt -p posts.csv -c comments.csv
```

The `urls.txt` must contain the full url in the pattern of 'https://www.instagram/p/xxxxx/'.

To delay between each post request, use the `-d/--delay`. Must be integer. The value is in seconds.

```bash
instagram-postComments -i urls.txt -p posts.csv -c comments.csv -d 3
```

To specify a user temporary directory

```bash
mkdir temp
instagram-postComments -i urls.txt -p posts.csv -c comments.csv -d 3 -u temp/
```

Run in a head mode

```bash
instagram-postComments -i urls.txt -p posts.csv -c comments.csv -d 3 -n
```

Get help

```bash
instagram-postComments -h
```

+ Mac users, if the job stops every ~220 iterations, it's very possible that the upper limit for file descriptors is too low, which is usually 256. To fix it, simply type the command below to your terminal and this will set the upper limit to 10000.

```bash
ulimit -Sn 10000
```

You can verify it by calling `ulimit -a`

```bash
ulimit -a
```

```
-t: cpu time (seconds)              unlimited
-f: file size (blocks)              unlimited
-d: data seg size (kbytes)          unlimited
-s: stack size (kbytes)             8192
-c: core file size (blocks)         0
-v: address space (kbytes)          unlimited
-l: locked-in-memory size (kbytes)  unlimited
-u: processes                       2784
-n: file descriptors                10000
```