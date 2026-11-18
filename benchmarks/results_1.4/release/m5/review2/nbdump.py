"""Second review of M5 (1.4.0): print the cells of a notebook, read-only.

  python3 -I nbdump.py NOTEBOOK.ipynb

Markdown and code cells with their index, and the text of the outputs that
are stored in the notebook. Nothing is executed.
"""
import json
import sys


def main(path):
    nb = json.load(open(path, encoding="utf-8"))
    for i, c in enumerate(nb.get("cells", [])):
        src = "".join(c.get("source", []))
        print("=" * 20, i, c.get("cell_type"), "=" * 20)
        print(src)
        for o in c.get("outputs", []) or []:
            if "text" in o:
                print("--- output (stream):")
                print("".join(o["text"]))
            elif "data" in o and "text/plain" in o["data"]:
                print("--- output (data):")
                print("".join(o["data"]["text/plain"]))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("#" * 10, p)
        main(p)
