FROM python:3.10

WORKDIR /usr/src/

RUN git clone https://github.com/AnnoyingRain5/Victini-Guard app

WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

RUN touch .env

CMD git pull; pip install --no-cache-dir -r requirements.txt; python3 ./bot.py