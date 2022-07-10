from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from urllib.parse import urljoin, urlparse
from datetime import datetime
from flask import make_response, request
from urllib.error import HTTPError
import feedparser

USER_AGENT = "Mozilla/5.0 (Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"


class SlugError(Exception):
    pass


class LastPageError(Exception):
    pass


class Scheduler:
    title = None

    def __init__(self, args, homepage):
        self.feed = FeedGenerator()

        self.feed.id(homepage)
        self.feed.link(href=homepage)

        self.query = args.get("query")
        self.iframe = args.get("iframe") == "on"

        self.pages = int(args.get("per-day", default="1"))
        if self.pages < 1 or self.pages > 10:
            raise ValueError("<code>per-day</code> must have value between 1 and 10")

        start = int(args.get("start"))
        if start < 1:
            raise ValueError("Number of first entry must be positive.")
        start_date = datetime.strptime(args.get("date"), "%Y-%m-%d")

        diff = (datetime.now() - start_date).days

        current = start + (diff + 1) * self.pages - 1

        oldest = current - (3 * self.pages)
        oldest = oldest if oldest > start else start

        self.range = range(oldest, current + 1)

        for num in self.range:
            self.create_entry(num)

    def create_entry(self, url, title):
        entry = self.feed.add_entry()
        entry.id(url)
        entry.title(title)
        entry.link(href=url)

        if self.iframe:
            content = f'<iframe width="100%" height="1000px" src="{url}"/>'
        elif self.query != "":
            req = Request(url, headers={"User-Agent": USER_AGENT})
            page = BeautifulSoup(urlopen(req), features="lxml")

            content = ""
            for img in page.body.select(self.query):
                src = urljoin(url, img["src"])
                content += f'<img src="{src}"/>'

        else:
            content = f'<a href="{url}">{title}</>'

        entry.content(content=content, type="html")

    def response(self):
        self.feed.title(self.title)

        response = make_response(self.feed.atom_str())
        response.headers.set("Content-Type", "application/rss+xml")
        return response


class NumberedScheduler(Scheduler):
    def __init__(self, args):
        self.scheme = args.get("scheme")
        self.title = args.get("title")

        if self.title is None or self.title == "":
            raise ValueError("title must be set.")

        parsed_scheme = urlparse(self.scheme)

        homepage = parsed_scheme.scheme + "//" + parsed_scheme.netloc

        super().__init__(args, homepage)

    def create_entry(self, num):
        url = self.scheme.format(num)

        title = self.title + " #" + str(num)

        super().create_entry(url, title)

class FeedScheduler(Scheduler):
    def __init__(self, args):
        self.feed = FeedGenerator()

        self.url = args.get("url")
        self.iframe = args.get("iframe") == "on"
        self.query = args.get("query")

        parsed = feedparser.parse(self.url)

        self.title = parsed.feed.title

        self.feed.id(parsed.feed.link)
        self.feed.link(href=parsed.feed.link)

        for entry in parsed.entries[0:5]:
            self.create_entry(entry)
            

        

    def create_entry(self, entry):
        url = entry.link

        title = entry.title

        super().create_entry(url, title)


class ComicRocketScheduler(Scheduler):
    def __init__(self, args):
        self.slug = args.get("slug")
        if self.slug is None or self.slug == "":
            raise ValueError("<code>slug</code> must be set")

        homepage = f"https://www.comic-rocket.com/explore/{self.slug}/"

        try:
            super().__init__(args, homepage)
        except LastPageError:
            entry = self.feed.add_entry()
            entry.id(homepage)
            entry.title("End of the feed")
            entry.link(href=homepage)

    def create_entry(self, num):
        url = f"https://www.comic-rocket.com/read/{self.slug}/{num}"
        req = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            page = BeautifulSoup(urlopen(req), features="lxml")
        except HTTPError:
            raise SlugError

        try:
            url = page.body.select("#serialpagebody iframe")[0]["src"]
        except IndexError:
            raise LastPageError

        if self.title is None:
            self.title = page.title.string.split(" - ")[0]

        super().create_entry(url, self.title + " #" + str(num))