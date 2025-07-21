from sqlmodel import SQLModel, Field, create_engine, select, Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.exc import NoResultFound
import requests, os, dotenv

dotenv.load_dotenv()


class VectorDatabaseModel(SQLModel, table=True):
    id: int | None = Field(None, primary_key=True)
    link: str = Field(index=True)
    document: str

class VectorDatabaseControl:
    def __init__(self, top_k=1):
        self.DATABASE_URL = "postgresql://postgres.fkbsrnqotuynrsplskxe:{key}@aws-0-us-east-2.pooler.supabase.com:6543/postgres".format(key=os.environ["SUPABASE_KEY"])
        self.engine = create_engine(self.DATABASE_URL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )

        self.URL = "https://tosautomation-embeddings.vercel.app"
        SQLModel.metadata.create_all(self.engine)

    def add(self, item, link):
        with Session(self.engine) as session:
            try:
                self.get_by_link(link)
            except NoResultFound:
                session.add(VectorDatabaseModel(link=link, document=item))
                session.commit()


    def get_by_link(self, link):
        with Session(self.engine) as session:
            condition = select(VectorDatabaseModel).where(VectorDatabaseModel.link == link)
            results = session.exec(condition)

            return results.one()


    def get_closest_neighbor(self, link, query):
        try:
            item = self.get_by_link(link)
            all_sections = self.text_splitter.split_text(item.document)
            headers = {
                'Content-Type': 'application/json',
            }

            json_data = {
                "query": query,
                "documents": all_sections
            }

            response = requests.post(self.URL, headers=headers, json=json_data)
            print(response)
            return response.json()[1]

        except NoResultFound:
            return None

vector_db = VectorDatabaseControl()
