import json
from generate_questions import generate_questions
from suggest_dishes import suggest_dishes

def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",  # or replace with "http://localhost:3000" or your frontend domain
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }
    try:
        # Handle preflight request
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"message": "CORS preflight"})
            }

        body = json.loads(event.get('body', '{}'))
        merchant_id = body.get('merchant_id', {})
        menu_id = body.get('menu_id', {})
        language = body.get('language', {})
        user_preferences = body.get('user_preferences', {})

        # Determina l'azione in base al percorso della richiesta
        if event.get('path') == '/generate-questions':
            response = generate_questions(merchant_id, menu_id, language)
        elif event.get('path') == '/suggest-dishes':
            response = suggest_dishes(merchant_id, menu_id, language, user_preferences)
        else:
            response = {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Invalid path'})
            }

        # Check if the response contains an error field
        if 'error' in response:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps(response)
            }

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response)
        }

    except Exception as e:
        # Gestisci eventuali errori
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }
