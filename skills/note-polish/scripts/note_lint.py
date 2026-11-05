#!/usr/bin/env python3
"""Obsidian 笔记排版检查（只读，不修改任何文件）。

检查项：
  MARKED      用户标记（默认「长长长」）正下方的公式块 —— 必须拆分
  OVER        估算渲染宽度 >= threshold 的公式块 —— 应拆分
  BORDERLINE  宽度在 [borderline, threshold) 之间 —— 只报告，不改
  TABLE       表格行里的 `|` 打断了公式 / wikilink，或列数与表头不一致，或尾部空行
  BALANCE     $$ 未闭合、\\begin/\\end 不配对、\\left/\\right 跨行、\\tag 写在 aligned 等环境内部

用法：
  python3 -I note_lint.py <file-or-dir> [...] [--threshold 66] [--borderline 60] [--marker REGEX]

宽度单位约等于一个字符宽（em 级别），是估算值而非像素：
  上下标按 0.7 计，\\frac 取分子分母较宽者，\\mathbb/\\big/\\left 等不计宽度，
  `=`/`+` 等带间距的运算符略宽。阈值 66 是在用户屏幕上用实际标记校准出来的。
"""
import argparse
import pathlib
import re
import sys

DEFAULT_MARKER = r"长长长"
PREFIX_RE = re.compile(r"^\s*(?:>\s*)*")  # callout `>` 前缀 + 缩进
ZERO_WIDTH = {
    "mathbb", "mathcal", "mathbf", "boldsymbol", "mathrm", "mathsf", "mathit",
    "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr",
    "left", "right", "limits", "nolimits", "displaystyle", "textstyle",
    "hat", "tilde", "bar", "vec", "dot", "ddot", "overline", "underline", "widehat", "widetilde",
    "phantom", "hphantom", "vphantom", "nonumber", "notag",
}
WIDE_OPS = {"max": 1.7, "min": 1.7, "arg": 1.7, "log": 1.7, "exp": 1.7, "lim": 1.7,
            "sin": 1.7, "cos": 1.7, "sup": 1.7, "inf": 1.7, "det": 1.7, "tr": 1.2}
SPACING = {"quad": 1.0, "qquad": 2.0, ",": 0.25, ";": 0.3, ":": 0.25, " ": 0.25, "!": 0.0}
ENV_NO_TAG = {"aligned", "gathered", "split", "cases", "matrix", "bmatrix", "pmatrix", "array"}


