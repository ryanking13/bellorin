import json
import sys

sys.path.append("..")
from instagram import Instagram
import pprint


def main():

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <target_instagram_data>")
        exit(1)

    fname = sys.argv[1]
    with open(fname, "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    i = Instagram()
    analysed = i.analyse(data)

    pprint.pprint(analysed)


if __name__ == "__main__":

    main()
