FROM public.ecr.aws/lambda/python:3.8

COPY app/ ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
COPY dev/.env .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["main.lambda_handler"]
