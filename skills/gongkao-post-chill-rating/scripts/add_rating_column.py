#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append a rating column to Markdown tables that contain a code column.

Usage:
    python add_rating_column.py POSITIONS.md ratings.json \
        --column 清闲度 --code-header 代码 --default —

ratings.json maps the code cell value (backticks stripped) to a rating:
    {"050000/010/03": "低", "050000/067/01": "中"}

Notes:
- Tables already containing --column are skipped, so the script is safe to rerun.
- Data rows are matched by the first backticked token in the code cell; if the
  cell has no backticks, the whole cell text is used.
"""
import argparse
import json
import re


def split_row(line: str):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def rebuild(cells):
    return "| " + " | ".join(cells) + " |"


def is_separator(line: str):
    return bool(re.match(r"^\|[\s:\-|]+\|?$", line.strip()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("ratings")
    ap.add_argument("--column", default="清闲度")
    ap.add_argument("--code-header", default="代码")
    ap.add_argument("--default", default="—")
    args = ap.parse_args()

    with open(args.ratings, encoding="utf-8-sig") as f:
        ratings = json.load(f)

    with open(args.markdown, encoding="utf-8-sig") as f:
        lines = f.read().split("\n")

    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        cells = split_row(line) if line.strip().startswith("|") else None

        has_code = cells and any(args.code_header in c for c in cells)
        already = cells and any(c == args.column for c in cells)

        if has_code and not already:
            code_idx = next(j for j, c in enumerate(cells) if args.code_header in c)
            ncols = len(cells) + 1
            out.append(rebuild(cells + [args.column]))
            i += 1

            if i < len(lines) and is_separator(lines[i]):
                sep = split_row(lines[i]) + [":---:"]
                while len(sep) < ncols:
                    sep.append("---")
                out.append(rebuild(sep[:ncols]))
                i += 1

            while i < len(lines) and lines[i].strip().startswith("|"):
                row = split_row(lines[i])
                if len(row) >= ncols - 1:
                    raw = row[code_idx] if code_idx < len(row) else ""
                    m = re.search(r"`([^`]+)`", raw)
                    code = (m.group(1) if m else raw).strip()
                    rating = ratings.get(code, args.default)
                    row = (row + [""] * (ncols - 1))[: ncols - 1] + [rating]
                    out.append(rebuild(row))
                else:
                    out.append(lines[i])
                i += 1
            continue

        out.append(line)
        i += 1

    with open(args.markdown, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("done:", args.markdown)


if __name__ == "__main__":
    main()
