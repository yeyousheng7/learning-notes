"""Generate timeline summaries when a spark has no explicit excerpt marker."""

from html import escape
from html.parser import HTMLParser
import re

from mkdocs.plugins import event_priority


EXCERPT_LENGTH = 60
_TITLE = re.compile(r"\s*(<h[1-6]\b[^>]*>.*?</h[1-6]>)(.*)", re.DOTALL)
_SENTENCE_ENDINGS = ("。", "！", "？", ".", "!", "?", "…")
_CLOSING_MARKS = "”’\"')）]】}》〉」』"
_MID_SENTENCE_MARKS = "，,、；;：:—–- \t"


class _Text(HTMLParser):
    """Read summary text without carrying incomplete HTML into the timeline."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignored = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignored = True
        elif tag in {"p", "div", "li", "blockquote", "pre", "br", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append(" ")
        elif tag == "img":
            self.parts.append(dict(attrs).get("alt", ""))

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.ignored = False
        elif tag in {"p", "div", "li", "blockquote", "pre", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


# The blog plugin renders excerpts at priority -100; shorten them afterwards.
@event_priority(-110)
def on_page_context(context, *, page, config, nav):
    if page.file.src_uri != "sparks/index.md":
        return context

    separator = config.plugins["material/blog"].config.post_excerpt_separator
    for excerpt in context.get("posts", []):
        if separator in excerpt.post.markdown:
            continue

        title = _TITLE.search(excerpt.content)
        parser = _Text()
        parser.feed(excerpt.content[:title.start()] + title[2])
        text = " ".join("".join(parser.parts).split())
        if len(text) <= EXCERPT_LENGTH:
            continue

        summary = text[:EXCERPT_LENGTH].rstrip()
        body = summary.rstrip(_CLOSING_MARKS)
        if not body.rstrip().endswith(_SENTENCE_ENDINGS):
            closing = summary[len(body):]
            summary = body.rstrip(_MID_SENTENCE_MARKS) + closing + "..."

        excerpt.content = f"{title[1]}\n<p>{escape(summary)}</p>"
        excerpt.more = text[EXCERPT_LENGTH:]

    return context
