FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --update alpine-sdk libffi-dev
RUN pip install -U git+https://github.com/Rapptz/discord.py@3f06f247c039a23948e7bb0014ea31db533b4ba2#egg=discord.py[voice]

RUN apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt &&  apk --update add postgresql-client

COPY . .

CMD ["./wait-for-postgres.sh", "db",  "python", "./main.py" ]
#CMD ["python", "./main.py" ]
