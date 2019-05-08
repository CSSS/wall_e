FROM python:3.5.5-alpine

WORKDIR /usr/src/app

COPY test-requirements.txt ./

COPY main.py ./

COPY pytest.ini ./

COPY setup.cfg ./

COPY commands_to_load ./commands_to_load

COPY helper_files ./helper_files

RUN pip install --no-cache-dir -r test-requirements.txt

RUN py.test

RUN pip uninstall -y -r test-requirements.txt

COPY requirements.txt ./

RUN apk add --update alpine-sdk libffi-dev

RUN apk add freetype-dev && apk add postgresql-dev && pip install --no-cache-dir -r requirements.txt &&  apk --update add postgresql-client 

#COPY . .

CMD ["./wait-for-postgres.sh", "db",  "python", "./main.py" ]
