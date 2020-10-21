#!/usr/bin/env python3


# +
# import(s)
# -
import os
import hashlib
import logging
import sys


# +
# code base
# -
BASE = '/var/www/disparu'
KEY = hashlib.sha256(BASE.encode('utf-8')).hexdigest()
logging.basicConfig(stream=sys.stderr)


# +
# path(s)
# -
os.environ["PYTHONPATH"] = f'{BASE}:{BASE}/dsrc'
sys.path.insert(0, f'{BASE}')
sys.path.append(f'{BASE}/dsrc')


# +
# print
# -
print(f'DISPARU> Python Version: {sys.version}')
print(f'DISPARU> Python Info: {sys.version_info}')
print(f'DISPARU> BASE={BASE}')
print(f'DISPARU> KEY={KEY}')
print(f'DISPARU> PATH={os.getenv("PATH")}')
print(f'DISPARU> PYTHONPATH={os.getenv("PYTHONPATH")}')


# +
# start
# -
from dsrc.disparu import app as application
application.secret_key = KEY
