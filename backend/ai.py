from openai import OpenAI
import json, tiktoken
from scraper import *
from vector_db import vector_db
from groq import Groq, RateLimitError


dotenv.load_dotenv()


class AiAccess:
    """
    Class for accessing the AI API
    """
    def __init__(self):
        self.MAIN_MODEL = _HcAiModel()
        self.PROMPTER = _AiPromptGenerator()
        self.SEGMENTS = ["information-cookies",
                         "rules-and-reg",
                         "user-rights",
                         "safety"]
        self.SEGMENT_MAPPINGS = {
            "information-cookies": "*What the company does with your information. How do they collect it? How is it stored? How is it used? Is data sold or shared?",
            "rules-and-reg": "*What rules must the user obey to use the services? What regulations are in place? What aren't users allowed to do?",
            "user-rights": "*What rights do users have over their own information? How about in disputes with the company?",
            "safety": "*How does the company ensure a user's safety when using their services? How are users protected?"}



    def call_summarizer(self, link, short, language_level="middle"):
        summary = ""
        for item in self.SEGMENTS:
            prompt = self.PROMPTER.generate_prompt_for_chunk(chunk_type=item,
                                                             chunk_description=self.SEGMENT_MAPPINGS[item], link=link,
                                                             language_level=language_level)
            try:
                summary += self.MAIN_MODEL.call_ai(prompt) + "\n\n"
            except RateLimitError:
                return "Backend Rate Limit Exceeded. Try again later."
            except Exception as e:
                print("Main model failed because of {exception}".format(exception=e))
                return "Something went wrong"

        doc_sum = self.PROMPTER.generate_prompt_for_summary(document=summary, language_level=language_level)
        refined_sum = self.MAIN_MODEL.call_ai(doc_sum)


        print("s", summary)
        return refined_sum

    def chat_completion(self, short, query, link, language_level="middle"):
        if short:
            prompt = self.PROMPTER.generate_short_completion_prompt(query, link, language_level)
        else:
            prompt = self.PROMPTER.generate_completion_prompt(query, link, language_level)

        try:
            return self.MAIN_MODEL.call_ai(prompt)
        except Exception as e:
            print("Main model failed because of {exception}. Falling back".format(exception=e))


class _AiPromptGenerator:
    """
        Class for prompt generation
    """
    def __init__(self):
        self.prompts = json.load(open("prompts.json", "r"))
        self.SCRAPER = ScraperDatabaseControl()
        self.TOKEN_COUNTER = tiktoken.get_encoding("cl100k_base")

    def generate_prompt_for_chunk(self, chunk_type, chunk_description, link, language_level):
        policy = vector_db.get_closest_neighbor(link=link, query=chunk_description, rewrite=False)
        content = self.prompts["language-levels"][language_level]
        content += self.prompts["normal"]["default-template"].format(link=link, format=self.prompts["normal"]["prompt-segments"][chunk_type], excerpt=policy)

        return content

    def generate_prompt_for_summary(self, document, language_level):
        content = self.prompts["language-levels"][language_level]
        content += self.prompts["normal"]["summary-template"].format(excerpt=document)
        return content

    def generate_completion_prompt(self, query, link, language_level="middle") -> str:
        """
            Generates prompt for chat-completions (followup questions) for the AI model.
            :param query: The query (question that the user asked)
            :param link: Link where the privacy policy originated from
            :param language_level: The level of complexity that the prompt generator should ask for
            :return: Complete prompt for chat completions
        """
        content = self.prompts["language-levels"][language_level]
        content += self.prompts["chat-comp"]["chat-comp"]
        closest_vector = vector_db.get_closest_neighbor(link=link, query=query)

        if closest_vector is None:
            self.SCRAPER.scrape_to_db(link)
            closest_vector = vector_db.get_closest_neighbor(link=link, query=query)

        content = content.format(link=link, question=query, excerpt=closest_vector)

        return content

    def generate_short_completion_prompt(self, query, link, language_level="middle") -> str:
        """
            Generates prompt for short chat-completions (followup questions) for the AI model.
            :param query: The query (question that the user asked)
            :param link: Link where the privacy policy originated from
            :param language_level: The level of complexity that the prompt generator should ask for
            :return: Complete prompt for chat completions
        """
        content = self.prompts["language-levels"][language_level]
        content += self.prompts["short-chat-comp"]["short-chat-comp"]
        closest_vector = vector_db.get_closest_neighbor(link=link, query=query)

        if closest_vector is None:
            self.SCRAPER.scrape_to_db(link)
            closest_vector = vector_db.get_closest_neighbor(link=link, query=query)

        content = content.format(link=link, question=query, excerpt=closest_vector)

        return content


    def generate_short_prompt(self, link, language_level="middle") -> str:
        """
            Generates prompt for short summaries of the privacy policy.
            :param link: Link to privacy policy to generate prompt for
            :param language_level: The level of complexity that the prompt generator should ask for
            :return: Complete prompt for short privacy policy/tos simplification
        """
        policy = vector_db.get_by_link(link).document

        if len(self.TOKEN_COUNTER.encode(policy)) > self.MODEL_TOKEN_LIMIT:
            chunks = self.chunker.split_and_process(policy)
            policy = ""
            for chunk in chunks:
                policy += chunk + "\n\n"

        content = self.prompts["language-levels"][language_level]
        content += self.prompts["short"]["short-head"]

        content += self.prompts["short"]["short-tail"]
        content = content.format(policy=policy)
        return content


class _GithubAiModel:
    """
        Class for accessing the AI API
    """
    def __init__(self):
        self.TOKEN = os.environ["AI_API_KEY"]
        self.MODEL = "openai/gpt-4.1-mini"
        self.URL = "https://models.github.ai/inference"

    def call_ai(self, prompt) -> str:# lang: str, mods: list, short: bool) -> str:
        client = OpenAI(
            base_url=self.URL,
            api_key=self.TOKEN,
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.MODEL,
        )

        return response.choices[0].message.content

class _HcAiModel:

    def __init__(self):
        self.URL = "https://api.groq.com/openai/v1/chat/completions"
        self.client = Groq(api_key=os.environ.get("GROQ_KEY"))
        self.model = "llama-3.1-8b-instant"

    def call_ai(self, prompt) -> str:
        print("prompted with", prompt)

        messages = [
            {
                'role': 'user',
                'content': prompt,

            },
        ]

        res = self.client.chat.completions.create(model=self.model, temperature=0.5, messages=messages)


        return res.choices[0].message.content



