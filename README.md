# Bellorin

Social Media Crawler

## Installation

> pip install -r requirements.txt

## Usage

```sh
usage: run.py [-h] [-v] [-t TARGETS [TARGETS ...]] [-d MAX_DAYS] [-o OUTPUT]
              query [query ...]

positional arguments:
  query                 Query to crawl

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Print all debug logs
  -t TARGETS [TARGETS ...], --targets TARGETS [TARGETS ...]
                        Targets services to crawl (default: instagram naver-
                        blog)
  -d MAX_DAYS, --max-days MAX_DAYS
                        Days to crawl (start from today, going backwards)
  -o OUTPUT, --output OUTPUT
                        Set output log file. if not specified, log will be
                        printed only to stdout
```

__Sample Usage__

```sh
python run.py bellorin
# python run.py <query>
# python run.py <query> <query2> ...
```

```sh
python run.py bellorin -t naver-blog -d 10 -o out.log
```