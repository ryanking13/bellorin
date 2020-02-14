from datetime import datetime
import itertools
import re
import json
import time
import logging
import pathlib
import requests
from bs4 import BeautifulSoup
from textrankr import TextRank
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
        self._analyser = NaverBlogAnalyser()
        self._session = requests.session()

        self._session.headers.update(
            {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
                "Referer": "https://blog.naver.com/PostView.nhn",
            }
        )

    def _parse_post(self, username, post_id):
        # self._log(f"trying to collect full post data from {username}/{post_id}")
        url = "https://blog.naver.com/PostView.nhn"
        params = {
            "blogId": username,
            "logNo": post_id,
        }

        r = self._session.get(url=url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")

        title = ""
        nickname = ""
        text = ""
        comments = []
        blog_id = re.findall(r"var blogNo = \'(\d+)\';", r.text)[0]

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
            self._log(f"NOT FOUND: title ({username}/{post_id})", False)

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
            self._log(f"NOT FOUND: nickname ({username}/{post_id})", False)

        # 3) text

        # 네이버 블로그에서 글 내용에 사용되는 클래스 목록
        #! WARNING: 실험적으로 찾아낸 값으로, 상황에 따라 업데이트 필요
        text_class = (
            "__se_component_area",  # 네이버 포스트 스타일 블로그: <div class="se_component_wrap sect_dsc __se_component_area">
            "se-main-container",  # 네이버 포스트 스타일 블로그: <div class="se-main-container">
            "post-view",  # 예전 버전 블로그: <div id="post-view{post_id}" class="post-view pcol2 _param(1) _postViewArea{post_id}">
        )
        found = False
        for tag in soup.find_all("div"):
            tag_class = tag.get("class", [])
            for tcls in text_class:
                if tcls in tag_class:
                    text = tag.text.strip()
                    text = re.sub(r"\s+", " ", text)  # compress whitespaces
                    found = True
                    break
            if found:
                break
        else:  # not found
            self._log(f"NOT FOUND: text ({username}/{post_id})", False)

        # 4) comments
        comment_url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json"
        params = {
            "ticket": "blog",
            "lang": "ko",
            "showReply": "true",
            "groupId": blog_id,
            "objectId": f"{blog_id}_201_{post_id}",
            "pool": "cbox9",
            "listType": "OBJECT",
            "cleanbotGrade": "2",
            "replyPageSize": "10",
            "useAltSort": "true",
            "initialize": "true",
            "page": "1",
            "pageType": "default",
            "indexSize": "10",
            "pageSize": "50",
            "templateId": "default",
            "_callback": "X",
        }

        self._session.headers.update({})
        r = self._session.get(url=comment_url, params=params)

        # response: X(<json_data>);
        _resp = json.loads(r.text.strip()[2:-2])
        if not _resp["success"]:
            self._log(f"NOT FOUND: comment ({username}/{post_id})", False)
        else:
            # comments returned at timestamp desc order
            # therefore, to efficiently match comment-reply, reverse order
            _comments = reversed(_resp["result"]["commentList"])

            for c in _comments:
                cmt = {
                    "id": c["commentNo"],
                    "text": c["contents"],
                    "username": c["profileUserId"],
                    "nickname": c["userName"],
                    "created": c["regTime"],
                    "replies": [],
                }

                # 답글
                if c["replyLevel"] > 1:
                    for _cmt in comments:
                        if _cmt["id"] == c["parentCommentNo"]:
                            _cmt["replies"].append(cmt)
                            break
                    else:
                        self._log(
                            f"Parent comment not exists: ({username}/{post_id} {cmt['text']})",
                            False,
                        )
                # 댓글
                else:
                    comments.append(cmt)

        return {
            "title": title,
            "nickname": nickname,
            "text": text,
            "blogId": blog_id,
            "comments": comments,
            "comments_cnt": len(comments),
        }

    def crawl(self, query, start_date, end_date, main_columns_only, full=True):
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

                # parse username and post_id,
                # `bloggerlink` will be like: `https://blog.naver.com/<username>
                # `link` will be like: `https://blog.naver.com/<username>?Redirect=Log&logNo=<post_id>`
                try:
                    username = item["bloggerlink"].split("/")[-1]
                    post_id = re.findall(r"logNo=(\d+)", item["link"])[0]
                except:
                    self._log(
                        f"username / post ID Parsing FAILED {item['bloggerlink']} / {item['link']}",
                        False,
                    )
                    stop = True
                    break

                post_data = {
                    "id": post_id,
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
                        post_full = self._parse_post(username, post_id)
                        post_data.update(post_full)
                        time.sleep(config.REQUEST_INTERVAL)  # prevent massive request
                    except Exception as e:
                        self._log(f"Parsing blog failed {username} / {post_id}", False)
                        self._log(e)

                if main_columns_only:
                    del post_data["blogname"]
                    del post_data["blogUrl"]
                    del post_data["postUrl"]
                    del post_data["summary"]
                    if full:
                        del post_data["nickname"]
                        del post_data["blogId"]
                        del post_data["comments"]

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
        self,
        query,
        start_date,
        end_date,
        save=True,
        analyse=True,
        save_dir="save",
        main_columns_only=True,
    ):
        posts = self.crawl(query, start_date, end_date, main_columns_only)

        if analyse:
            self._log(f"Analysing result...")
            analysed_data = self.analyse(data=posts)
            for post, _data in zip(posts, analysed_data):
                post.update(_data)

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


class NaverBlogAnalyser:
    def __init__(self):
        pass

    def _key_sentences(self, datum, n=1):
        text = datum["text"]
        textrank = TextRank(text)
        return textrank.summarize(n)

    def run(self, data):
        analysed_data = []
        for d in data:
            analysed_data.append({"key_sentences": self._key_sentences(d)})

        return analysed_data
