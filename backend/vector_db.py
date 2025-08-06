from sqlmodel import SQLModel, Field, create_engine, select, Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.exc import NoResultFound
import requests, os, dotenv
import datetime
dotenv.load_dotenv()


class VectorDatabaseModel(SQLModel, table=True):
    id: int | None = Field(None, primary_key=True)
    link: str = Field(index=True)
    document: str
    last_updated: datetime.datetime = Field(default=datetime.datetime.now())

class VectorDatabaseControl:
    def __init__(self, time_to_update_db_entry:int=5):
        """
            Function to initialize Control for Vector Database
            :param time_to_update_db_entry: Max time in days before a database entry within the vector db is updated
        """
        self.DATABASE_URL = "postgresql://postgres.fkbsrnqotuynrsplskxe:{key}@aws-0-us-east-2.pooler.supabase.com:6543/postgres".format(key=os.environ["SUPABASE_KEY"])
        self.TIME_TO_UPDATE_DB = time_to_update_db_entry * 24 * 60 * 60

        self.engine = create_engine(self.DATABASE_URL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )

        # self.URL = "https://tosautomation-embeddings.vercel.app"
        self.URL = "http://127.0.0.1:8000"
        SQLModel.metadata.create_all(self.engine)

    def add(self, item, link):
        with Session(self.engine) as session:
            try:
                l = self.get_by_link(link)
                if (datetime.datetime.now() - l.last_updated).total_seconds() > self.TIME_TO_UPDATE_DB:
                    session.add(VectorDatabaseModel(link=link, document=item))
                    session.commit()
            except NoResultFound:
                session.add(VectorDatabaseModel(link=link, document=item))
                session.commit()


    def get_by_link(self, link):
        with Session(self.engine) as session:
            condition = select(VectorDatabaseModel).where(VectorDatabaseModel.link == link)
            results = session.exec(condition)

            return results.one()


    def get_closest_neighbor(self, link, query, rewrite=True):
        try:
            item = self.get_by_link(link)
            all_sections = self.text_splitter.split_text(item.document)
            headers = {
                'Content-Type': 'application/json',
            }

            json_data = {
                "query": query,
                "documents": all_sections,
                "origin": link,
                "rewrite": rewrite
            }

            response = requests.post(self.URL, headers=headers, json=json_data)
            return response.json()

        except NoResultFound:
            return None

vector_db = VectorDatabaseControl()
