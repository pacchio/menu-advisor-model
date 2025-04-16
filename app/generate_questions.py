import os
import json

from fetch_menu import MenuFetcher
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional, Literal, Dict, Union, Any
from pydantic import BaseModel, ValidationError

load_dotenv()

OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = "https://api.deepseek.com"
# API_BASE_URL = "https://api.openai.com/v1"
API_MODEL = "deepseek-chat"
# API_MODEL = "gpt-4o-mini"

class Question(BaseModel):
    question: str
    type: Literal["single-selection", "multi-selection", "open-text"]
    possible_answers: Optional[List[str]] = None

class QuestionList(BaseModel):
    questions: List[Question]

def generate_questions(merchant_id: str, menu_id: str, language: str,) -> Dict:
    """
    Generate questions based on the menu using DeepSeek model.
    :param merchant_id: merchant identifier.
    :param menu_id: menu identifier (variant ID).
    :param language: language used for the output.
    :return: list of generated questions.
    """
    # 1. Fetch menu from MongoDB
    menu_fetcher = MenuFetcher()
    menu_data = menu_fetcher.get_menu(merchant_id)

    if not menu_data or len(menu_data) == 0:
        return {"error": "Menu not found"}

    if len(menu_data) == 1 or not menu_id:
        menu_data = menu_data[0]
    else:
        menu_data = next((menu for menu in menu_data if menu['_id'] == menu_id), None)

    # 2. Data cleaning
    cleaned_data = clean_menu_data(menu_data)

    print("\n<< Filtered menu data >>", cleaned_data)

    # 3. Preparation of the prompt
    prompt = create_prompt(cleaned_data, language)

    print("\n<< Prompt >>", prompt)

    # 4. Integration with DeepSeek API
    model_response = call_deepseek_api(prompt)

    print("\n<< Model response >>", model_response)

    # 5. Post-process the generated questions
    return post_process_questions(model_response)

def clean_menu_data(menu_data: Dict) -> Dict:
    """
    Extracts and cleans relevant data from the menu.
    :param menu_data: JSON data of the menu.
    :return: Cleaned data as a dictionary.
    """
    cleaned_data = {
        'dishes': []
    }

    for category in menu_data.get('categories', []):
        for item in category.get('items', []):
            ingredients = [
                ingredient.get('name', '') for ingredient in item.get('ingredients', [])
            ]
            dish = {
                'id': item.get('id'),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'ingredients': ingredients,
                'allergens': item.get('allergens', []),
                'price': item.get('price'),
                'category': category.get('name')  # add the category name
            }
            cleaned_data['dishes'].append(dish)

    return cleaned_data

def create_prompt(cleaned_data: Dict, language: str) -> str:
    """
    Creates a prompt for the DeepSeek model based on the cleaned menu data
    :param cleaned_data
    :param language: language used for the output.
    :return: Prompt as string.
    """
    prompt = "Based on the following list of dishes, generate 3 user questions:\n"

    for dish in cleaned_data['dishes']:
        prompt += f"- {dish['name']}: {dish['description']}\n"
        prompt += f"  Ingredients: {', '.join(dish['ingredients'])}\n"
        prompt += f"  Allergens: {', '.join(dish['allergens'])}\n"
    prompt += (
        "\nCreate 3 questions to help the user choose dishes according to their preferences."
        "\nEach question must include: 'question', 'type' (one of: single-selection (for questions with yes/no answer), multi-selection (for questions with multiple answers allowed), open-text (for questions without pre-defined answers to which the client can respond in an open way)), and if applicable, 'possible_answers'."
        "\nRespond only with JSON (no markdown or explanations) wrapping questions array into 'questions' key."
    )
    prompt += f"\n\nLanguage of the questions and possible answers: {language}\n"

    return prompt

def call_deepseek_api(prompt: str) -> Optional[str]:
    """
    Call DeepSeek API to generate questions.
    :param prompt: Prompt for the model.
    :return: List of generated questions.
    """
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=API_BASE_URL
    )

    try:
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates user questions based on menu data."},
                {"role": "user", "content": prompt},
            ],
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error while making call to the model: {e}")
        return None


def post_process_questions(content: Optional[str]) -> Union[
    Dict[str, str], Dict[str, List[Any]], Dict[str, str], Dict[str, Union[str, Any]]]:
    """
    Cleans and formats the generated questions.
    :param content: generated content.
    :return: Dict containing the list of cleaned question objects under "questions".
    """
    if not content:
        return {"error": "No response from model"}

    try:
        parsed = json.loads(content)
        validated = QuestionList.model_validate(parsed)
        return validated.model_dump()
    except ValidationError as e:
        return {"error": "Schema validation failed", "details": e.errors()}
    except json.JSONDecodeError:
        return {"error": "Malformed JSON in model response"}
