# Bellorin

Social Media Crawler

## Installation

> pip install -r requirements.txt

## Available Social Media

- Instagram
- Naver Blog
  - [Naver API required](https://developers.naver.com/products/search/)
- Naver Cafe
  - [Naver API required](https://developers.naver.com/products/search/)
- Tistory
  - [Kakao REST API required](https://developers.kakao.com/features/kakao)


## Usage

```sh
usage: run.py [-h] [-v] [-t TARGETS [TARGETS ...]] [-d MAX_DAYS] [-o OUTPUT]
              [--no-analyse]
              query [query ...]

positional arguments:
  query                 Query to crawl

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Print all debug logs
  -t TARGETS [TARGETS ...], --targets TARGETS [TARGETS ...]
                        Targets services to crawl (default: instagram naver-
                        blog naver-cafe tistory)
  -d MAX_DAYS, --max-days MAX_DAYS
                        Days to crawl (start from today, going backwards)
  -o OUTPUT, --output OUTPUT
                        Set output log file. if not specified, log will be
                        printed only to stdout
  --no-analyse          Do not analyse scrapped data after crawling
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

### Miscellaneous

- The name `Bellorin` came from the novel [Polaris Rhapsody](https://en.wikipedia.org/wiki/Lee_Yeongdo#Other_novels) by _Lee Yeongdo(이영도)_, Bellorin is a girl who knows everything in the world.