FROM python:3.10.12-buster

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /usr/local/outlier

WORKDIR /usr/local/outlier
RUN python3 setup.py install

WORKDIR /src
