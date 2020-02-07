from datetime import datetime
import itertools
import re
import json
import time
import logging
import pathlib
import requests
from bs4 import BeautifulSoup
from crawler import Crawler
import config


class NaverCafe(Crawler):
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

    def _parse_post(self, url):
        # 검색을 통한 유입 시뮬레이션
        self._session.headers.update(
            {"Referer": f"https://search.naver.com/?&query={self._query}"}
        )

        # 게시글 불러오는 jsp파일 URL 추출 (cafe.naver.com/ArticleRead.nhn)
        # e.g. https://cafe.naver.com/ArticleRead.nhn?articleid=13787&sc=b29e811a1e4f9b8f1cea36c6ae3baaa8b4d26d8&query=ssafy&where=search&clubid=29884561&tc=naver_search
        # TODO: sc값 생성 원리 파악 후 fake generate
        r = self._session.get(url=url)
        article_url = re.findall(r"\$\(\"cafe_main\"\)\.src = \"(.+)\";", r.text)
        if not article_url:
            self._log(f"Failed parsing content ({url})", False)
            raise Exception()

        article_url = f"https:{article_url[0]}"
        # self._log(f"trying to collect full post data from {article_url}")

        r = self._session.get(url=article_url)
        soup = BeautifulSoup(r.text, "html.parser")

        username = ""
        created = ""
        content = ""
        comments = []
        cafe_id = re.findall(r"clubid=(\d+)", article_url)[0]
        article_id = re.findall(r"articleid=(\d+)", article_url)[0]

        # 1) username

        for tag in soup.find_all("a"):
            # 멤버 정보 URL
            href = tag.get("href", "")
            if href.startswith("/CafeMemberNetworkView.nhn"):
                _username = re.findall(r"memberid=(.+)[&]*$", href)
                if _username:
                    username = _username[0].strip()
                    break
        else:  # not found
            self._log(f"NOT FOUND: username ({article_url})", False)

        # 2) created

        # e.g. <td class="m-tcol-c date">2012.05.15. 20:59</td>
        for tag in soup.find_all("td"):
            _class = " ".join(tag.get("class", ""))
            if _class == "m-tcol-c date":
                created = datetime.strptime(
                    tag.text.strip(), "%Y.%m.%d. %H:%M"
                ).isoformat()
                break
        else:  # not found
            self._log(f"NOT FOUND: created ({article_url})", False)

        # 3) content

        # e.g. <div class="tbody m-tcol-c" id="tbody">
        for tag in soup.find_all("div"):
            _id = tag.get("id", "")
            if _id == "tbody":
                content = tag.text.strip()
                content = re.sub(r"\s+", " ", content)  # compress whitespaces
                break
        else:  # not found
            self._log(f"NOT FOUND: content ({article_url})", False)

        # 4) comments
        comment_url = "https://cafe.naver.com/CommentView.nhn"
        params = {
            "search.clubid": cafe_id,
            "search.articleid": article_id,
        }
        r = self._session.post(url=comment_url, data=params)

        _comments = r.json()["result"]["list"]
        for c in _comments:
            cmt = {
                "id": c["commentid"],
                "content": c["content"],
                "username": c["writerid"],
                "nickname": c["writernick"],
                "replies": [],
            }

            # if deleted, no date information
            if not c["deleted"]:
                cmt["created"] = datetime.strptime(
                    c["writedt"], "%Y.%m.%d. %H:%M"
                ).isoformat()

            # 답글
            if c["refComment"]:
                for _cmt in comments:
                    if _cmt["id"] == c["refcommentid"]:
                        _cmt["replies"].append(cmt)
                        break
            # 댓글
            else:
                comments.append(cmt)

        return {
            "username": username,
            "created": created,
            "content": content,
            "cafeId": cafe_id,
            "article_id": article_id,
            "comments": comments,
        }

    def crawl(self, query, start_date, end_date):
        url = "https://openapi.naver.com/v1/search/cafearticle.json"
        display_size = 100
        params = {
            "query": query,
            "display": display_size,
            "start": 1,
            "sort": "date",
        }

        self._query = query
        posts = []
        stop = False
        cur_date = None
        while True:
            r = self._session.get(url=url, params=params)
            if not r.ok:
                if r.status_code == 401:
                    self._log("ERROR: NAVER API 키를 설정하세요", False)
                    return posts
                else:  # Undefined status codes
                    self._log(f"FAILED ({r.status_code}/{r.text})", False)
                    return posts

            resp = r.json()
            for item in resp["items"]:

                # parse postId,
                # `link` will be like: `http://cafe.naver.com/<cafe_name>/<post_id>`
                try:
                    postId = int(item["link"].split("/")[-1])
                except:
                    self._log(
                        f"post ID Parsing FAILED {item['link']}", False,
                    )
                    stop = True
                    break

                post_data = {
                    "id": postId,
                    "title": item["title"],
                    "cafename": item["cafename"],
                    "cafeUrl": item["cafeurl"],
                    "postUrl": item["link"],
                    "summary": item["description"],
                }

                # naver search api does not reveal full blog data,
                # therefore, manual crawling needed to get full data.
                # however, this might be considered as an malicious behavior.
                #! Naver Cafe search api does not crawl post creation date,
                #! therefore, manual crawling is *necessary*
                try:
                    post_full = self._parse_post(item["link"])
                    post_data.update(post_full)
                    time.sleep(0.1)  # prevent massive request
                except Exception as e:
                    self._log(f"Parsing cafe failed {item['link']}", False)
                    self._log(e)

                postdate = datetime.strptime(post_data["created"], "%Y-%m-%dT%H:%M:%S")
                if postdate.date() < start_date or postdate.date() > end_date:
                    self._log("Post out of range, stop crawling...")
                    stop = True
                    break

                # Date logging (for progress checking)
                if postdate != cur_date:
                    cur_date = postdate.date()
                    self._log(f"crawling on date={cur_date}")

                posts.append(post_data)

            if stop:
                break

            # no more items
            if resp["total"] <= resp["start"] + resp["display"]:
                self._log("No more item, stop crawling...")
                break

            # search result maximum exceeded
            # Reference: https://developers.naver.com/forum/posts/10120
            if resp["start"] + resp["display"] >= 1100:
                self._log("No more item, stop crawling...")
                break

            params["start"] += display_size

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
