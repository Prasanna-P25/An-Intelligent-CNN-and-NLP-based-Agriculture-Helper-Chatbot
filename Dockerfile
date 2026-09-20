FROM python:3.7.3-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade "pip==23.3.2" \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input

CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:$PORT Chatbot.wsgi:application"]