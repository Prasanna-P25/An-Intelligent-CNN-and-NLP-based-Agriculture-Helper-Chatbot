FROM python:3.7.17-slim-bullseye

RUN sed -i '/bullseye-security/d' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y libglib2.0-0 libsm6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade "pip==23.3.2" \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input

CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:$PORT Chatbot.wsgi:application"]