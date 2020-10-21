#!/usr/bin/env python3.7


# +
# import(s)
# -
import os


# +
# constant(s)
# -
DISPARU_APP_HOST = os.getenv("DISPARU_APP_HOST", "sassy.as.arizona.edu")
DISPARU_APP_PORT = os.getenv("DISPARU_APP_PORT", 5000)
DISPARU_APP_URL = os.getenv("DISPARU_APP_URL", f"https://{DISPARU_APP_HOST}/disparu")
DISPARU_BIN = os.getenv("DISPARU_BIN", "/var/www/disparu/bin")
DISPARU_DATA = os.getenv("DISPARU_DATA", "")
DISPARU_DB_HOST = os.getenv("DISPARU_DB_HOST", "localhost")
DISPARU_DB_NAME = os.getenv("DISPARU_DB_NAME", "disparu")
DISPARU_DB_PASS = os.getenv("DISPARU_DB_PASS", "db_secret")
DISPARU_DB_PORT = os.getenv("DISPARU_DB_PORT", 5435)
DISPARU_DB_USER = os.getenv("DISPARU_DB_USER", "disparu")
DISPARU_ETC = os.getenv("DISPARU_ETC", "/var/www/disparu/etc")
DISPARU_HOME = os.getenv("DISPARU_HOME", "/var/www/disparu")
DISPARU_LOGS = os.getenv("DISPARU_LOGS", "/var/www/disparu/logs")
DISPARU_SRC = os.getenv("DISPARU_SRC", "/var/www/disparu/dsrc")
DISPARU_TYPE = os.getenv("DISPARU_TYPE", "")
PYTHONPATH = os.getenv("PYTHONPATH", "/var/www/disparu:/var/www/disparu/dsrc")
