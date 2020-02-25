# Get post images from instagram

Download instagram post images. The images being downloaded are pretty small.

## Usage

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