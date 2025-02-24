# Use the official Python image from the Docker Hub
FROM public.ecr.aws/lambda/python:3.8

ARG OPENAI_API_KEY
ARG DEEPSEEK_API_KEY
ARG MONGO_URI
ARG DATABASE_NAME

ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
ENV MONGO_URI=$MONGO_URI
ENV DATABASE_NAME=$DATABASE_NAME

COPY app/ ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
# needed when running locally
#COPY .env .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["main.lambda_handler"]
