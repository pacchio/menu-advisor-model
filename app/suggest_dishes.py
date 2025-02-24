import os
from fetch_menu import MenuFetcher
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = "https://api.deepseek.com"
# API_BASE_URL = "https://api.openai.com/v1"
API_MODEL = "deepseek-chat"
# API_MODEL = "gpt-4o-mini"

def suggest_dishes(merchant_id: str, menu_id: str, user_preferences: Dict) -> Dict:
    """
    Suggerisce piatti basati sul menu e le preferenze dell'utente utilizzando l'API di DeepSeek.
    :param merchant_id: ID del merchant.
    :param menu_id: ID del menu (variant ID).
    :param user_preferences: Preferenze dell'utente (domande e risposte).
    :return: Lista di piatti suggeriti (con tutti i campi originali).
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

    # 3. Pulizia dei dati del menu
    cleaned_data = clean_menu_data(menu_data)

    print("========== here the filtered menu data ===========", cleaned_data)

    # 3. Preparazione del prompt per DeepSeek
    prompt = create_prompt(cleaned_data, user_preferences)

    print("========== here the prompt ===========", prompt)

    # 4. Integrazione con DeepSeek API
    suggested_dish_names = call_deepseek_api(prompt)

    # 5. Filtra i piatti suggeriti dal menu originale
    suggested_dishes = filter_suggested_dishes(cleaned_data, suggested_dish_names)

    return {
        'suggested_dishes': suggested_dishes
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

def create_prompt(cleaned_data: Dict, user_preferences: Dict) -> str:
    """
    Crea un prompt strutturato per DeepSeek.
    :param cleaned_data: Dati puliti del menu.
    :param user_preferences: Preferenze dell'utente (domande e risposte).
    :return: Prompt come stringa.
    """
    prompt = "Suggerisci piatti basati sul seguente menu e le preferenze dell'utente:\n\n"

    # Aggiungi i dettagli del menu
    prompt += "Menu:\n"
    for dish in cleaned_data['dishes']:
        prompt += f"- {dish['name']}: {dish['description']}\n"
        prompt += f"  Ingredienti: {', '.join(map(str, dish['ingredients']))}\n"
        prompt += f"  Allergeni: {', '.join(map(str, dish['allergens']))}\n"

    # Aggiungi le preferenze dell'utente
    prompt += "\nPreferenze dell'utente:\n"
    for preference in user_preferences.get('preferences', []):
        prompt += f"- Domanda: {preference['question']}\n"
        prompt += f"  Risposta: {preference['answer']}\n"

    prompt += "\nSuggerisci i nomi dei piatti più adatti alle preferenze dell'utente. Restituisci solo i nomi dei piatti, uno per riga."

    return prompt

def call_deepseek_api(prompt: str) -> List[str]:
    """
    Chiama l'API di DeepSeek per generare suggerimenti.
    :param prompt: Prompt da inviare a DeepSeek.
    :return: Lista di nomi di piatti suggeriti.
    """
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=API_BASE_URL
    )

    try:
        # Invia la richiesta a DeepSeek
        response = client.chat.completions.create(
            model="deepseek-chat",  # Modello di DeepSeek
            messages=[
                {"role": "system", "content": "Sei un assistente utile che suggerisce piatti basati su un menu e le preferenze dell'utente."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        # Estrai il testo generato dalla risposta
        generated_text = response.choices[0].message.content

        # Estrai i nomi dei piatti suggeriti dal testo generato
        suggested_dish_names = [dish.strip() for dish in generated_text.split('\n') if dish.strip()]
        return suggested_dish_names

    except Exception as e:
        print(f"Errore durante la chiamata a DeepSeek API: {e}")
        return []

def filter_suggested_dishes(menu_data: Dict, suggested_dish_names: List[str]) -> List[Dict]:
    """
    Filtra i piatti suggeriti dal menu originale.
    :param menu_data: Dati del menu (struttura JSON).
    :param suggested_dish_names: Lista di nomi di piatti suggeriti.
    :return: Lista di piatti completi (con tutti i campi originali).
    """
    suggested_dishes = []

    for category in menu_data.get('categories', []):
        for item in category.get('items', []):
            if item.get('name') in suggested_dish_names:
                # Aggiungi il piatto con tutti i campi originali
                suggested_dishes.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'description': item.get('description'),
                    'ingredients': item.get('ingredients', []),
                    'allergens': item.get('allergens', []),
                    'price': item.get('price'),
                    'categoryId': category.get('id'),
                    'categoryName': category.get('name')
                })

    return suggested_dishes
