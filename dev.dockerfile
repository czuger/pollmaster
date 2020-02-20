FROM python:3.7.5-slim

WORKDIR /usr/src/app

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get -y install gcc && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./pollmaster.py" ]
