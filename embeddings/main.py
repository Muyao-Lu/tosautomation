from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from langchain_cohere import CohereEmbeddings
import dotenv
dotenv.load_dotenv()

APP_MODE = "deployment"

def dot_product(vector_a, vector_b):
    assert len(vector_a) == len(vector_b)
    r = 0
    for i in range(len(vector_a)):
        r += abs(vector_a[i] + vector_b[i])

    return r

def norm(vector):
    r = 0
    for item in vector:
        r += item**2

    return r ** (1/2)

class Ranker:

    def __init__(self):
        self.embedder = CohereEmbeddings(model="embed-english-light-v3.0")

    def rank(self, query, documents):

        embedded_text_segments = self.embedder.embed_documents(documents)
        query = self.embedder.embed_query(query)
        results = zip(embedded_text_segments, documents)

        results = map(lambda x: [dot_product(x[0], query)/(norm(x[0]) * norm(query)), x[1]], iter(results))
        results = sorted((item for item in results), key = lambda x: x[0], reverse=True)

        return results[0]


app = FastAPI(docs_url=None, redoc_url=None)
ranker = Ranker()

if APP_MODE == "testing":
    origins = [
        "https://tosautomation-backend.vercel.app",
        "http://127.0.0.1:800"
    ]
elif APP_MODE == "deployment":
    origins = ["https://tosautomation-backend.vercel.app"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["POST"],
    allow_headers=["*"],
)

class RankerModel(BaseModel):
    query: str
    documents: list

@app.post("/")
async def process_ranking_request(request: RankerModel):
    result = ranker.rank(query=request.query, documents=request.documents)
    return result

if APP_MODE == "testing":
    if __name__ == "__main__":
        uvicorn.run(app, port=8000)

