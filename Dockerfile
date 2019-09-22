FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY wall_e/requirements.txt .

RUN apk add --update alpine-sdk libffi-dev

RUN apk add freetype-dev && apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt &&  apk --update add postgresql-client

COPY wall_e .

CMD ["./wait-for-postgres.sh", "db",  "python", "./main.py" ]
