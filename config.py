import os


def die(msg):
    print(f"{__file__}: {msg}")
    exit(1)


try:
    # for testing:
    # if you are two lazy to set env variables,
    # copy config.py to _config.py and set variables.
    if __file__.endswith("_config.py"):
        raise Exception()

    from _config import *
except:

    # Crawler Configurations
    INSTAGRAM_EMAIL = "" or os.environ.get("INSTAGRAM_EMAIL")
    INSTAGRAM_PASSWORD = "" or os.environ.get("INSTAGRAM_PASSWORD")

    NAVER_CLIENT_ID = "" or os.environ.get("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = "" or os.environ.get("NAVER_CLIENT_SECRET")

    KAKAO_REST_API_KEY = "" or os.environ.get("KAKAO_REST_API_KEY")

    # FACEBOOK_EMAIL = "" or os.environ.get("FACEBOOK_EMAIL") or die("FACEBOOK_EMAIL not set")
    # FACEBOOK_PASSWORD = (
    #     "" or os.environ.get("FACEBOOK_PASSWORD") or die("FACEBOOK_PASSWORD not set")
    # )

    # for global logging, after this codes being packaged, no more needed
    LOGGER_NAME = "bellorin"

    # seconds to sleep between each requests (per target)
    REQUEST_INTERVAL = 0.5

