# Bellorin

키워드 기반 소셜 미디어(SNS) 크롤러

[README English version](./README-en.md)

## Installation

> pip install -r requirements.txt

## Available Social Media

- 인스타그램
- 네이버 블로그
  - [Naver API 필요](https://developers.naver.com/products/search/)
- 네이버 카페
  - [Naver API 필요](https://developers.naver.com/products/search/)
- 티스토리
  - [Kakao REST API 필요](https://developers.kakao.com/docs/restapi/search)


## Usage

```sh
usage: run.py [-h] [-v] [-t TARGETS [TARGETS ...]] [-d MAX_DAYS] [-o OUTPUT]
              [--no-analyse] [--all-columns]
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
  --all-columns         Add additional columns to scrapped data
```

### Prerequisite

`config.py`에 필요한 API KEY를 지정합니다.

각 API KEY를 신청할 수 있는 링크는 아래와 같습니다.

- [NAVER](https://developers.naver.com/products/search/)
- [KAKAO](https://developers.kakao.com/docs/restapi/search)

> `config.py`에 직접 키를 하드코딩하는 것보다는, 환경변수를 이용하거나, `config.py`를 `_config.py`로 바꾸어 사용하는 방법을 권장합니다.

### Simple Usage

```sh
python run.py thornapple 쏜애플
# python run.py <query>
# python run.py <query1> <query2> ...
```

찾고자 하는 키워드를 주어 실행합니다.

수집한 데이터를 `save/` 디렉토리에 저장됩니다.

### Advanced Usage

#### 플랫폼 지정

```sh
# 네이버 블로그와 카페에서 데이터 수집
python run.py thornapple -t naver-blog naver-cafe
```

`-t` 옵션을 사용하여 특정한 플랫폼에 대해서만 크롤링을 수행합니다.

#### 날짜 범위 지정

```sh
# 오늘부터 30일 전까지의 데이터 수집
python run.py thornapple -d 30
```

`-d` 옵션을 사용하여 수집할 데이터의 날짜 범위를 지정합니다. 

#### 기타

```sh
# 데이터 수집 과정에서 발생하는 로그를 모두 출력합니다.
python run.py thornapple -v

# 로그를 지정한 파일로 저장합니다.
python run.py thornapple -o out.log
```

### Miscellaneous

- __Bellorin__ 은 _이영도_ 의 소설 [폴라리스 랩소디](https://en.wikipedia.org/wiki/Lee_Yeongdo#Other_novels)의 등장인물입니다.