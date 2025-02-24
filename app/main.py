import json
from generate_questions import generate_questions
from suggest_dishes import suggest_dishes

def lambda_handler(event, context):
    try:
        # Estrai il corpo della richiesta
        body = json.loads(event.get('body', '{}'))
        merchant_id = body.get('merchant_id', {})
        menu_id = body.get('menu_id', {})
        user_preferences = body.get('user_preferences', {})

        # Determina l'azione in base al percorso della richiesta
        if event.get('path') == '/generate-questions':
            response = generate_questions(merchant_id, menu_id)
        elif event.get('path') == '/suggest-dishes':
            response = suggest_dishes(merchant_id, menu_id, user_preferences)
        else:
            response = {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid path'})
            }

        # Restituisci la risposta
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    except Exception as e:
        # Gestisci eventuali errori
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
