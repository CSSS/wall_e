FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --update alpine-sdk && apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
