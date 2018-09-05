FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt && apk add build-base

COPY . .

CMD [ "python", "./main.py" ]
