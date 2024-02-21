#!/usr/bin/env python
from __future__ import annotations

from typing import Generator, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import BaseModel, PrivateAttr


class WebPage(BaseModel):
    """Represents a web page with methods to process its content.

    Attributes:
        inner_text: The text content of the web page.
        html: The HTML content of the web page.
        url: The URL of the web page.
        _soup: A BeautifulSoup object for parsing HTML, initialized lazily.
        _title: The title of the web page, extracted from its HTML, initialized lazily.
    """

    inner_text: str
    html: str
    url: str

    _soup: Optional[BeautifulSoup] = PrivateAttr(default=None)
    _title: Optional[str] = PrivateAttr(default=None)

    @property
    def soup(self) -> BeautifulSoup:
        """Lazily initializes and returns a BeautifulSoup object for the web page.

        Returns:
            A BeautifulSoup object for parsing the web page's HTML.
        """
        if self._soup is None:
            self._soup = BeautifulSoup(self.html, "html.parser")
        return self._soup

    @property
    def title(self):
        """Extracts and returns the title of the web page.

        Returns:
            The title of the web page as a string.
        """
        if self._title is None:
            title_tag = self.soup.find("title")
            self._title = title_tag.text.strip() if title_tag is not None else ""
        return self._title

    def get_links(self) -> Generator[str, None, None]:
        """Finds and yields all unique links present in the web page.

        Yields:
            Each link found in the web page as a string.
        """
        for i in self.soup.find_all("a", href=True):
            url = i["href"]
            result = urlparse(url)
            if not result.scheme and result.path:
                yield urljoin(self.url, url)
            elif url.startswith(("http://", "https://")):
                yield urljoin(self.url, url)


def get_html_content(page: str, base: str):
    """Extracts and returns the text content from a web page's HTML.

    Args:
        page: The HTML content of the web page.
        base: The base URL of the web page.

    Returns:
        The text content of the web page.
    """
    soup = _get_soup(page)

    return soup.get_text(strip=True)


def _get_soup(page: str):
    """Creates and returns a BeautifulSoup object for a given HTML content.

    Args:
        page: The HTML content to parse.

    Returns:
        A BeautifulSoup object for parsing the given HTML content.
    """
    soup = BeautifulSoup(page, "html.parser")
    # https://stackoverflow.com/questions/1936466/how-to-scrape-only-visible-webpage-text-with-beautifulsoup
    for s in soup(["style", "script", "[document]", "head", "title"]):
        s.extract()

    return soup
