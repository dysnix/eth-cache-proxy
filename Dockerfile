FROM python:3.9.9

ADD requirements.txt /usr/src/app/requirements.txt

WORKDIR /usr/src/app

RUN pip install -r requirements.txt

ADD ./ /usr/src/app/

EXPOSE 8080
ENV GUNICORN_WORKERS 4

CMD ["gunicorn", "run:eth_cache_proxy", "--bind", "0.0.0.0:8080", "--worker-class", "aiohttp.GunicornWebWorker", "--workers", "${GUNICORN_WORKERS}"]