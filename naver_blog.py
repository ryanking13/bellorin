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
        # self._log(f"trying to collect full post data from {username}/{postId}")
        url = "https://blog.naver.com/PostView.nhn"
        params = {
            "blogId": username,
            "logNo": postId,
        }

        r = self._session.get(url=url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")

        title = ""
        nickname = ""
        content = ""

        # 1) title

        # 네이버 블로그에서 제목에 사용되는 클래스 목록
        #! WARNING: 실험적으로 찾아낸 값으로, 상황에 따라 업데이트 필요
        title_class = (
            "se-title-text",  # 네이버 포스트 스타일 블로그: <div class="se-module se-module-text se-title-text">
            "se_title",  # 네이버 포스트 스타일 블로그: <div class="se_editView se_title">
            "itemSubjectBoldfont",  # 예전 버전 블로그: <span class="pcol1 itemSubjectBoldfont">
        )

        found = False
        for tag in itertools.chain(soup.find_all("div"), soup.find_all("span")):
            tag_class = tag.get("class", [])
            for tcls in title_class:
                if tcls in tag_class:
                    title = tag.text.strip()
                    found = True
                    break
            if found:
                break
        else:  # not found
            self._log(f"NOT FOUND: title ({username}/{postId})", False)

        # 2) nickname

        # 네이버 블로그에서 유저 닉네임에 사용되는 클래스 목록
        #! WARNING: 실험적으로 찾아낸 값으로, 상황에 따라 업데이트 필요
        nickname_class = ("nick",)  # <strong class="itemfont col" id="nickNameArea">
        found = False
        for tag in soup.find_all("strong"):
            tag_class = tag.get("class", [])
            for ncls in nickname_class:
                if ncls in tag_class:
                    nickname = tag.text.strip()
                    found = True
                    break
            if found:
                break
        else:  # not found
            self._log(f"NOT FOUND: nickname ({username}/{postId})", False)

        # 3) content

        # 네이버 블로그에서 글 내용에 사용되는 클래스 목록
        #! WARNING: 실험적으로 찾아낸 값으로, 상황에 따라 업데이트 필요
        content_class = (
            "__se_component_area",  # 네이버 포스트 스타일 블로그: <div class="se_component_wrap sect_dsc __se_component_area">
            "se-main-container",  # 네이버 포스트 스타일 블로그: <div class="se-main-container">
            "post-view",  # 예전 버전 블로그: <div id="post-view{postId}" class="post-view pcol2 _param(1) _postViewArea{postId}">
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
            self._log(f"NOT FOUND: content ({username}/{postId})", False)

        return {
            "title": title,
            "nickname": nickname,
            "content": content,
        }

    def crawl(self, query, start_date, end_date, full=True):
        url = "https://openapi.naver.com/v1/search/blog.json"
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
                        post_data.update(post_full)
                        time.sleep(config.REQUEST_INTERVAL)  # prevent massive request
                    except Exception as e:
                        self._log(f"Parsing blog failed {username} / {postId}", False)
                        self._log(e)
                        pass
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
