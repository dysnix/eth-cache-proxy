import os

BACKEND_RPC_URL = os.environ.get('BACKEND_RPC_URL', 'https://bsc-dataseed1.defibit.io/')
CACHE_TTL = int(os.environ.get('CACHE_TTL', '3'))

REDIS_ENDPOINT = os.environ.get('REDIS_ENDPOINT', '127.0.0.1')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
