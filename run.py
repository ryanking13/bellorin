import argparse
from datetime import datetime, timedelta
import logging
import sys
import concurrent.futures
from instagram import Instagram
from naver_blog import NaverBlog
from naver_cafe import NaverCafe
from tistory import Tistory
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
    "naver-cafe": class_gen(
        NaverCafe, id=config.NAVER_CLIENT_ID, secret=config.NAVER_CLIENT_SECRET
    ),
    "tistory": class_gen(Tistory, key=config.KAKAO_REST_API_KEY),
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

    parser.add_argument(
        "--no-analyse",
        action="store_const",
        default=True,
        const=False,
        dest="analyse",
        help="Do not analyse scrapped data after crawling",
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

    pool = concurrent.futures.ThreadPoolExecutor()
    futures = []
    for q in args.query:
        crawling_targets = [target2crawler[target.lower()]() for target in args.targets]
        futures.extend(
            [
                pool.submit(
                    lambda query, start_date, end_date, analyse: c.run(
                        query=query,
                        start_date=start_date,
                        end_date=end_date,
                        analyse=analyse,
                    ),
                    q,
                    start_date,
                    end_date,
                    args.analyse,
                )
                for c in crawling_targets
            ]
        )

    try:
        for completed in concurrent.futures.as_completed(futures):
            print(f"[+] Done - {completed.result()}")
    except KeyboardInterrupt:
        # https://gist.github.com/clchiou/f2608cbe54403edb0b13
        pool._threads.clear()
        concurrent.futures.thread._threads_queues.clear()
        raise

    pool.shutdown()


if __name__ == "__main__":
    main()
