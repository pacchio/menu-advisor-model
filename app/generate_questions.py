import os
import json
from fetch_menu import MenuFetcher
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = "https://api.deepseek.com"
# API_BASE_URL = "https://api.openai.com/v1"
API_MODEL = "deepseek-chat"
# API_MODEL = "gpt-4o-mini"

def generate_questions(merchant_id: str, menu_id: str,) -> Dict:
    """
    Genera domande basate sul menu utilizzando l'API di DeepSeek.
    :param merchant_id: ID del merchant.
    :param menu_id: ID del menu (variant ID).
    :return: Lista di domande generate.
    """
    # 1. Recupera il menu da MongoDB
    menu_fetcher = MenuFetcher()
    menu_data = menu_fetcher.get_menu(merchant_id)

    if not menu_data or len(menu_data) == 0:
        return {"error": "Menu non trovato"}

    if len(menu_data) == 1 or not menu_id:
        menu_data = menu_data[0]
    else:
        menu_data = next((menu for menu in menu_data if menu['_id'] == menu_id), None)

    # 1. Pulizia dei dati
    cleaned_data = clean_menu_data(menu_data)

    print("\n<< Filtered menu data >>", cleaned_data)

    # 2. Preparazione del prompt per DeepSeek
    prompt = create_prompt(cleaned_data)

    print("\n<< Prompt >>", prompt)

    # 3. Integrazione con DeepSeek API
    content = call_deepseek_api(prompt)

    print("\n<< Content >>", content)

    # 4. Post-processing delle domande
    questions = post_process_questions(content)

    return {
        'questions': questions
    }

def clean_menu_data(menu_data: Dict) -> Dict:
    """
    Estrae e pulisce i dati rilevanti dal menu.
    :param menu_data: Dati del menu (struttura JSON).
    :return: Dati puliti (dict).
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
                'category': category.get('name')  # Aggiungi la categoria
            }
            cleaned_data['dishes'].append(dish)

    return cleaned_data

def create_prompt(cleaned_data: Dict) -> str:
    """
    Crea un prompt strutturato per DeepSeek.
    :param cleaned_data: Dati puliti del menu.
    :return: Prompt come stringa.
    """
    prompt = "Genera domande per l'utente basate sui seguenti piatti:\n"

    for dish in cleaned_data['dishes']:
        prompt += f"- {dish['name']}: {dish['description']}\n"
        prompt += f"  Ingredienti: {', '.join(map(str, dish['ingredients']))}\n"
        prompt += f"  Allergeni: {', '.join(map(str, dish['allergens']))}\n"

    prompt += "\nCrea 3 domande che aiutino l'utente a scegliere i piatti più adatti alle sue preferenze."
    prompt += "\nSe le domande hanno risposte specifiche, includi le risposte possibili e torna quindi un dato strutturato (es: JSON list con 'question' e 'possible_answers' -> [{question: ‘’, possible_answers: []}])."
    prompt += "\nSe alcuni piatti hanno allergeni specificati, includi nelle domande una domanda sulle allergie, altrimenti no."
    prompt += "\nRestituisci solo il json con le domande."

    return prompt

def call_deepseek_api(prompt: str) -> Optional[str]:
    """
    Chiama l'API di DeepSeek per generare domande.
    :param prompt: Prompt da inviare a DeepSeek.
    :return: Lista di domande generate.
    """
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=API_BASE_URL
    )

    try:
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": "Sei un assistente utile che genera domande basate su un menu."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        content = response.choices[0].message.content

        return content

    except Exception as e:
        print(f"Errore durante la chiamata a DeepSeek API: {e}")
        return None


def post_process_questions(content: Optional[str]) -> List[Dict[str, List[str]]]:
    """
    Cleans and formats the generated questions.
    :param content: generated content.
    :return: List of cleaned question objects.
    """
    if not content:
        return []

    try:
        # Remove the ```json and ``` markers if they exist
        if content.strip().startswith("```json") and content.strip().endswith("```"):
            content = content.strip()[7:-3].strip()  # Remove ```json and ```

        # Parse the JSON content
        questions = json.loads(content)
        return questions
    except json.JSONDecodeError:
        print("Error parsing JSON content")
        return []
