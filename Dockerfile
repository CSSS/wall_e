FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY test-requirements.txt ./

COPY main.py ./

COPY commands_to_load ./

COPY helper_files ./

RUN pip install --no-cache-dir -r test-requirements.txt

RUN ls -l

RUN ls -l commands_to_load

RUN ls -l helper_file

RUN py.test

RUN pip uninstall -r test-requirements.txt

COPY requirements.txt ./

RUN apk add --update alpine-sdk libffi-dev

RUN apk add freetype-dev && apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt &&  apk --update add postgresql-client 

#COPY . .

CMD ["./wait-for-postgres.sh", "db",  "python", "./main.py" ]
