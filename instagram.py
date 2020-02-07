import sys
from datetime import datetime, timedelta
import json
import logging
import pathlib
import itertools
import collections
import instaloader
from crawler import Crawler
import config


class Instagram(Crawler):
    def __init__(self, *args, **kwargs):
        self.email = kwargs.get("email", "")  # TODO: not used
        self.pw = kwargs.get("pw", "")  # TODO: not used
        self.L = instaloader.Instaloader()
        self._query = ""
        self._done = False
        self._data = None
        self._logger = logging.getLogger(
            config.LOGGER_NAME
        )  # when packaged, change this to logger.getLogger(__name__)
        self._analyser = InstagramAnalyser()

    def crawl(self, query, start_date, end_date):
        posts = []
        self._query = query
        cur_date = None

        try:
            for post in self.L.get_hashtag_posts(query):

                if post.date_utc.date() < start_date or post.date_utc.date() > end_date:
                    self._log("Post out of range, stop crawling...")
                    break

                # Date logging (for progress checking)
                if post.date_utc.date() != cur_date:
                    cur_date = post.date_utc.date()
                    self._log(f"crawling on date={cur_date}")

                post_data = {
                    "id": post.shortcode,
                    "username": post.profile,
                    "userId": post.owner_id,
                    "profileUrl": f"https://instagram.com/{post.profile}",
                    "postUrl": f"https://instagram.com/p/{post.shortcode}",
                    "created": post.date_utc.isoformat(),
                    "imageUrl": post.url,
                    "text": post.caption,
                    "hashtags": post.caption_hashtags,
                    "comments": [
                        {
                            "id": comment.id,
                            "userId": comment.owner.userid,
                            "username": comment.owner.username,
                            "text": comment.text,
                            "created": comment.created_at_utc.isoformat(),
                            "replies": [
                                {
                                    "id": answer.id,
                                    "userId": answer.owner.userid,
                                    "username": answer.owner.username,
                                    "text": answer.text,
                                    "created": answer.created_at_utc.isoformat(),
                                }
                                for answer in comment.answers
                            ],
                        }
                        for comment in post.get_comments()
                    ],
                }

                posts.append(post_data)

        # when there is no post at all
        except instaloader.exceptions.QueryReturnedNotFoundException:
            pass

        # print(posts)
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

        if analyse:
            self._log(f"Analysing result...")
            analysed_data = self.analyse()
            dump = json.dumps(analysed_data, indent=2, ensure_ascii=False)

            diectory = pathlib.Path(save_dir)
            directory.mkdir(parents=True, exist_ok=True)
            f = (
                diectory
                / f"{self.__class__.__name__}_{query}_{start_date}~{end_date}_analysed.json"
            )
            self._log(f"Saving analysed results to {str(f)}", False)
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


class InstagramAnalyser:
    def __init__(self):
        pass

    def _hashtag_usage(self, data):
        hashtags = itertools.chain.from_iterable([d["hashtags"] for d in data])
        hashtags_cnt = collections.Counter(hashtags)
        return collections.OrderedDict(hashtags_cnt.most_common())

    def _users(self, data):
        usernames = [d["username"] for d in data]
        usernames_cnt = collections.Counter(usernames)
        return collections.OrderedDict(usernames_cnt.most_common())

    def run(self, data):
        return {
            "hashtags_count": self._hashtag_usage(data),
            "users_count": self._users(data),
        }


if __name__ == "__main__":
    today = datetime.utcnow()
    start_date = (today - timedelta(days=1)).date()
    end_date = today.date()
    Instagram().run(query="ssafy", start_date=start_date, end_date=end_date)
