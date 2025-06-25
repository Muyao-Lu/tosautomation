from openai import OpenAI
import json, requests, os
from scraper import *
from vector_db import vector_db


class AiAccess:
    """
    Class for accessing the AI API
    """
    def __init__(self):
        self.MAIN_MODEL = _HcAiModel()
        self.FALLBACK = _GithubAiModel()
        self.PROMPTER = _AiPromptGenerator()
        self.lang_level = None

    def call_summarizer(self, short, policy, language_level="middle"):
        self.lang_level = language_level
        if short:
            prompt = self.PROMPTER.generate_short_prompt(policy=policy, language_level=language_level)
        else:
            prompt = self.PROMPTER.generate_prompt(policy=policy, language_level=language_level)

        try:
            return self.MAIN_MODEL.call_ai(prompt)
        except:
            print("Main model failed. Falling back")
            try:
                return self.FALLBACK.call_ai(prompt)
            except:
                return "Something went wrong with the AI model(s). If you are a user, check your connection and then try again. If you are an administrator, check the logs"

    def chat_completion(self, query, link):
        prompt = self.PROMPTER.generate_completion_prompt(query, link)

        try:
            return self.MAIN_MODEL.call_ai(prompt)
        except:
            print("Main model failed. Falling back")
            try:
                return self.FALLBACK.call_ai(prompt)
            except:
                return "Something went wrong with the AI model(s). If you are a user, check your connection and then try again. If you are an administrator, check the logs"



class _AiPromptGenerator:
    """
        Class for prompt generation
    """
    def __init__(self):
        self.prompts = json.load(open("prompts.json", "r"))

    def generate_prompt(self, policy, language_level) -> str:
        """
        Generates initial prompt for AI models.
        :param policy: The privacy policy to create the prompt for
        :param language_level: The level of complexity that the prompt generator should ask for
        :return: Complete prompt
        """
        content = self.prompts["normal"]["default-prompts"]["default-prompt-head"]
        content += self.prompts["language-levels"][language_level]
        content += self.prompts["normal"]["default-prompts"]["default-prompt-middle"]
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
        content = self.prompts["chat-comp"]["chat-comp-head"]
        content += self.prompts["language-levels"][language_level]
        content += self.prompts["chat-comp"]["chat-comp-tail"]
        closest_vector = vector_db.get_closest_neighbor(link=link, query=query)
        content = content.format(link=link, question=query, excerpt=closest_vector)

        return content


    def generate_short_prompt(self, policy, language_level="middle") -> str:
        """
            Generates prompt for short summaries of the privacy policy.
            :param policy: Privacy policy to generate prompt for
            :param language_level: The level of complexity that the prompt generator should ask for
            :return: Complete prompt for short privacy policy/tos simplification
        """
        prompt_segment = self.prompts["short"]
        content = prompt_segment["short-head"]
        content += self.prompts["language-levels"][language_level]
        content += prompt_segment["short-tail"]
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
    def call_ai(self, prompt) -> str:
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

        return response.json()["choices"][0]["message"]["content"]

