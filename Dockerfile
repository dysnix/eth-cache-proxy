FROM python:3

ADD requirements.txt /usr/src/app/requirements.txt

WORKDIR /usr/src/app

RUN pip install -r requirements.txt

ADD ./ /usr/src/app/

EXPOSE 8080

CMD ["python", "run.py"]