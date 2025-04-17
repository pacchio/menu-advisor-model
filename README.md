# Menu Advisor Model

The **Menu Advisor Model** is an AI-powered recommendation system for a digital menu platform.
<br>This Lambda-based service integrates with MongoDB to analyze menu data and provide personalized dish suggestions using DeepSeek's AI models.

### Key Features:
- 🗂️ **Menu-Centric Design** - Works directly with menu data stored in MongoDB using only a `menu_id`.
- 🤖 **DeepSeek AI Integration** - Leverages DeepSeek's language models for intelligent question generation and recommendations
- ❓ **Smart Question Generation** - Dynamically creates preference questions based on menu ingredients and allergens.
- 🍽️ **Personalized Recommendations** - Suggests dishes matching user preferences and dietary restrictions.
- ☁️ **Cloud-Native** - Serverless architecture with AWS Lambda + API Gateway for scalable, low-maintenance operation.

---

## Table of Contents
1. [How It Works](#how-it-works)
2. [Requirements](#requirements)
3. [Local Development](#local-development)
4. [Deploy](#deploy)
5. [Test Endpoint](#test-endpoint)

---

## How It Works

```mermaid
graph TD
    A[User provides menu_id] --> B[Fetch menu from MongoDB]
    B --> C[LLM generates questions]
    C --> D[User answers]
    D --> E[LLM filters dishes]
    E --> F[Return matches]
 ```

1. Input: Digital menu platform provides a menu_id
2. Data Retrieval: Fetch complete menu details from MongoDB
3. AI Processing:
   - LLM analyzes ingredients/allergens to generate relevant questions
   - LLM processes user responses to filter compatible dishes
4. Output Validation:
   - The generated questions and dish suggestions are validated using Pydantic models to ensure the structure and format adhere to the defined schema.
5. Final Output: Returns JSON with personalized recommendations.

The **Menu Advisor Model** operates in two main steps:

1. **Generate Questions**:
    - The `/generate-questions` endpoint provides a set of questions to the user to gather their preferences (e.g., dietary restrictions, allergies, cuisine preferences).
    - These questions are dynamically generated based on the menu data and user context.

2. **Suggest Dishes**:
    - The `/suggest-dishes` endpoint takes the user's preferences (collected from the questions) and recommends dishes from the menu that match their criteria.
    - The recommendations are filtered based on factors like ingredients, allergens, and user preferences.

---

## Requirements

- Python 3.10+
- MongoDB (Atlas or self-hosted)
- Docker
- DeepSeek API Key
- AWS Account (for deployment)

---

## Local Development

Create your `.env` file in the `dev` folder to configure secrets (you can use the `.env.example` file as a template).

### Run Locally

You can run the Lambda function locally for testing and development.

#### Simulating Lambda Using Docker

This method uses a Docker container to simulate the AWS Lambda environment.

```bash
# Build the Docker image using the dev Dockerfile
docker build . -t menu-advisor-model-lambda -f dev/Dockerfile
pydantic
# Run the Docker image
docker run -p 9000:8080 menu-advisor-model-lambda
```

```bash
# test generate-questions
jq -n \
  --arg path "/generate-questions" \
  '{path: $path, body: ({merchant_id: "5f4d157ed8eef50017ed8836", menu_id: "menu", language: "en"} | tostring)}' | \
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
-H "Content-Type: application/json" \
-d @-

# test suggest-dishes
jq -n \
  --arg path "/suggest-dishes" \
  --argjson preferences "$(cat dev/preferences.json)" \
  '{path: $path, body: ({merchant_id: "5f4d157ed8eef50017ed8836", menu_id: "menu", language: "en", user_preferences: $preferences} | tostring)}' | \
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
-H "Content-Type: application/json" \
-d @-
```

## Deploy

The **Menu Advisor Model** is deployed to **AWS Lambda** and exposed via **AWS API Gateway**, enabling RESTful API access. The deployment is automated using GitHub Actions on every push to the `main` branch.

---

### Key Components & Advantages

1. **AWS Lambda**:
   - **Serverless**: No infrastructure management, scales automatically.
   - **Cost-Efficient**: Pay-per-execution pricing model.

2. **AWS API Gateway**:
   - **Simplified API Management**: Routes requests to Lambda, handles authentication, rate limiting, and CORS.
   - **Scalability**: Automatically scales with traffic spikes.
   - **Security**: Built-in request validation and integration with AWS security services.

3. **Amazon ECR**:
   - Stores the Docker image used by Lambda for consistent deployments.

---

### Deployment Steps

1. **Checkout Code**: Fetch the latest code from the `main` branch.
2. **Configure AWS Credentials**: Securely authenticate with AWS using GitHub Secrets.
3. **Build & Push Docker Image**:
   - Build the Docker image with environment variables (API keys, database URI).
   - Push the image to Amazon ECR.
4. **Update Lambda**:
   - Deploy the new image to AWS Lambda.
   - Configure environment variables for the Lambda function.

## Test Endpoint

You can test the endpoints using the `.http` files into `api` folder.
<br />Have a look at this [README.md](api/README.md) file for more info.

## 🚀 Demo

To see how the **Menu Advisor Model** works in practice, check out the client project: [Menu Advisor Client](https://github.com/pacchio/menu-advisor-client). 🖥️✨
<br>This repository demonstrates the integration of the backend service with a user-facing application, showcasing the end-to-end functionality of menu-based recommendations. 
