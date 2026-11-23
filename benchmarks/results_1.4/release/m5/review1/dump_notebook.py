"""M5 review 1 (read-only): print the cells of a notebook as plain text,
markdown, code and the text of its stored outputs, with cell numbers, so
that the figures it states can be read beside the records of M3.

  python3 -I dump_notebook.py NOTEBOOK.ipynb
"""
import json
import sys


def text(x):
    return "".join(x) if isinstance(x, list) else (x or "")


def main(path):
    nb = json.load(open(path, encoding="utf-8"))
    for i, c in enumerate(nb.get("cells", [])):
        kind = c.get("cell_type")
        print("=" * 20, "cell %d [%s]" % (i, kind))
        print(text(c.get("source")))
        for o in c.get("outputs", []) or []:
            if "text" in o:
                print("--- output (stream)")
                print(text(o["text"]))
            elif "data" in o and "text/plain" in o["data"]:
                print("--- output (data)")
                print(text(o["data"]["text/plain"]))


if __name__ == "__main__":
    main(sys.argv[1])
