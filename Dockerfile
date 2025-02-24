# Usa l'immagine ufficiale di AWS Lambda per Python
FROM public.ecr.aws/lambda/python:3.8

# Copia i file del progetto
COPY app/ ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
COPY .env .

# Installa le dipendenze
RUN pip install -r requirements.txt

# Imposta il comando di default per la Lambda
CMD ["main.lambda_handler"]
