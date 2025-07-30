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

APP_MODE = "deployment"
assert APP_MODE == "testing" or APP_MODE == "deployment"

if APP_MODE == "testing":
    app = FastAPI()
    origins = [
        "https://muyao-lu.github.io/tosautomation/",
        "http://muyao-lu.github.io/tosautomation/",
        "https://muyao-lu.github.io",
        "http://muyao-lu.github.io",
        "http://localhost:63342"
    ]

elif APP_MODE == "deployment":
    app = FastAPI(docs_url=None, redoc_url=None)
    origins = [
        "https://muyao-lu.github.io/tosautomation/",
        "http://muyao-lu.github.io/tosautomation/",
        "https://muyao-lu.github.io",
        "http://muyao-lu.github.io"
    ]

webscraper = ScraperDatabaseControl()
ai_api = AiAccess()
ip_validation = IpController()


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
    lang: str
    short: bool
    query : str = None

@app.post("/{document_type}/")
async def process_terms_of_service(document_type, request: Request):
    print("Request initiated with the following info:", "\nLink:", request.link, "\nIp:",
          request.ip, "\nLang:", request.lang, "\nShort:", request.short, "\nQuery:", request.query)
    try:
        if check_link(request.link):
            if ip_validation.check_request_time_validity(request.ip):
                if document_type != "followup":
                    try:
                        text = ai_api.call_summarizer(link=request.link, short=request.short, language_level=request.lang)
                    except NoResultFound:
                        print("No result found for", request.link)
                        webscraper.scrape_to_db(request.link)
                        text = ai_api.call_summarizer(link=request.link, short=request.short, language_level=request.lang)
                    except Exception as e:
                        print(e)

                    return convert_to_html(text)
                else:
                    if request.query is not None:
                        try:
                            text = ai_api.chat_completion(short=request.short, link=request.link, query=request.query, language_level=request.lang)
                        except NoResultFound:
                            webscraper.scrape_to_db(request.link)
                            text = ai_api.chat_completion(short=request.short, link=request.link, query=request.query, language_level=request.lang)
                        return convert_to_html(text)
        
                    else:
                        raise HTTPException(status_code=400, detail="Query parameter cannot be empty for followup questions. Please provide a query in the request body.")
            else:
                raise HTTPException(status_code=429, detail="Too many requests. Please obey the 20s rule between requests")
        else:
            raise HTTPException(status_code=400, detail="Please provide a valid link")
    except Exception as e:
        return e


if APP_MODE == "testing":
    if __name__ == '__main__':
        uvicorn.run(app, port=800)
