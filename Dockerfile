FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --update alpine-sdk libffi-dev
RUN pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]

RUN apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt &&  apk --update add postgresql-client

COPY . .

CMD ["./wait-for-postgres.sh", "db",  "python", "./main.py" ]
#CMD ["python", "./main.py" ]
