import json
import sys

sys.path.append("..")
from instagram import Instagram
import pprint


def main():

    if len(sys.argv) < 2:
        fname = "Instagram_THORNAPPLE_2020-02-05~2020-02-05.json"
    else:
        fname = sys.argv[1]
        
    with open(fname, "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    i = Instagram()
    analysed = i.analyse(data)

    pprint.pprint(analysed)


if __name__ == "__main__":

    main()
