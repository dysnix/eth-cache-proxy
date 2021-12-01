FROM python:3.9.9

WORKDIR /usr/src/app
COPY requirements.txt *.py /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
ENV GUNICORN_WORKERS 4

CMD ["gunicorn", "run:eth_cache_proxy", "--bind", "0.0.0.0:8080", "--worker-class", "aiohttp.GunicornWebWorker", "--workers", "${GUNICORN_WORKERS}"]