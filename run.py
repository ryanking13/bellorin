import argparse
from datetime import datetime, timedelta
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from instagram import Instagram
from naver_blog import NaverBlog
import config

# lazy class generation, prevent side-effects
def class_gen(c, *args, **kwargs):
    return lambda: c(*args, **kwargs)


target2crawler = {
    "instagram": class_gen(
        Instagram, email=config.INSTAGRAM_EMAIL, pw=config.INSTAGRAM_PASSWORD
    ),
    "naver-blog": class_gen(
        NaverBlog, id=config.NAVER_CLIENT_ID, secret=config.NAVER_CLIENT_SECRET
    ),
    # "tistory",
}

targets = target2crawler.keys()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Query to crawl")
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

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Set output log file. if not specified, log will be printed only to stdout",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    logger = logging.getLogger(config.LOGGER_NAME)

    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logger.debug("VERBOSE MODE ON")

    if args.output is not None:
        logger.debug(f"Saving log to: {args.output}")
        logger.addHandler(logging.FileHandler(args.output, encoding="utf-8", mode="w"))

    today = datetime.utcnow()
    start_date = (today - timedelta(days=args.max_days - 1)).date()
    end_date = today.date()

    logger.debug(f"[*] Query: {args.query}")
    logger.debug(f"[*] Date range: {start_date}~{end_date}")
    logger.debug(f"[*] Crawling targets: {', '.join(args.targets)}")

    logger.debug("[*] Running crawlers...")

    pool = ThreadPoolExecutor()
    futures = []
    for q in args.query:
        crawling_targets = [target2crawler[target.lower()]() for target in args.targets]
        futures.extend(
            [pool.submit(c.run, q, start_date, end_date) for c in crawling_targets]
        )

    for completed in as_completed(futures):
        print(f"[+] Done - {completed.result()}")


if __name__ == "__main__":
    main()
