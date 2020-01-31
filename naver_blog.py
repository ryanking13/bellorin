from datetime import datetime
import re
import json
import logging
import pathlib
import requests
from bs4 import BeautifulSoup
from crawler import Crawler
import config


class NaverBlog(Crawler):
    def __init__(self, *args, **kwargs):
        self.client_id = kwargs["id"]
        self.client_secret = kwargs["secret"]
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
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            }
        )

    def _parse_post(self, username, postId):
        self._log(f"trying to collect full post data from {username}/{postId}")
        url = "https://blog.naver.com/PostView.nhn"
        params = {
            "blogId": username,
            "logNo": postId,
        }

        r = self._session.get(url=url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        # TODO: parsing blog content
        return {}

    def crawl(self, query, start_date, end_date, full=True):
        url = "https://openapi.naver.com/v1/search/blog.json"
        params = {
            "query": query,
            "display": 100,
            "start": 1,
            "sort": "date",
        }

        posts = []
        stop = False
        cur_date = None
        while True:
            r = self._session.get(url=url, params=params)
            if not r.ok:
                self._log(f"FAILED ({r.status_code}/)", False)
                return posts

            resp = r.json()
            for item in resp["items"]:
                # if not naver blog, skip
                if "naver" not in item["bloggerlink"]:
                    continue

                postdate = datetime.strptime(item["postdate"], "%Y%m%d")
                if postdate.date() < start_date or postdate.date() > end_date:
                    self._log("Post out of range, stop crawling...")
                    stop = True
                    break

                # Date logging (for progress checking)
                if postdate != cur_date:
                    cur_date = postdate.date()
                    self._log(f"crawling on date={cur_date}")

                # parse username and postId,
                # `bloggerlink` will be like: `https://blog.naver.com/<username>
                # `link` will be like: `https://blog.naver.com/<username>?Redirect=Log&logNo=<postId>`
                try:
                    username = item["bloggerlink"].split("/")[-1]
                    postId = re.findall(r"logNo=(\d+)", item["link"])[0]
                except:
                    self._log(
                        f"username / post ID Parsing FAILED {item['bloggerlink']} / {item['link']}",
                        False,
                    )
                    stop = True
                    break

                post_data = {
                    "id": postId,
                    "username": username,
                    "blogname": item["bloggername"],
                    "blogUrl": item["bloggerlink"],
                    "postUrl": item["link"],
                    "summary": item["description"],
                    "created": postdate.isoformat(),
                }

                # naver search api does not reveal full blog data,
                # therefore, manual crawling needed to get full data.
                # however, this might be considered as an malicious behavior.
                if full:
                    try:
                        post_full = self._parse_post(username, postId)
                    except:
                        self._log(f"Parsing blog failed {username} / {postId}", False)
                        pass
                posts.append(post_data)

            if stop:
                break

            # no more items
            if resp["total"] <= resp["start"] + resp["display"]:
                self._log("No more item, stop crawling...")
                break

            params["start"] += 1

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

    def analyse(self):
        if not self._done:
            return []
        return self._analyser.run(self._data)

    def _log(self, msg, debug=True):
        if debug:
            self._logger.debug(f"[*] {self.__class__.__name__}: {msg}")
        else:
            self._logger.info(f"[*] {self.__class__.__name__}: {msg}")
