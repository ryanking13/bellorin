import sys
from datetime import datetime, timedelta
import json
import logging
import pathlib
import instaloader
from crawler import Crawler
import config


class Instagram(Crawler):
    def __init__(self, *args, **kwargs):
        self.email = kwargs["email"]  # TODO: not used
        self.pw = kwargs["pw"]  # TODO: not used
        self.L = instaloader.Instaloader()
        self._query = ""
        self._done = False
        self._data = None
        self._logger = logging.getLogger(config.LOGGER_NAME)

    def crawl(self, query, start_date, end_date):
        posts = []
        for post in self.L.get_hashtag_posts(query):

            if post.date_utc.date() < start_date or post.date_utc.date() > end_date:
                self._log("Post out of range, stop crawling...")
                break

            post_data = {
                "id": post.shortcode,
                "username": post.profile,
                "userId": post.owner_id,
                "created": post.date_utc.isoformat(),
                "url": post.url,
                "text": post.caption,
                "hashtags": post.caption_hashtags,
                "comments": [
                    {
                        "id": comment.id,
                        "userId": comment.owner.userid,
                        "username": comment.owner.username,
                        "text": comment.text,
                        "created": comment.created_at_utc.isoformat(),
                        "answers": [
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

        # print(posts)
        self._done = True
        self._data = posts
        return posts

    def run(self, query, start_date, end_date, auto_save=True, save_dir="save"):
        posts = self.crawl(query, start_date, end_date)
        dump = json.dumps(posts, indent=2, ensure_ascii=False)

        if auto_save:
            directory = pathlib.Path(save_dir)
            directory.mkdir(parents=True, exist_ok=True)
            f = directory / f"instagram_{query}_{start_date}~{end_date}.json"

            self._log(f"Saving results to {str(f)}")
            with open(str(f), "w", encoding="utf-8") as f:
                f.write(dump)

        # for concurrent.futures to recognize class
        return f"{self.__class__.__name__}: {query} {start_date}~{end_date}"

    @property
    def data(self):
        if not self._done:
            return []
        return self._data

    def _log(self, msg, debug=True):
        if debug:
            self._logger.debug(f"[*] {self.__class__.__name__}: {msg}")
        else:
            self._logger.info(f"[*] {self.__class__.__name__}: {msg}")


if __name__ == "__main__":
    today = datetime.utcnow()
    start_date = (today - timedelta(days=1)).date()
    end_date = today.date()
    Instagram().run(query="ssafy", start_date=start_date, end_date=end_date)
