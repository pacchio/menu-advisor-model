# Menu Advisor Model
Python Lambda function to provide a menu suggestion based on the user's preferences.

## Requirements

- Python 3
- Docker

## Local development

Create your `.env` file into `dev` folder to configure secrets (you can use the .env.example as a template)

### Run locally
You can run the lambda locally.

#### Simulating Lambda using Docker
This way will use a docker container to run the application.<br>

```bash
# build the docker image with dev Dockerfile
docker build . -t menu-advisor-model-lambda -f dev/Dockerfile

# run the docker image
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
- The `.github/workflows/deploy.yml` file contains the configuration of the action
- It creates the docker image using the `Dockerfile`
- Push the docker image to the **ECR** (Elastic Container Registry)
- Deploy the application to AWS Lambda

## Test Endpoint

api gateway endpoint: https://5bhznb8wh0.execute-api.eu-south-1.amazonaws.com/production

```bash
# test generate-questions
curl -X POST "https://5bhznb8wh0.execute-api.eu-south-1.amazonaws.com/production/generate-questions" \
-H "Content-Type: application/json" \
-d '{"merchant_id": "5f4d157ed8eef50017ed8836", "menu_id": "menu"}'

# test suggest-dishes
curl -X POST "https://5bhznb8wh0.execute-api.eu-south-1.amazonaws.com/production/suggest-dishes" \
-H "Content-Type: application/json" \
-d "$(jq -n --argjson preferences "$(cat data/preferences.json)" '{merchant_id: "5f4d157ed8eef50017ed8836", menu_id: "menu", user_preferences: $preferences}')"
```
