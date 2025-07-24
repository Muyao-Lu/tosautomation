from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from langchain_cohere import CohereEmbeddings
import dotenv, requests
from math import sqrt
dotenv.load_dotenv()

APP_MODE = "deployment"

def dot_product(vector_a, vector_b):
    assert len(vector_a) == len(vector_b)
    r = 0
    for i in range(len(vector_a)):
        r += vector_a[i] * vector_b[i]

    return r

def norm(vector):
    r = 0
    for item in vector:
        r += item**2

    return sqrt(r)

class Ranker:

    def __init__(self, min_confidance=0.55):
        """
            Initiates a ranker for RAG
            :param min_confidance: Link to privacy policy to generate prompt for
            :return: Document if distance for top element is lesser than confidance. Segment of document if it is greater
        """
        self.embedder = CohereEmbeddings(model="embed-english-light-v3.0")
        self.rewriter = Rewriter()
        self.MIN_CONFIDANCE = min_confidance

    def rank(self, query, documents, origin):

        embedded_text_segments = self.embedder.embed_documents(documents)
        query_enhanced = self.embedder.embed_query(self.rewriter.call_ai(query, origin=origin))
        results = zip(embedded_text_segments, documents)

        results = map(lambda x: [dot_product(x[0], query_enhanced)/(norm(x[0]) * norm(query_enhanced)), x[1]], iter(results))
        results = sorted((item for item in results), key = lambda x: x[0], reverse=True)
        for item in results:
            print(item)

        if results[0][0] > self.MIN_CONFIDANCE:
            return results[0]
        else:
            return "No result exceeded limit"

class Rewriter:
    def __init__(self):
        self.URL = "https://ai.hackclub.com/chat/completions"

    def call_ai(self, prompt_to_rewrite, origin) -> str:
        prompt = ("Please rewrite the following prompt for better Retrieval Augmented Generation search. "
                  "No explanation is needed, just rewrite and return the prompt alone. If the prompt is incoherent"
                  "leave it as is. Unless otherwise stated assume the excerpt is from {origin} \n {prompt}")
        prompt = prompt.format(prompt=prompt_to_rewrite, origin=origin)

        headers = {
            'Content-Type': 'application/json',
        }

        json_data = {
            'messages': [
                {
                    'role': 'system',
                    'content': prompt,
                },
            ],
        }

        response = requests.post(self.URL, headers=headers, json=json_data)
        print(response.json()["choices"][0]["message"]["content"])

        return response.json()["choices"][0]["message"]["content"]


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
    origin: str

@app.post("/")
async def process_ranking_request(request: RankerModel):
    result = ranker.rank(query=request.query, documents=request.documents, origin=request.origin)
    return result

if APP_MODE == "testing":
    if __name__ == "__main__":
        uvicorn.run(app, port=8000)

