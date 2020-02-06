from datetime import datetime
import json
import pathlib
import logging
import requests
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

        self._session.headers.update({"Authorization": f"KakaoAK {self.app_key}"})

    def crawl(self, query, start_date, end_date):
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
                    "summary": document["contents"],
                    "thumbnailUrl": document["thumbnail"],
                    "created": postdate.isoformat(),
                }

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
