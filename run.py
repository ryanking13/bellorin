import argparse
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from instagram import Instagram
import config

# lazy class generation, prevent side-effects
def class_gen(c, *args):
    return lambda: c(*args)


target2crawler = {
    "instagram": class_gen(
        Instagram, config.INSTAGRAM_EMAIL, config.INSTAGRAM_PASSWORD
    ),
    # "naver-blog",
    # "tistory",
    # "twitter",
}

targets = target2crawler.keys()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Query to crawl")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print all debug logs"
    )
    parser.add_argument(
        "-t",
        "--targets",
        nargs="+",
        help=f"Targets services to crawl (default: {' '.join(targets)})",
        default=targets,
    )
    parser.add_argument(
        "-d",
        "--max-days",
        default=7,
        help="Days to crawl (start from today, going backwards)",
        type=int,
    )

    return parser.parse_args()


def main():
    args = parse_args()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    crawling_targets = [target2crawler[target.lower()]() for target in args.targets]

    today = datetime.utcnow()
    start_date = (today - timedelta(days=args.max_days - 1)).date()
    end_date = today.date()

    pool = ThreadPoolExecutor()
    futures = [
        pool.submit(c.run, args.query, start_date, end_date) for c in crawling_targets
    ]

    for completed in as_completed(futures):
        print(f"[+] Done - {completed.result()}")


if __name__ == "__main__":
    main()
