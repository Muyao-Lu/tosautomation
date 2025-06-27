from langchain_hyperbrowser import HyperbrowserLoader
from vector_db import vector_db
import os, dotenv
dotenv.load_dotenv()

class ScraperModel:
    def __init__(self):
        self.api_key = os.environ["HYPERBROWSER_KEY"]

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
        self.vector_db.add(link=link, item=str(self.document[0].page_content))

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
