from openai import OpenAI
import json, tiktoken
from scraper import *
from vector_db import vector_db
from langchain_text_splitters import RecursiveCharacterTextSplitter
from urllib3 import request
from urllib3.util.timeout import Timeout

dotenv.load_dotenv()


class AiAccess:
    """
    Class for accessing the AI API
    """
    def __init__(self):
        self.MAIN_MODEL = _HcAiModel()
        # self.FALLBACK = _GithubAiModel()
        self.PROMPTER = _AiPromptGenerator()
        self.lang_level = None



    def call_summarizer(self, link, short, language_level="middle"):
        self.lang_level = language_level
        if short:
            prompt = self.PROMPTER.generate_short_prompt(link=link, language_level=language_level)
        else:
            prompt = self.PROMPTER.generate_prompt(link=link, language_level=language_level)

        print("prompt = ", prompt)
        try:
            return self.MAIN_MODEL.call_ai(prompt)
        except Exception as e:
            print("Main model failed because of {exception}. Falling back".format(exception=e))

    def chat_completion(self, short, query, link, language_level="middle"):
        if short:
            prompt = self.PROMPTER.generate_short_completion_prompt(query, link, language_level)
        else:
            prompt = self.PROMPTER.generate_completion_prompt(query, link, language_level)

        try:
            return self.MAIN_MODEL.call_ai(prompt)
        except Exception as e:
            print("Main model failed because of {exception}. Falling back".format(exception=e))


class AiChunker:
    def __init__(self):
        self.MAX_CHUNK_SIZE = 5000
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=self.MAX_CHUNK_SIZE,
            chunk_overlap=self.MAX_CHUNK_SIZE * 0.1
        )
        self.ai_access = _HcAiModel()

        self.TOKEN_COUNTER = tiktoken.get_encoding("cl100k_base")

    def split_and_process(self, document):
        chunks = self.text_splitter.split_text(document)

        chunks_processed = []
        for chunk in chunks:
            chunks_processed.append(self.ai_access.call_ai("Please reformat this excerpt to only contain key points. "
                                                           "Denote separate sections with headers. \n ### Excerpt: {excerpt}".format(excerpt=chunk)))

        return chunks_processed

class _AiPromptGenerator:
    """
        Class for prompt generation
    """
    def __init__(self):
        self.prompts = json.load(open("prompts.json", "r"))
        self.SCRAPER = ScraperDatabaseControl()
        self.MODEL_TOKEN_LIMIT = 100000000

    def generate_prompt(self, link, language_level) -> str:
        """
        Generates initial prompt for AI models.
        :param link: The link of the privacy policy to create the prompt for
        :param language_level: The level of complexity that the prompt generator should ask for
        :return: Complete prompt
        """
        policy = vector_db.get_by_link(link).document

        content = self.prompts["language-levels"][language_level]
        content += self.prompts["normal"]["default-prompts"]["default-prompt-head"]
        content += self.prompts["normal"]["default-prompts"]["default-prompt-tail"]

        content = content.format(policy=policy)

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
        self.URL = "https://ai.hackclub.com/chat/completions"
        self.TIMEOUT = Timeout(connect=2, read=50)

    def call_ai(self, prompt, max_retries=3, think=False) -> str:

        headers = {
            'Content-Type': 'application/json'
        }
        if think:
            json_data = {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt,
                    },
                ],
            }
        else:
            json_data = {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt + "  * /no_think *",
                    },
                ],
            }

        print("called with", json_data)


        response = request("post", self.URL, json=json_data, headers=headers, retries=max_retries, timeout=self.TIMEOUT)
        data = response.data
        del response
        print("success")
        return json.loads(data.decode("utf-8"))["choices"][0]["message"]["content"]



