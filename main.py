from fastapi import FastAPI
import sys
import uvicorn, datetime
from pydantic import BaseModel
from ai import *
from convert import *
from ip import *

sys.path.insert(1, "server/")

app = FastAPI()

webscraper = ScraperDatabaseControl()
ai_api = AiAccess()
ip_validation = IpController()
class Request(BaseModel):
    link: str
    ip: str
    lang: str = "middle"
    short: bool = False
    query : str = None


@app.post("/server/{document_type}/")
async def root(document_type, request: Request):
    if ip_validation.check_request_time_validity(request.ip):
        if document_type != "f":
            webscraper.scrape_to_db(request.link)
            website = webscraper.get_full_website()
            text = ai_api.call_summarizer(short=request.short, policy=website, language_level=request.lang)
            return convert_to_html(text)
        else:
            if request.query is not None:
                text = ai_api.chat_completion(link=request.link, query=request.query)
                return convert_to_html(text)
            else:
                return "Cannot parse request with empty query"
    else:
        return "Too many requests"


if __name__ == '__main__':
    uvicorn.run(app, port=800)