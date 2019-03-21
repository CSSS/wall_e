FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --update alpine-sdk libffi-dev

RUN apk add freetype-dev && apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt &&  apk --update add postgresql-client 

COPY . .

CMD ["./wait-for-postgres.sh", "db",  "python", "./main.py" ]