from langchain_hyperbrowser import HyperbrowserLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vector_db import vector_db
import os

class ScraperModel:
    def __init__(self):
        self.api_key = os.environ["Hyperbrowser-key"]

    def scrape(self, link):
        loader = HyperbrowserLoader(
            urls=link,
            api_key=self.api_key,
        )

        return loader.load()


class ScraperDatabaseControl:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        self.scraper = ScraperModel()
        self.vector_db = vector_db
        self.document = None

    def scrape_to_db(self, link):
        self.document = self.scraper.scrape(link)
        all_splits = self.text_splitter.split_documents(self.document)
        for split in all_splits:
            self.vector_db.add(split.page_content)

    def get_full_website(self):
        if self.document is not None:
            return self.document[0].page_content
        else:
            return None

    def get_similar_term(self, query):
        if self.document is not None:
            return self.vector_db.get_closest_neighbor(query)[0]
        else:
            return None

"""""
import urllib.request
import bs4
from bs4 import BeautifulSoup

def check_dynamic(text: str) -> bool:
    return len(text.replace("\n", "")) < (len(text) * 0.9)

def delete_all(tag_name: str, document: BeautifulSoup) -> None:
    tags = document.find_all(tag_name)
    for tag in tags:
        tag.decompose()


class _ScraperModel:
    def __init__(self):
        self.DEL_LIST = ["script", "style", "head", "iframe", "nav", "header", "footer"]
        self.TIMEOUT = 3


    def decode_link(self, link: str, replacement_arguments: dict):
        # Helper function to process sanitized links
        # :param link: Link to process
        # :param replacement_arguments: Operations to perform in the format {character segment to replace: replacement}
        # :return: processed link
        l = link
        for item in replacement_arguments.keys():
            l.replace(item, replacement_arguments[item])
        return l



    def scrape(self, link) -> dict:
        # Webscraper
        # :param link: Link
        # :return: Dictionary with the following keys:
        # failed: Whether the scraping timed out/failed
        # html: The html of the scraped website if the scraping succeeded, or the link to the website if it didn't
        failed = False
        try:
            raw = urllib.request.urlopen(self.decode_link(link, {"%3A": ":", "%2F": "/"}), timeout=self.TIMEOUT)
            html = BeautifulSoup(raw, "html.parser")

        except:
            failed = True
            html = link

        return {"failed": failed, "html": html}


class ScraperControl:
    def __init__(self):
        self.DEL_LIST = ["script", "style", "head", "iframe", "nav", "header", "footer"]
        self.scraper = _ScraperModel()

    def scrape(self, link):
        raw  = self.scraper.scrape(link)
        if not raw["failed"]:
            html = raw["html"]
            html = self.clean_result(html)
            text = self.find_main_body(html, len(html.text))

            if check_dynamic(text):
                return link
            return text
        else:
            return link

    def clean_result(self, html) -> BeautifulSoup:
        html_cleaned = html
        for item in self.DEL_LIST:
            delete_all(item, html_cleaned)

        return html

    def find_main_body(self, html: BeautifulSoup | bs4.PageElement, original_length: int,
                       distribution_ratio: int = 0.9) -> str:
        text_lengths = []

        for child in list(html.children):
            text_lengths.append(len(child.text))

        passes = list(filter(lambda x: x > (original_length * distribution_ratio), text_lengths))
        if len(passes) > 0:
            return self.find_main_body(list(html.children)[text_lengths.index(max(passes))], original_length)

        else:
            return html.text
"""""
