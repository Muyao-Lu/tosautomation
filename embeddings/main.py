from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import dotenv, requests
from math import sqrt
import cohere
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
        self.client = cohere.ClientV2()
        self.rewriter = Rewriter()
        self.MIN_CONFIDANCE = min_confidance

    def rank(self, query, documents, origin):

        query_enhanced = self.rewriter.call_ai(query, origin=origin)
        results = self.client.rerank(
            model="rerank-v3.5",
            query=query_enhanced,
            documents=documents,
            top_n=5,
        )


        results = dict(results)
        print(results["results"][0])

        first_item_data = dict(results["results"][0])
        results_text = documents[first_item_data["index"]]




        if float(first_item_data["relevance_score"]) > self.MIN_CONFIDANCE:
            return results_text
        else:
            """""
                Will turn into a lambda if you believe hard enough
            """""
            l = []
            for item in results["results"]:
                l.append(documents[dict(item)["index"]])

            return l

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
    print("returning", result)
    return result

if APP_MODE == "testing":
    if __name__ == "__main__":
        uvicorn.run(app, port=8000)

