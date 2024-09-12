import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()


def get_gpt_question(topic):

    iam_token = os.environ["IAM_TOKEN"]

    headers = {
        "Authorization": f"Bearer {iam_token}",
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    data = {
        "modelUri": "gpt://b1g7cjd9omhtvo8u0n4e/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 1, "maxTokens": "2000"},
        "messages": [
            {
                "role": "user",
                "text": f"Придумай вопрос для викторины на тему: {topic} "
                "и четыре варианта ответов. "
                "В ответ отправь только JSON с полями, без других слов и пробелов"
                "{'question': вопрос,'answer_1': ответ 1, "
                "'answer_2': ответ 2, 'answer_3': ответ 3, "
                "'answer_4': ответ 4, "
                "'correct_answer': тут ключ правильного ответа "
                "т.е. answer_1 или answer_2 или answer_3 или answer_4}",
            }
        ],
    }

    data = json.dumps(data)
    resp = requests.post(url, headers=headers, data=data)

    if resp.status_code != 200:
        raise RuntimeError(
            "Invalid response received: code: {}, message: {}".format(
                {resp.status_code}, {resp.text}
            )
        )
    question, answer_1, answer_2, answer_3, answer_4, correct_answer = parse_gpt_response(resp.text)
    question_dict = {
        "question": question,
        "answer_1": answer_1,
        "answer_2": answer_2,
        "answer_3": answer_3,
        "answer_4": answer_4,
        "correct_answer": correct_answer,
    }

    return question_dict


def parse_gpt_response(gpt_text):
    gpt_text = gpt_text.replace("\n    ", "").replace("\n", "").replace("\\", "")
    question = re.search(r"\"question\": \"(.*?)\"", gpt_text).group(1)
    answer_1 = re.search(r"\"answer_1\": \"(.*?)\"", gpt_text).group(1)
    answer_2 = re.search(r"\"answer_2\": \"(.*?)\"", gpt_text).group(1)
    answer_3 = re.search(r"\"answer_3\": \"(.*?)\"", gpt_text).group(1)
    answer_4 = re.search(r"\"answer_4\": \"(.*?)\"", gpt_text).group(1)
    correct_answer = re.search(r"\"correct_answer\": \"(.*?)\"", gpt_text).group(1)
    return question, answer_1, answer_2, answer_3, answer_4, correct_answer
