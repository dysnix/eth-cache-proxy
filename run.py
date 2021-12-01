import ujson
import logging
import hashlib
import aiohttp
import settings
from aiohttp import web
from aiocache import cached, Cache
from aiohttp.hdrs import ACCEPT
from aiocache.serializers import JsonSerializer
from aioprometheus import REGISTRY, Summary, timer
from aioprometheus.renderer import render

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary("eth_cache_request_seconds", "Time spent request processing request")
PROXY_TIME = Summary("eth_cache_proxy_seconds", "Time spent proxy processing request")
HASH_TIME = Summary("eth_cache_hash_seconds", "Time spent hash request payload")


@timer(HASH_TIME)
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


def build_key(f, data, session):
    k = "{}_{}".format(f.__name__, get_hash(data))
    logging.debug('key: {}'.format(k))
    return k


@timer(PROXY_TIME)
async def rpc_request(data, session):
    async with session.post(settings.BACKEND_RPC_URL, json=data) as resp:
        res = await resp.json()
        logging.debug('Result: {}'.format(str(res)))
        return res


# @cached(key_builder=build_key, serializer=JsonSerializer(), ttl=settings.CACHE_TTL, cache=Cache.REDIS,
#         endpoint=settings.REDIS_ENDPOINT, port=settings.REDIS_PORT, namespace="main")
@cached(key_builder=build_key, serializer=JsonSerializer(), ttl=settings.CACHE_TTL)
async def cached_rpc_request(data, session):
    logging.debug('Request: {}'.format(str(data)))
    return await rpc_request(data, session)


@timer(REQUEST_TIME)
async def handle(request):
    session = request.app['PERSISTENT_SESSION']
    try:
        data = await request.json()
    except:
        raise aiohttp.web.HTTPBadRequest()

    if type(data) is dict:
        response = await cached_rpc_request(data=data, session=session)
        try:
            response['id'] = data['id']
        except:
            logging.error('Error to set response ID')
    elif type(data) is list:
        # Don't cache bulk requests
        response = await rpc_request(data=data, session=session)
    else:
        raise aiohttp.web.HTTPInternalServerError()

    return web.json_response(response)


async def handle_metrics(request):
    content, http_headers = render(REGISTRY, request.headers.getall(ACCEPT, []))
    return web.Response(body=content, headers=http_headers)


async def healthz(request):
    return web.Response(body="OK")


async def persistent_session(app):
    app['PERSISTENT_SESSION'] = session = aiohttp.ClientSession()
    yield
    await session.close()


async def eth_cache_proxy():
    app = web.Application()
    logging.basicConfig(level=settings.LOG_LEVEL)
    app.cleanup_ctx.append(persistent_session)

    app.router.add_post('/{tail:.*}', handle)

    app.router.add_get('/metrics', handle_metrics)
    app.router.add_get("/healthz", healthz)

    return app


if __name__ == "__main__":
    web.run_app(eth_cache_proxy())
