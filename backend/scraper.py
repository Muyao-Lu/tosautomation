from langchain_hyperbrowser import HyperbrowserLoader
from pdfminer.pdfparser import PDFSyntaxError

from vector_db import vector_db
import os, dotenv
import requests, io, pdfplumber
dotenv.load_dotenv()

class ScraperModel:
    def __init__(self):
        self.api_key = os.environ["HYPERBROWSER_API_KEY"]

    def scrape(self, link):
        loader = HyperbrowserLoader(
            urls=link,
            api_key=self.api_key,
        )

        return loader.load()


class ScraperDatabaseControl:
    def __init__(self):

        self.scraper = ScraperModel()
        self.vector_db = vector_db
        self.document = None

    def scrape_to_db(self, link):
        self.document = self.scraper.scrape(link)
        print("scraped", self.document[0].page_content)
        if len(self.document[0].page_content) < 1:
            print("pdf")
            self.document = self.extract_pdf(link)
            self.vector_db.add(link=link, item=self.document)
        else:
            self.vector_db.add(link=link, item=str(self.document[0].page_content))
        print("added")


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

    def extract_pdf(self, link):
        d = ""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(link, headers=headers)
            stream = io.BytesIO(response.content)
            with pdfplumber.open(stream) as pdf:
                for page in pdf.pages:
                    d += page.extract_text()

            return d
        except PDFSyntaxError:
            return ""

