from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import dotenv, os, cohere
from groq import Groq
dotenv.load_dotenv()

APP_MODE = "deployment"

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

    def rank(self, query, documents, origin, rewrite):
        if rewrite:
            query_enhanced = self.rewriter.call_ai(query, origin=origin)
        else:
            query_enhanced = query

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
        self.client = Groq(api_key=os.environ.get("GROQ_KEY"))
        self.model = "llama-3.1-8b-instant"

    def call_ai(self, prompt_to_rewrite, origin) -> str:
        prompt = ("Please rewrite the following prompt for better Retrieval Augmented Generation search. "
                  "No explanation is needed, just rewrite and return the prompt alone. If the prompt is incoherent"
                  "leave it as is. Unless otherwise stated assume the excerpt is from {origin} \n {prompt}")
        prompt = prompt.format(prompt=prompt_to_rewrite, origin=origin)

        messages = [
            {
                'role': 'user',
                'content': prompt,

            },
        ]

        res = self.client.chat.completions.create(model=self.model, temperature=0, messages=messages)

        return res.choices[0].message.content


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
    rewrite: bool

@app.post("/")
async def process_ranking_request(request: RankerModel):
    if len(request.documents) > 0:
        print(request.rewrite)
        result = ranker.rank(query=request.query, documents=request.documents, origin=request.origin, rewrite=request.rewrite)
        print("returning", result)
        return result
    else:
        return None

if APP_MODE == "testing":
    if __name__ == "__main__":
        uvicorn.run(app, port=8000)


