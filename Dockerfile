FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt service.py ./
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "./service.py" ]
