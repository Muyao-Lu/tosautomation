print("started")
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
import uvicorn
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound

from ai import AiAccess
from scraper import ScraperDatabaseControl
from convert import convert_to_html
from ip import IpController

print("0")
app = FastAPI()

webscraper = ScraperDatabaseControl()
ai_api = AiAccess()
ip_validation = IpController()
print("0.5")
class Request(BaseModel):
    link: str
    ip: str
    lang: str = "middle"
    short: bool = False
    query : str = None


@app.post("/{document_type}/")
async def process_terms_of_service(document_type, request: Request):
    if ip_validation.check_request_time_validity(request.ip):
        if document_type != "followup":

            webscraper.scrape_to_db(request.link)
            website = webscraper.get_full_website()
            text = ai_api.call_summarizer(short=request.short, policy=website, language_level=request.lang)

            return convert_to_html(text)
        else:

            if request.query is not None:
                print("1")
                try:
                    text = ai_api.chat_completion(link=request.link, query=request.query)
                    print("2")
                    return convert_to_html(text)
                except NoResultFound:
                    webscraper.scrape_to_db(request.link)
                    text = ai_api.chat_completion(link=request.link, query=request.query)
                    print("3")
                    return convert_to_html(text)

            else:
                print("4")
                raise HTTPException(status_code=400, detail="Query parameter cannot be empty for followup questions. Please provide a query in the request body.")
    else:
        print("5")
        raise HTTPException(status_code=429, detail="Too many requests. Please obey the 20s rule between requests")


if __name__ == '__main__':
    uvicorn.run(app, port=800)
