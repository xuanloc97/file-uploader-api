FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get install -y apt-utils 

WORKDIR /src

ENV FLASK_APP=src/main.py
ENV PYTHONPATH "${PYTHONPATH}:/src"

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


COPY . .
RUN ls -la .

EXPOSE 5000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
