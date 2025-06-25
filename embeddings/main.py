from sentence_transformers import CrossEncoder
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


class Ranker:

    def __init__(self):
        self.ranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

    def rank(self, query, documents):
        text_list = []
        rankings = self.ranker.rank(query=query, documents=documents, return_documents=True)
        for item in rankings:
            text_list.append({"score": float(item["score"]), "text": item["text"]})
        return text_list


app = FastAPI()
ranker = Ranker()

origins = [
    "https://tosautomation-backend.vercel.app"
]

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

if __name__ == "__main__":
    uvicorn.run(app, port=800)


