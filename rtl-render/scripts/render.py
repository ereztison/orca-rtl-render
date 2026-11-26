"""Render Markdown as one self-contained right-to-left Orca visual."""

import argparse
from html import escape
import os
import re
from pathlib import Path
import sys
from unicodedata import bidirectional
from uuid import uuid4


def render_image(tokens, index, options, env):
    token = tokens[index]
    label = escape(token.content or token.attrGet("src") or "")
    source = escape(token.attrGet("src") or "", quote=True)
    return f'<a href="{source}">{label}</a>'


def extract_local_links(tokens):
    """Preserve local link labels in the card and return clickable chat links."""
    links = {}
    for block in tokens:
        children = block.children or []
        local_link = None
        for index, token in enumerate(children):
            if token.type == "link_open":
                href = token.attrGet("href") or ""
                if href.startswith("/") and not href.startswith("//"):
                    local_link = (index, href)
                    token.tag = "span"
                    token.attrs = {}
            elif token.type == "link_close" and local_link:
                start, href = local_link
                label = "".join(part.content for part in children[start + 1 : index])
                label = " ".join(label.split()) or href
                label = re.sub(r"([\\\[\]`*_~<>!])", r"\\\1", label)
                links.setdefault(href, f"[{label}](<{href}>)")
                token.tag = "span"
                local_link = None
    return links.values()


def write_visual(markdown, directory):
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    parser.renderer.rules.update({
        "image": render_image,
        "table_open": lambda *_: '<div class="table-wrap"><table>\n',
        "table_close": lambda *_: "</table></div>\n",
    })
    env = {}
    tokens = parser.parse(markdown, env)
    has_rtl = False
    for index, inline in enumerate(tokens):
        if inline.type != "inline":
            continue
        directions = {
            bidirectional(char)
            for child in inline.children or []
            if child.type in {"text", "image"}
            for char in child.content
        }
        rtl = bool(directions & {"R", "AL"})
        has_rtl |= rtl
        block = tokens[index - 1]
        if not rtl and "L" in directions and block.type in {"paragraph_open", "heading_open"}:
            block.attrSet("dir", "ltr")
    if not has_rtl:
        return None
    if directory is None or not directory.is_dir():
        raise ValueError("תצוגה בתוך ההודעה זמינה בצ׳אט של Orca עם תיקיית תצוגה נגישה.")

    local_links = extract_local_links(tokens)
    body = parser.renderer.render(tokens, parser.options, env)
    template = Path(__file__).resolve().with_name("page.html").read_text(encoding="utf-8")
    page = template.replace("<!-- CONTENT -->", body, 1).encode("utf-8")
    if len(page) >= 512 * 1024:
        raise ValueError("התצוגה חורגת ממגבלת 512 ק״ב של Orca.")
    filename = f"rtl-output-{uuid4().hex}.html"
    with (directory / filename).open("xb") as output:
        output.write(page)
    return filename, local_links


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--keep-original", action="store_true",
                     help="Omit the chat link footer when the original stays visible")
    cli.add_argument("markdown", nargs="?", help="Original Markdown (defaults to stdin)")
    args = cli.parse_args()
    scratch = os.environ.get("ORCA_CHAT_SCRATCH_DIR")
    try:
        markdown = args.markdown if args.markdown is not None else sys.stdin.read()
        visual = write_visual(markdown, Path(scratch) if scratch else None)
    except ModuleNotFoundError:
        cli.exit(1, "ממיר Markdown אינו זמין בסביבת Python זו (markdown-it-py).\n")
    except (OSError, ValueError) as error:
        cli.exit(1, f"יצירת התצוגה נכשלה. {error}\n")
    if visual is None:
        return
    filename, local_links = visual
    print(f'::orca-visual{{file="{filename}" title="תצוגה מימין לשמאל"}}')

    if local_links and not args.keep_original:
        print()
        print("\n".join(f"- {link}" for link in local_links))


if __name__ == "__main__":
    main()
