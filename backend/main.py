from fastapi import FastAPI
from fastapi.exceptions import HTTPException
import uvicorn
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from fastapi.middleware.cors import CORSMiddleware
from ai import AiAccess
from scraper import ScraperDatabaseControl
from convert import convert_to_html, check_link
from ip import IpController

app = FastAPI(docs_url=None, redoc_url=None)

webscraper = ScraperDatabaseControl()
ai_api = AiAccess()
ip_validation = IpController()

origins = [
    "https://muyao-lu.github.io/tosautomation/",
    "http://muyao-lu.github.io/tosautomation/",
    "https://muyao-lu.github.io",
    "http://muyao-lu.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Request(BaseModel):
    link: str
    ip: str
    lang: str = "middle"
    short: bool = False
    query : str = None

@app.post("/{document_type}/")
async def process_terms_of_service(document_type, request: Request):
    try:
        if check_link(request.link):
            if ip_validation.check_request_time_validity(request.ip):
                if document_type != "followup":
        
                    webscraper.scrape_to_db(request.link)
                    website = webscraper.get_full_website()
                    text = ai_api.call_summarizer(short=request.short, policy=website, language_level=request.lang)
        
                    return convert_to_html(text)
                else:
                    if request.query is not None:
                        try:
                            text = ai_api.chat_completion(link=request.link, query=request.query)
                            return convert_to_html(text)
                        except NoResultFound:
                            webscraper.scrape_to_db(request.link)
                            text = ai_api.chat_completion(link=request.link, query=request.query)
                            return convert_to_html(text)
        
                    else:
                        raise HTTPException(status_code=400, detail="Query parameter cannot be empty for followup questions. Please provide a query in the request body.")
            else:
                raise HTTPException(status_code=429, detail="Too many requests. Please obey the 20s rule between requests")
        else:
            raise HTTPException(status_code=400, detail="Please provide a valid link")
    except Exception as e:
        return e



if __name__ == '__main__':
    uvicorn.run(app, port=800)
