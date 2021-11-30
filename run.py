import json
import logging
import hashlib
import aiohttp
import settings
from aiohttp import web
from aiocache import cached
from aiocache.serializers import JsonSerializer


def get_hash(data_orig):
    data = dict(sorted(data_orig.copy().items()))

    try:
        del data['id']
    except:
        logging.error('No id present in payload')
        pass

    hash_object = hashlib.sha1(json.dumps(data).encode('utf8'))

    return hash_object.hexdigest()


def build_key(f, data):
    k = "{}_{}".format(f.__name__, get_hash(data))
    logging.debug('key: {}'.format(k))
    return k


@cached(key_builder=build_key, serializer=JsonSerializer(), ttl=settings.CACHE_TTL)
async def rpc_request(data):
    async with aiohttp.ClientSession() as session:
        async with session.post(settings.BACKEND_RPC_URL, json=data) as resp:
            res = await resp.json()
            logging.debug('Result: {}'.format(str(res)))
            return res


async def handle(request):
    try:
        data = await request.json()
    except:
        raise aiohttp.web.HTTPBadRequest()

    logging.debug('Request: {}'.format(str(data)))
    return web.json_response(await rpc_request(data=data))


if __name__ == "__main__":
    app = web.Application()
    app.router.add_route('POST', '/{tail:.*}', handle)

    web.run_app(app)
