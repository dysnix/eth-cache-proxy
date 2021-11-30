import ujson
import logging
import hashlib
import aiohttp
import settings
from aiohttp import web
from aiocache import cached, Cache
from aiohttp.hdrs import ACCEPT
from aiocache.serializers import JsonSerializer
from aioprometheus import REGISTRY, Counter
from aioprometheus.renderer import render


def get_hash(data_orig):
    if type(data_orig) is dict:
        data = dict(sorted(data_orig.copy().items()))
        try:
            del data['id']
        except:
            logging.error('No id present in payload')
            pass
    elif type(data_orig) is list:
        data = data_orig
    else:
        logging.error('Bad payload: {}'.format(str(data_orig)))
        raise aiohttp.web.HTTPInternalServerError()

    hash_object = hashlib.sha1(ujson.dumps(data).encode('utf8'))

    return hash_object.hexdigest()


def build_key(f, data):
    k = "{}_{}".format(f.__name__, get_hash(data))
    logging.debug('key: {}'.format(k))
    return k


@cached(key_builder=build_key, serializer=JsonSerializer(), ttl=settings.CACHE_TTL, cache=Cache.REDIS,
        endpoint=settings.REDIS_ENDPOINT, port=settings.REDIS_PORT, namespace="main")
async def rpc_request(data):
    async with aiohttp.ClientSession() as session:
        async with session.post(settings.BACKEND_RPC_URL, json=data) as resp:
            res = await resp.json()
            logging.debug('Result: {}'.format(str(res)))
            app.requests_counter.inc({"type": "proxied"})
            return res


async def handle(request):
    try:
        data = await request.json()
    except:
        raise aiohttp.web.HTTPBadRequest()

    logging.debug('Request: {}'.format(str(data)))
    app.requests_counter.inc({"type": "total"})

    return web.json_response(await rpc_request(data=data))


async def handle_metrics(request):
    content, http_headers = render(REGISTRY, request.headers.getall(ACCEPT, []))
    return web.Response(body=content, headers=http_headers)


if __name__ == "__main__":
    app = web.Application()

    app.requests_counter = Counter("requests_counter", "Total requests")

    app.router.add_route('POST', '/{tail:.*}', handle)
    app.router.add_route('GET', '/metrics', handle_metrics)

    web.run_app(app)
