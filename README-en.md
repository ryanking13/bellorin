# Bellorin

Keyword based Social Media crawler

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

### Prerequisite

Set API keys in `config.py`.

You can get API KEYs at links below.

- [NAVER](https://developers.naver.com/products/search/)
- [KAKAO](https://developers.kakao.com/docs/restapi/search)

> Writing directly to `config.py` is not recommended. Use environment variables or copy `config.py` to `_config.py` and modify `_config.py`.

### Simple Usage

```sh
python run.py thornapple bandthornapple
# python run.py <query>
# python run.py <query1> <query2> ...
```

Every collected data is saved at `save/` directory. 

### Advanced Usage

#### Specifying target platforms

```sh
# Collects data from Naver Blog and Naver Cafe
python run.py thornapple -t naver-blog naver-cafe
```

By using `-t` option, you can specify target platforms to scrap data.

#### Setting date range

```sh
# From today, to 30 days before
python run.py thornapple -d 30
```

By using `-d` option, you can change date range.

#### Other

```sh
# Verbose mode
python run.py thornapple -v

# Save log to specified file
python run.py thornapple -o out.log
```

### Miscellaneous

- The name `Bellorin` came from the novel [Polaris Rhapsody](https://en.wikipedia.org/wiki/Lee_Yeongdo#Other_novels) by _Lee Yeongdo(이영도)_, Bellorin is a girl who knows everything in the world.