def group(s, i):
    """s[i] == '{' -> (inner, index after matching '}')."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    return s[i + 1:], len(s)


def arg(s, i):
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        return group(s, i)
    if s[i] == "\\":
        m = re.match(r"\\([a-zA-Z]+|.)", s[i:])
        return m.group(0), i + len(m.group(0))
    return s[i], i + 1


def width(s):
    w, i = 0.0, 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            m = re.match(r"\\([a-zA-Z]+|.)", s[i:])
            name = m.group(1)
            i += len(m.group(0))
            if name in ("frac", "dfrac", "tfrac", "cfrac", "binom"):
                a, i = arg(s, i)
                b, i = arg(s, i)
                w += max(width(a), width(b)) + 0.4
            elif name in ("text", "textbf", "textit", "operatorname", "mbox"):
                a, i = arg(s, i)
                w += len(a) * 0.55
            elif name == "tag":
                a, i = arg(s, i)
                w += len(a) + 3
            elif name in ("underbrace", "overbrace", "underset", "overset", "stackrel"):
                if name in ("underset", "overset", "stackrel"):
                    lab, i = arg(s, i)
                    body, i = arg(s, i)
                    w += max(width(body), 0.7 * width(lab))
                    continue
                body, i = arg(s, i)
                bw = width(body)
                if i < len(s) and s[i] in "_^":
                    lab, i = arg(s, i + 1)
                    bw = max(bw, 0.7 * width(lab))
                w += bw
            elif name in ("xrightarrow", "xleftarrow"):
                below = ""
                if i < len(s) and s[i] == "[":
                    j = s.index("]", i)
                    below, i = s[i + 1:j], j + 1
                above, i = arg(s, i)
                w += max(width(above), width(below)) * 0.7 + 1.5
            elif name in ("begin", "end"):
                _, i = arg(s, i)
                if i < len(s) and s[i] == "{":  # array column spec
                    _, i = group(s, i)
            elif name in ZERO_WIDTH:
                pass
            elif name in SPACING:
                w += SPACING[name]
            elif name in ("sum", "prod", "int", "oint", "bigcup", "bigcap"):
                w += 1.4
            elif name in WIDE_OPS:
                w += WIDE_OPS[name]
            elif name == "\\":
                pass
            else:
                w += 1.0
        elif c in "_^":
            a, i = arg(s, i + 1)
            w += 0.7 * max(width(a), 1.0) if a.startswith("\\") else 0.7 * width(a)
        elif c in "{}& \t":
            i += 1
        elif c in "=<>":
            w += 1.7
            i += 1
        elif c in "+-":
            w += 1.5
            i += 1
        elif c == ",":
            w += 0.5
            i += 1
        else:
            w += 1.0
            i += 1
    return w


def line_width(content):
    return max(width(part) for part in re.split(r"\\\\", content))


def strip_prefix(line):
    return PREFIX_RE.sub("", line, count=1)


def collect(paths):
    out = []
    for p in paths:
        p = pathlib.Path(p)
        if p.is_dir():
            out += sorted(q for q in p.rglob("*.md")
                          if not any(part.startswith(".") for part in q.parts))
        elif p.suffix == ".md":
            out.append(p)
        else:
            print(f"skip: {p}", file=sys.stderr)
    return out


def math_blocks(lines):
    """yield (start_idx, end_idx, [(idx, content)]) for display math blocks; end_idx None if unclosed."""
    i = 0
    while i < len(lines):
        c = strip_prefix(lines[i]).strip()
        if c.startswith("$$"):
            if len(c) > 4 and c.endswith("$$"):  # single-line $$...$$
                yield i, i, [(i, c[2:-2])]
                i += 1
                continue
            body = [] if c == "$$" else [(i, c[2:])]
            j = i + 1
            while j < len(lines):
                cj = strip_prefix(lines[j]).strip()
                if cj.endswith("$$"):
                    if cj != "$$":
                        body.append((j, cj[:-2]))
                    break
                body.append((j, cj))
                j += 1
            yield i, (j if j < len(lines) else None), body
            i = j + 1
        else:
            i += 1


def split_cells(row):
    """split a markdown table row on unescaped `|`."""
    cells, cur, k = [], "", 0
    while k < len(row):
        if row[k] == "\\" and k + 1 < len(row):
            cur += row[k:k + 2]
            k += 2
            continue
        if row[k] == "|":
            cells.append(cur)
            cur = ""
        else:
            cur += row[k]
        k += 1
    cells.append(cur)
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def check_tables(lines):
    issues = []
    i = 0
    while i < len(lines):
        if strip_prefix(lines[i]).lstrip().startswith("|"):
            j = i
            while j < len(lines) and strip_prefix(lines[j]).lstrip().startswith("|"):
                j += 1
            rows = [(k, strip_prefix(lines[k]).strip()) for k in range(i, j)]
            header_n = len(split_cells(rows[0][1]))
            for k, row in rows:
                # 公式或 wikilink 里的 | 才是问题本体
                for m in re.finditer(r"(?<!\$)\$(?!\$)([^$]*)\$", row.replace("\\|", "")):
                    if "|" in m.group(1):
                        issues.append((k, "公式里含 `|`，会被当成列分隔符", m.group(0)[:60]))
                for m in re.finditer(r"\[\[([^\]]*)\]\]", row):
                    if re.search(r"(?<!\\)\|", m.group(1)):
                        issues.append((k, "wikilink 别名的 `|` 需写成 `\\|`", m.group(0)[:60]))
                cells = split_cells(row)
                if "-" in row and re.fullmatch(r"[\s|:\-]+", row):
                    continue  # 分隔行
                if len(cells) != header_n:
                    issues.append((k, f"列数 {len(cells)} 与表头 {header_n} 不一致", row[:60]))
                if all(c.strip() == "" for c in cells) and k == rows[-1][0]:
                    issues.append((k, "表格末尾是空行（多半是排版错乱的残留）", ""))
            i = j
        else:
            i += 1
    return issues


def check_block_balance(body):
    issues = []
    text = "\n".join(c for _, c in body)
    begins = re.findall(r"\\begin\{(\w+\*?)\}", text)
    ends = re.findall(r"\\end\{(\w+\*?)\}", text)
    if sorted(begins) != sorted(ends):
        issues.append((body[0][0] if body else 0, f"\\begin {begins} 与 \\end {ends} 不配对"))
    multi = "\\\\" in text
    for idx, c in body:
        for seg in re.split(r"\\\\", c):
            l, r = len(re.findall(r"\\left\b", seg)), len(re.findall(r"\\right\b", seg))
            if multi and l != r:
                issues.append((idx, f"\\left/\\right 跨行（本行 left={l}, right={r}），会渲染报错"))
    # \tag 是否落在 aligned 等环境内部
    depth = 0
    for tok in re.finditer(r"\\begin\{(\w+)\}|\\end\{(\w+)\}|\\tag\b", text):
        if tok.group(1) in ENV_NO_TAG:
            depth += 1
        elif tok.group(2) in ENV_NO_TAG:
            depth -= 1
        elif tok.group(0) == "\\tag" and depth > 0:
            issues.append((body[0][0], "\\tag 写在 aligned/gathered 内部，应移到 \\end{...} 之后"))
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--threshold", type=float, default=66.0)
    ap.add_argument("--borderline", type=float, default=60.0)
    ap.add_argument("--marker", default=DEFAULT_MARKER, help="用户标记的正则（匹配整行去掉前缀后的内容）")
    a = ap.parse_args()
    marker_re = re.compile(rf"^(?:{a.marker})\s*$")

    sections = {k: [] for k in ("MARKED", "OVER", "BORDERLINE", "TABLE", "BALANCE", "STRAY_MARKER")}
    marked_widths = []
    for f in collect(a.paths):
        lines = f.read_text(encoding="utf-8").split("\n")
        used_markers = set()
        for start, end, body in math_blocks(lines):
            if end is None:
                sections["BALANCE"].append(f"{f}:{start + 1}: $$ 没有闭合")
                continue
            for idx, msg in check_block_balance(body):
                sections["BALANCE"].append(f"{f}:{idx + 1}: {msg}")
            if not body:
                continue
            widest_idx, widest = max(((idx, line_width(c)) for idx, c in body), key=lambda t: t[1])
            # 标记：块前最近的非空行
            k = start - 1
            while k >= 0 and strip_prefix(lines[k]).strip() == "":
                k -= 1
            marked = k >= 0 and marker_re.match(strip_prefix(lines[k]).strip())
            if marked:
                used_markers.add(k)
                marked_widths.append(widest)
            callout = lines[start].lstrip().startswith(">")
            where = "callout" if callout else "body"
            row = (f"{widest:6.1f}  {f}:{start + 1}-{end + 1}  (最宽行 {widest_idx + 1}, {where})"
                   + (f"  [标记在第 {k + 1} 行]" if marked else ""))
            if marked:
                sections["MARKED"].append(row)
            elif widest >= a.threshold:
                sections["OVER"].append(row)
            elif widest >= a.borderline:
                sections["BORDERLINE"].append(row)
        for k, line in enumerate(lines):
            if marker_re.match(strip_prefix(line).strip()) and k not in used_markers:
                sections["STRAY_MARKER"].append(f"{f}:{k + 1}: 标记后面不是公式块，需人工看上下文")
        for k, msg, snippet in check_tables(lines):
            sections["TABLE"].append(f"{f}:{k + 1}: {msg}  {snippet}")

    titles = {
        "MARKED": "用户标记的公式块（必须拆分，并删除标记行）",
        "OVER": f"超过阈值 {a.threshold:g} 的公式块（应拆分）",
        "BORDERLINE": f"接近阈值 [{a.borderline:g}, {a.threshold:g}) 的公式块（只报告，不改）",
        "TABLE": "表格问题",
        "BALANCE": "公式结构问题（会导致渲染报错）",
        "STRAY_MARKER": "孤立标记",
    }
    for key, items in sections.items():
        print(f"## {titles[key]}: {len(items)}")
        for it in items:
            print("  " + it)
    if marked_widths:
        lo = min(marked_widths)
        print(f"\n校准：标记块最窄宽度 = {lo:.1f}；本次建议阈值 = {min(lo, a.threshold):.1f}"
              + ("（低于当前阈值，建议用 --threshold 重新跑一次）" if lo < a.threshold else ""))


if __name__ == "__main__":
    main()
