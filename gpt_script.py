import json
import os
import re
from typing import Dict, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()


def get_gpt_question(topic: str) -> Dict[str, str] | None:

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
                "{'question': 'вопрос','1': 'ответ 1', "
                "'2': 'ответ 2', '3': 'ответ 3', "
                "'4': 'ответ 4', "
                "'correct_answer': номер правильного ответа}",
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
    if parse_gpt_response(resp.text):
        question, answer_1, answer_2, answer_3, answer_4, correct_answer = parse_gpt_response(
            resp.text
        )

        question_dict = {
            "question": question,
            "1": answer_1,
            "2": answer_2,
            "3": answer_3,
            "4": answer_4,
            "correct_answer": correct_answer,
        }

        return question_dict
    return


def parse_gpt_response(gpt_text: str) -> Tuple[str, str, str, str, str, str] | None:

    # gpt_text = gpt_text.replace("\n    ", "").replace("\n", "").replace("\\", "")

    question = re.search(r".*['\"]\\?question\\?['\"]?:\s*\\?['\"]?(.+?)\\?['\"]", gpt_text)
    answer_1 = re.search(r".*['\"]\\?1\\?['\"]?:\s*\\?['\"]?(.+?)\\?['\"]", gpt_text)
    answer_2 = re.search(r".*['\"]\\?2\\?['\"]?:\s*\\?['\"]?(.+?)\\?['\"]", gpt_text)
    answer_3 = re.search(r".*['\"]\\?3\\?['\"]?:\s*\\?['\"]?(.+?)\\?['\"]", gpt_text)
    answer_4 = re.search(r".*['\"]\\?4\\?['\"]?:\s*\\?['\"]?(.+?)\\?['\"]", gpt_text)
    correct_answer = re.search(r".*['\"]\\?correct_answer\\?['\"]?:\s*\\?['\"]?([1-4])", gpt_text)

    if all([question, answer_1, answer_2, answer_3, answer_4, correct_answer]):
        question = question.group(1)
        answer_1 = answer_1.group(1)
        answer_2 = answer_2.group(1)
        answer_3 = answer_3.group(1)
        answer_4 = answer_4.group(1)
        correct_answer = correct_answer.group(1)

        return question, answer_1, answer_2, answer_3, answer_4, correct_answer

    print(gpt_text)
    return
