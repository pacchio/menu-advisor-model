import os
import json

from fetch_menu import MenuFetcher
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, field_validator, ValidationError

load_dotenv()

OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = "https://api.deepseek.com"
# API_BASE_URL = "https://api.openai.com/v1"
API_MODEL = "deepseek-chat"
# API_MODEL = "gpt-4o-mini"

class DishSuggestion(BaseModel):
    suggested_dishes: List[str]

    @field_validator('suggested_dishes')
    @classmethod
    def truncate_and_validate(cls, v: List[str]) -> List[str]:
        if len(v) < 1:
            raise ValueError("You must suggest at least one dish.")
        return v[:5]

def suggest_dishes(merchant_id: str, menu_id: str, user_preferences: Dict) -> Dict:
    """
    Suggest dishes based on menu and user preferences using DeepSeek API.
    :param merchant_id: Merchant ID.
    :param menu_id: Menu (variant) ID.
    :param user_preferences: User preferences (questions and answers).
    :return: Full dish objects matching suggestions.
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
    prompt = create_prompt(cleaned_data, user_preferences)

    print("\n<< Prompt >>", prompt)

    # 4. Integration with DeepSeek API
    model_response = call_deepseek_api(prompt)

    print("\n<< Model response >>", model_response)

    # 5. Post-process the suggested dishes
    return post_process_suggestions(menu_data, model_response)


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

def create_prompt(cleaned_data: Dict, user_preferences: Dict) -> str:
    """
    Creates a prompt for the DeepSeek model based on the cleaned menu data
    :param cleaned_data
    :param user_preferences: User preferences (questions and answers).
    :return: Prompt as string.
    """
    prompt = "Based on the following menu and following user preferences:\n\n"

    prompt += "Menu:\n"
    for dish in cleaned_data['dishes']:
        prompt += f"- Name: {dish['name']}"
        prompt += f"  Description: {dish['description']}\n"
        prompt += f"  Ingredients: {', '.join(dish['ingredients'])}\n"
        prompt += f"  Allergens: {', '.join(dish['allergens'])}\n"

    prompt += "\nUser preferences:\n"
    for preference in user_preferences.get('preferences', []):
        prompt += f"- Question: {preference['question']}\n"
        prompt += f"  Answer: {preference['answer']}\n"

    prompt += (
        "\nSuggest up to 5 dish names that best suit the user's preferences."
        "\nThe suggestions are an array of string in which the string is the name of the dish."
        "\nRespond only with JSON (no markdown or explanations) wrapping suggestions array into 'suggested_dishes' key."
    )

    return prompt

def call_deepseek_api(prompt: str) -> Optional[str]:
    """
    Call DeepSeek API to generate suggestions.
    :param prompt: Prompt for the model.
    :return: List of suggested dishes.
    """
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=API_BASE_URL
    )

    try:
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant who suggests dishes based on a menu and the user's preferences."},
                {"role": "user", "content": prompt},
            ],
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error while making call to the model: {e}")
        return None

def post_process_suggestions(menu_data: Dict, content: Optional[str]) -> Union[
    Union[Dict[str, str], List[Any], Dict[str, Union[str, Any]]], Any]:
    """
    Filter suggested dishes from the original menu.
    :param menu_data: Menu data (JSON structure).
    :param content: String with the names of the suggested dishes (formatted with newlines).
    :return: List of complete dishes (with all original fields).
    """
    suggested_dishes = []

    if not content:
        return suggested_dishes

    try:
        parsed = json.loads(content)
        validated = DishSuggestion.model_validate(parsed)
        suggested_dish_names = validated.model_dump()['suggested_dishes']

        for category in menu_data.get('categories', []):
            for item in category.get('items', []):
                if item.get('name') in suggested_dish_names:
                    ingredients = []
                    for ingredient in item.get('ingredients', []):
                        ingredients.append({
                            'id': str(ingredient.get('_id')),
                            'name': ingredient.get('name')
                        })

                    # Add the dish with all the original fields
                    suggested_dishes.append({
                        'id': str(item.get('_id')),
                        'name': item.get('name'),
                        'description': item.get('description'),
                        'ingredients': ingredients,
                        'allergens': item.get('allergens', []),
                        'price': item.get('price'),
                        'categoryId': str(category.get('_id')),
                        'categoryName': category.get('name')
                    })
        return { "suggested_dishes": suggested_dishes }
    except ValidationError as e:
        return {"error": "Schema validation failed", "details": str(e)}
    except json.JSONDecodeError:
        return {"error": "Malformed JSON in model response"}
