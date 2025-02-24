# Menu Advisor Model
Python Lambda function to provide a menu suggestion based on the user's preferences.

## Requirements

- Python 3
- Docker

## Local development

```bash
# install dependencies
pip install -r requirements.txt
```

Then create your `.env` file to configure database properties (you can use the .env.example as a template)

### Run locally
You can run the lambda locally:

#### Simple running script (TO DO)
```bash
# test generate-questions

# test suggest-dishes
```

#### Simulating Lambda using Docker
This way will use a docker container to run the application.<br>
The configuration is taken from the env variables into `.env` file.

```bash
# build the docker image
docker build -t menu-advisor-model-lambda .

# build the docker image
docker run -p 9000:8080 menu-advisor-model-lambda
```

```bash
# test generate-questions
jq -n \
  --arg path "/generate-questions" \
  '{path: $path, body: ({merchant_id: "5f4d157ed8eef50017ed8836", menu_id: "menu"} | tostring)}' | \
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
-H "Content-Type: application/json" \
-d @-

# test suggest-dishes
jq -n \
  --arg path "/suggest-dishes" \
  --argjson preferences "$(cat data/preferences.json)" \
  '{path: $path, body: ({merchant_id: "5f4d157ed8eef50017ed8836", menu_id: "menu", user_preferences: $preferences} | tostring)}' | \
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
-H "Content-Type: application/json" \
-d @-
```

## Deploy

The application is deployed to AWS Lambda using GitHub Actions.

- When a push is made to the `main` branch, the **GitHub Action** is triggered
    - the `.github/workflows/deploy.yml` file contains the configuration of the action
    - it creates the docker image using the `Dockerfile`
    - push the docker image to the **ECR** (Elastic Container Registry)
    - deploy the application to AWS Lambda

## Test Endpoint

