from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlmodel import SQLModel, Field, create_engine, select, Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.exc import NoResultFound

ranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


class VectorDatabaseModel(SQLModel, table=True):
    id: int | None = Field(None, primary_key=True)
    link: str = Field(index=True)
    document: str

class VectorDatabaseControl:
    def __init__(self, top_k=1):
        self.DATABASE_URL = "sqlite:///vector.db"
        self.engine = create_engine(self.DATABASE_URL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )

        self.top_k = top_k
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
            return ranker.rank(query=query, documents=all_sections, return_documents=True)
        except NoResultFound:
            return None

vector_db = VectorDatabaseControl()
vector_db.add("hello", "test.com")
