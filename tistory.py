from datetime import datetime
import json
import pathlib
import logging
import re
import time
import requests
from bs4 import BeautifulSoup
import config
from crawler import Crawler


class Tistory(Crawler):
    def __init__(self, *args, **kwargs):
        self.app_key = kwargs["key"]
        self._query = ""
        self._done = False
        self._data = None
        self._logger = logging.getLogger(
            config.LOGGER_NAME
        )  # when packaged, change this to logger.getLogger(__name__)
        self._analyser = None
        self._session = requests.session()

        self._session.headers.update(
            {
                "Authorization": f"KakaoAK {self.app_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            }
        )

    def _parse_post(self, url):
        r = self._session.get(url=url)
        soup = BeautifulSoup(r.text, "html.parser")
        content = ""

        # 1) content

        # 티스토리 블로그에서 글 내용에 사용되는 클래스 목록
        #! WARNING: 실험적으로 찾아낸 값으로, 상황에 따라 업데이트 필요
        content_class = (
            "tt_article_useless_p_margin",  # https://cow5jean.tistory.com/29
            "article_view",  # https://milkbean.tistory.com/16?category=842530
            "entry-content",  # https://simyeju.tistory.com/48
            "post-content",  # https://philipbox.tistory.com/79
            "desc",  # https://michaelchoi.tistory.com/25
            "article_cont",  # https://iton.tistory.com/4090
            "article",  # https://freepanda.tistory.com/47
            "area_view",  # https://choish313.tistory.com/122
        )
        found = False
        for tag in soup.find_all("div"):
            tag_class = tag.get("class", [])
            for ccls in content_class:
                if ccls in tag_class:
                    content = tag.text.strip()
                    content = re.sub(r"\s+", " ", content)  # compress whitespaces
                    found = True
                    break
            if found:
                break
        else:  # not found
            self._log(f"NOT FOUND: content ({url})", False)

        return {
            "content": content,
        }

    def crawl(self, query, start_date, end_date, full=True):
        url = "https://dapi.kakao.com/v2/search/blog"
        display_size = 50
        params = {
            "query": query,
            "size": display_size,
            "page": 1,
            "sort": "recency",
        }

        self._query = query
        posts = []
        stop = False
        cur_date = None

        while True:
            r = self._session.get(url=url, params=params)
            if not r.ok:
                if r.status_code == 401:
                    self._log("ERROR: KAKAO API 키를 설정하세요", False)
                    return posts
                else:  # Undefined status codes
                    self._log(f"FAILED ({r.status_code}/{r.text})", False)
                    return posts

            resp = r.json()
            for document in resp["documents"]:
                # if not tistory, skip
                if "tistory.com" not in document["url"]:
                    continue

                postdate = datetime.strptime(
                    document["datetime"], "%Y-%m-%dT%H:%M:%S.000%z"
                )
                if postdate.date() < start_date or postdate.date() > end_date:
                    self._log("Post out of range, stop crawling...")
                    stop = True
                    break

                # Date logging (for progress checking)
                if postdate != cur_date:
                    cur_date = postdate.date()
                    self._log(f"crawling on date={cur_date}")

                post_data = {
                    "title": document["title"],
                    "blogname": document["blogname"],
                    "postUrl": document["url"],
                    "blogUrl": document["url"][
                        : document["url"].rindex("/")
                    ],  # strip rightmost slash
                    "summary": document["contents"],
                    "thumbnailUrl": document["thumbnail"],
                    "created": postdate.isoformat(),
                }

                # kakao search api does not reveal full blog data,
                # therefore, manual crawling needed to get full data.
                # however, this might be considered as an malicious behavior.
                if full:
                    try:
                        post_full = self._parse_post(document["url"])
                        post_data.update(post_full)
                        time.sleep(0.1)  # prevent massive request
                    except Exception as e:
                        self._log(f"Parsing blog failed {document['url']}", False)
                        self._log(e)
                        pass

                posts.append(post_data)

            if stop:
                break

            if resp["meta"]["is_end"]:
                self._log("No more item, stop crawling...")
                break

            params["page"] += 1

        self._done = True
        self._data = posts
        return posts

    def run(
        self, query, start_date, end_date, save=True, analyse=True, save_dir="save"
    ):
        posts = self.crawl(query, start_date, end_date)
        if save:
            dump = json.dumps(posts, indent=2, ensure_ascii=False)
            directory = pathlib.Path(save_dir)
            directory.mkdir(parents=True, exist_ok=True)
            f = (
                directory
                / f"{self.__class__.__name__}_{query}_{start_date}~{end_date}.json"
            )

            self._log(f"Saving results to {str(f)}", False)
            with open(str(f), "w", encoding="utf-8") as f:
                f.write(dump)

        # TODO
        # if analyse:
        #     self._log(f"Analysing result...")
        #     analysed_data = self.analyse()
        #     dump = json.dumps(analysed_data, indent=2, ensure_ascii=False)

        #     diectory = pathlib.Path(save_dir)
        #     directory.mkdir(parents=True, exist_ok=True)
        #     f = (
        #         diectory
        #         / f"{self.__class__.__name__}_{query}_{start_date}~{end_date}_analysed.json"
        #     )
        #     self._log(f"Saving analysed results to {str(f)}", False)
        #     with open(str(f), "w", encoding="utf-8") as f:
        #         f.write(dump)

        # for concurrent.futures to recognize class
        return f"{self.__class__.__name__}: {query} {start_date}~{end_date}"

    @property
    def data(self):
        if not self._done:
            return []
        return self._data

    def analyse(self, data=None):
        if data is not None:
            return self._analyser.run(data)
        else:
            if not self._done:
                return []
            return self._analyser.run(self._data)

    def _log(self, msg, debug=True):
        if debug:
            self._logger.debug(f"[*] {self.__class__.__name__} ({self._query}): {msg}")
        else:
            self._logger.info(f"[*] {self.__class__.__name__} ({self._query}): {msg}")
