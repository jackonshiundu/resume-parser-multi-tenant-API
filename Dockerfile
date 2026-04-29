FROM python:3.9-alpine3.13
LABEL maintainer="echesajackon.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

ARG DEV=false

RUN apk add --no-cache postgresql-client && \
    apk add --no-cache --virtual .tmp-build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        python3-dev \
        postgresql-dev && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        pip install -r /tmp/requirements.dev.txt; \
    fi && \
    apk del .tmp-build-deps && \
    adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web /vol/media/resumes && \
    chown -R django-user:django-user /vol

COPY ./app /app

RUN chown -R django-user:django-user /app

USER django-user

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --no-input && gunicorn --bind 0.0.0.0:8000 app.wsgi:application"]