import os


def die(msg):
    print(f"{__file__}: {msg}")
    exit(1)


INSTAGRAM_EMAIL = "" or os.environ.get("INSTAGRAM_EMAIL")
INSTAGRAM_PASSWORD = "" or os.environ.get("INSTAGRAM_PASSWORD")

# FACEBOOK_EMAIL = "" or os.environ.get("FACEBOOK_EMAIL") or die("FACEBOOK_EMAIL not set")
# FACEBOOK_PASSWORD = (
#     "" or os.environ.get("FACEBOOK_PASSWORD") or die("FACEBOOK_PASSWORD not set")
# )

# for global logging, after this codes being packaged, no more needed
LOGGER_NAME = "bellorin"
