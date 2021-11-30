import os

BACKEND_RPC_URL = os.environ.get('BACKEND_RPC_URL', 'https://bsc-dataseed1.defibit.io/')
CACHE_TTL = int(os.environ.get('CACHE_TTL', '3'))
