import sys
from datetime import datetime, timedelta
import json

import instaloader


def main():
    today = datetime.utcnow()
    start_date = (today - timedelta(days=2)).date()
    end_date = today.date()

    L = instaloader.Instaloader()

    posts = []
    query = sys.argv[1]
    for post in L.get_hashtag_posts(query):

        if post.date_utc.date() < start_date or post.date_utc.date() > end_date:
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

    print(posts)
    dump = json.dumps(posts, indent=2, ensure_ascii=False)

    print(dump)

    with open(
        f"insta_{query}_{start_date}~{end_date}.json", "w", encoding="utf-8"
    ) as f:
        f.write(dump)


if __name__ == "__main__":
    main()
