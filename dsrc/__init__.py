#!/usr/bin/env python3


# +
# import(s)
# -
# noinspection PyUnresolvedReferences
from astropy.coordinates import Angle
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.time import Time
from datetime import datetime
from datetime import timedelta

import base64
import ephem
import hashlib
import logging
import logging.config
import math
import os
import pytz
import random
import re


# +
# constant(s)
# -
DISPARU_ALPHABET_UC = {chr(_i): _i for _i in range(65, 91)}
DISPARU_ALPHABET_LC = {chr(_i): _i for _i in range(97, 123)}
DISPARU_ASTROPLAN_IERS_URL = 'ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all'
DISPARU_ASTROPLAN_IERS_URL_ALTERNATE = 'https://datacenter.iers.org/data/9/finals2000A.all'
DISPARU_BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DISPARU_COMMENT_CHARS = r' #%!<>+-\/'
DISPARU_DEC_PATTERN = '[+-]?[0-9]{2}:[0-9]{2}:[0-9]{2}'
DISPARU_DECODE_DICT = \
    {'.us.': '_', '.sq.': "'", '.ws.': ' ', '.bs.': '\\', '.at.': '@', '.bg.': '!', '.dq.': '"', '.eq.': '='}
DISPARU_ENCODE_DICT = {v: k for k, v in DISPARU_DECODE_DICT.items()}
DISPARU_EPHEM_PATTERN = '[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]'
DISPARU_FALSE_VALUES = [0, False, '0', 'false', 'f', 'FALSE', 'F']
DISPARU_ISO_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
DISPARU_ISO_PATTERN = '[0-9]{4}-[0-9]{2}-[0-9]{2}[ T?][0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6}'
DISPARU_LOG_CLR_FMT = \
    '%(log_color)s%(asctime)-20s %(levelname)-9s %(filename)-15s line:%(lineno)-5d %(message)s'
DISPARU_LOG_CSL_FMT = \
    '%(asctime)-20s %(levelname)-9s %(filename)-15s line:%(lineno)-5d %(message)s'
DISPARU_LOG_FIL_FMT = \
    '%(asctime)-20s %(levelname)-9s %(filename)-15s line:%(lineno)-5d %(message)s'
DISPARU_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
DISPARU_LOG_MAX_BYTES = 9223372036854775807
DISPARU_MJD_OFFSET = 2400000.5
DISPARU_ONE_HOUR = 1.0 / 24.0
DISPARU_RA_PATTERN = '[0-9]{2}:[0-9]{2}:[0-9]{2}'
DISPARU_RESERVED_USERNAMES = ['darks', 'focus', 'skyflats', 'standard']
DISPARU_SECONDS_PER_DAY = 86400.0
DISPARU_SUPPORTED_COLORS = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'black', '']
DISPARU_TIMEZONE = pytz.timezone('America/Phoenix')
DISPARU_TRUE_VALUES = [1, True, '1', 'true', 't', 'TRUE', 'T']
DISPARU_UTC_OFFSET = datetime.now(DISPARU_TIMEZONE).utcoffset().total_seconds()/60.0/60.0
DISPARU_ZERO_NID = '2019-01-01T00:00:00.000000'


# +
# credential(s)
# -
DISPARU_DB_HOST = os.getenv("DISPARU_DB_HOST", "localhost")
DISPARU_DB_NAME = os.getenv("DISPARU_DB_NAME", "disparu")
DISPARU_DB_PASS = os.getenv("DISPARU_DB_PASS", "db_secret")
DISPARU_DB_PORT = os.getenv("DISPARU_DB_PORT", 5432)
DISPARU_DB_USER = os.getenv("DISPARU_DB_USER", "disparu")


# +
# initialization
# -
random.seed(os.getpid())


# +
# class: Logger() inherits from the object class
# -
# noinspection PyBroadException,PyPep8
class Logger(object):

    # +
    # method: __init__
    # -
    def __init__(self, name='', level='DEBUG'):

        # get arguments(s)
        self.name = name
        self.level = level

        # define some variables and initialize them
        self.__msg = None
        self.__logconsole = f'/tmp/console-{self.__name}.log'
        self.__logdir = os.getenv("DISPARU_LOGS", "/var/www/disparu/logs")
        if not os.path.exists(self.__logdir) or not os.access(self.__logdir, os.W_OK):
            self.__logdir = os.getcwd()
        self.__logfile = f'{self.__logdir}/{self.__name}.log'

        # logger dictionary
        utils_logger_dictionary = {

            # logging version
            'version': 1,

            # do not disable any existing loggers
            'disable_existing_loggers': False,

            # use the same formatter for everything
            'formatters': {
                'ObsColoredFormatter': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': DISPARU_LOG_CLR_FMT,
                    'log_colors': {
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'white,bg_red',
                    }
                },
                'ObsConsoleFormatter': {
                    'format': DISPARU_LOG_CSL_FMT
                },
                'ObsFileFormatter': {
                    'format': DISPARU_LOG_FIL_FMT
                }
            },

            # define file and console handlers
            'handlers': {
                'colored': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'ObsColoredFormatter',
                    'level': self.__level,
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'ObsConsoleFormatter',
                    'level': self.__level,
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'ObsFileFormatter',
                    'filename': self.__logfile,
                    'level': self.__level,
                    'maxBytes': DISPARU_LOG_MAX_BYTES
                },
                #'utils': {
                #    'backupCount': 10,
                #    'class': 'logging.handlers.RotatingFileHandler',
                #    'formatter': 'ObsFileFormatter',
                #    'filename': self.__logconsole,
                #    'level': self.__level,
                #    'maxBytes': DISPARU_LOG_MAX_BYTES
                #}
            },

            # make this logger use file and console handlers
            'loggers': {
                self.__name: {
                    # 'handlers': ['colored', 'file', 'utils'],
                    'handlers': ['colored', 'file'],
                    'level': self.__level,
                    'propagate': True
                }
            }
        }

        # configure logger
        logging.config.dictConfig(utils_logger_dictionary)

        # get logger
        self.logger = logging.getLogger(self.__name)

    # +
    # Decorator(s)
    # -
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name=''):
        self.__name = name if (isinstance(name, str) and name.strip() != '') else os.getenv('USER')

    @property
    def level(self):
        return self.__level

    @level.setter
    def level(self, level=''):
        self.__level = level.upper() if \
            (isinstance(level, str) and level.strip() != '' and level.upper() in DISPARU_LOG_LEVELS) else DISPARU_LOG_LEVELS[0]


# +
# function: get_isot()
# -
# noinspection PyBroadException,PyPep8
def get_isot(ndays=0, utc=False):
    """ return date in isot format for any ndays offset """
    try:
        if utc:
            return (datetime.utcnow() + timedelta(days=ndays)).isoformat()
        else:
            return (datetime.now() + timedelta(days=ndays)).isoformat()
    except:
        return None


# +
# function: get_jd()
# -
# noinspection PyBroadException,PyPep8
def get_jd(ndays=0):
    """ return date in jd format for any ndays offset """
    try:
        return Time(get_isot(ndays)).jd
    except:
        return math.nan


# +
# function: isot_to_ephem()
# -
# noinspection PyBroadException,PyPep8
def isot_to_ephem(isot=get_isot()):
    """ returns ephem date object from isot date string """
    try:
        return ephem.Date(isot.replace('-', '/').replace('T', ' '))
    except:
        return None


# +
# function: ephem_to_isot()
# -
# noinspection PyBroadException,PyPep8
def ephem_to_isot(date=None):
    """ returns isot string from ephem date object """
    try:
        return date.datetime().isoformat()
    except:
        return None


# +
# function: isot_to_jd()
# -
# noinspection PyBroadException,PyPep8
def isot_to_jd(isot=get_isot()):
    """ returns jd from isot date string """
    try:
        return Time(isot).jd
    except:
        return math.nan


# +
# function: isot_to_mjd()
# -
# noinspection PyBroadException,PyPep8
def isot_to_mjd(isot=get_isot()):
    """ returns mjd from isot date string """
    try:
        return Time(isot).mjd
    except:
        return math.nan


# +
# function: isot_to_nid()
# -
# noinspection PyBroadException,PyPep8
def isot_to_nid(isot=get_isot()):
    """ returns ARTN night id from isot date string """
    try:
        return int(isot_to_jd(isot) - isot_to_jd(DISPARU_ZERO_NID))
    except:
        return None


# +
# function: nid_to_isot()
# -
# noinspection PyBroadException,PyPep8
def nid_to_isot(nid=0):
    """ returns date string from ARTN night id """
    try:
        return jd_to_isot(isot_to_jd(DISPARU_ZERO_NID) + nid)
    except:
        return None


# +
# function: jd_to_isot()
# -
# noinspection PyBroadException,PyPep8
def jd_to_isot(jd=math.nan):
    """ return isot from jd """
    try:
        return Time(jd, format='jd', precision=6).isot
    except:
        return None


# +
# function: jd_to_mjd()
# -
# noinspection PyBroadException,PyPep8
def jd_to_mjd(jd=math.nan):
    """ return isot from jd """
    try:
        return jd - DISPARU_MJD_OFFSET
    except:
        return math.nan


# +
# function: mjd_to_isot()
# -
# noinspection PyBroadException,PyPep8
def mjd_to_isot(mjd=math.nan):
    """ return isot from jd """
    try:
        return Time(mjd, format='mjd', precision=6).isot
    except:
        return None


# +
# function: mjd_to_jd()
# -
# noinspection PyBroadException,PyPep8
def mjd_to_jd(mjd=math.nan):
    """ return isot from jd """
    try:
        return mjd + DISPARU_MJD_OFFSET
    except:
        return math.nan


# +
# function: get_hash()
# -
# noinspection PyBroadException,PyPep8
def get_hash(seed=''):
    """ return unique 64-character string """
    if not isinstance(seed, str) or seed.strip() == '':
        seed = get_isot()
    try:
        return hashlib.sha256(seed.encode('utf-8')).hexdigest()
    except:
        return None


# +
# function: ra_to_decimal()
# -
# noinspection PyBroadException,PyPep8
def ra_to_decimal(ra='13:29:53 hours'):
    """ return RA H:M:S as a decimal """
    try:
        ra = f'{ra} hours' if 'hours' not in ra.lower() else ra
        return float(Angle(ra).degree)
    except:
        return math.nan


# +
# function: ra_from_decimal()
# -
# noinspection PyBroadException,PyPep8,PyUnresolvedReferences,PyUnresolvedReferences
def ra_from_decimal(ra=math.nan):
    """ return RA H:M:S from decimal """
    try:
        _c = SkyCoord(ra=ra*u.degree, dec=math.nan*u.degree).ra.hms
        _h, _m, _s = int(_c.h), int(_c.m), _c.s
        return f'{_h:02d}:{_m:02d}:{_s:06.3f}'
    except Exception:
        return None


# +
# function: ra_to_hms()
# -
# noinspection PyBroadException,PyPep8,PyUnresolvedReferences
def ra_to_hms(ra=math.nan):
    """ return RA from decimal to H:M:S """
    try:
        _c = Angle(ra, unit=u.degree).hms
        _h, _m, _s = int(_c.h), int(_c.m), _c.s
        return f'{_h:02d}:{_m:02d}:{_s:06.3f}'
    except:
        return None


# +
# function: dec_to_decimal()
# -
# noinspection PyBroadException,PyPep8
def dec_to_decimal(dec='47:11:43 degrees'):
    """ return Dec d:m:s as a decimal """
    try:
        dec = f'{dec} degrees' if 'degrees' not in dec.lower() else dec
        return float(Angle(dec).degree)
    except:
        return math.nan


# +
# function: dec_from_decimal()
# -
# noinspection PyBroadException,PyPep8,PyUnresolvedReferences
def dec_from_decimal(dec=math.nan):
    """ return Dec d:m:s from decimal """
    try:
        # noinspection PyUnresolvedReferences
        _c = SkyCoord(ra=math.nan*u.degree, dec=dec*u.degree).dec.signed_dms
        _d, _m, _s = int(_c.d), int(_c.m), _c.s
        _sign = '+' if _c.sign == 1.0 else '-'
        return f'{_sign}{_d:02d}:{_m:02d}:{_s:06.3f}'
    except:
        return None


# +
# function: dec_to_dms()
# -
# noinspection PyBroadException,PyPep8,PyUnresolvedReferences
def dec_to_dms(dec=math.nan):
    """ return Dec from decimal to d:m:s """
    try:
        _c = Angle(dec, unit=u.degree).signed_dms
        _d, _m, _s = int(_c.d), int(_c.m), _c.s
        _sign = '+' if _c.sign == 1.0 else '-'
        return f'{_sign}{_d:02d}:{_m:02d}:{_s:06.3f}'
    except:
        return None


# +
# function: degree_to_radian()
# -
# noinspection PyBroadException,PyPep8
def degree_to_radian(deg=math.nan):
    """ converts degrees to radians """
    try:
        return math.radians(deg)
    except:
        return math.nan


# +
# function: radian_to_degree()
# -
# noinspection PyBroadException,PyPep8
def radian_to_degree(rad=math.nan):
    """ converts radians to degrees """
    try:
        return math.degrees(rad)
    except:
        return math.nan


# +
# function: get_astropy_coords()
# -
# noinspection PyBroadException,PyPep8
def get_astropy_coords(name='M51'):
    """ return co-ordinates of name via astropy lookup """
    try:
        _name = SkyCoord.from_name(name)
        return _name.ra.value, _name.dec.value
    except:
        return math.nan, math.nan


# +
# function: decode_verboten():
# -
# noinspection PyBroadException,PyPep8
def decode_verboten(string='The.ws.Quick.ws.Brown.ws.Fox.ws.Jumped.ws.Over.ws.The.ws.Lazy.ws.Dog', decode=None):
    decode = decode if (isinstance(decode, dict) and decode is not {} and decode is not None) else DISPARU_DECODE_DICT
    if isinstance(string, str) and string.strip() != '':
        for c in decode.keys():
            if c in string:
                string = string.replace(c, decode[c])
    return string


# +
# function: encode_verboten():
# -
# noinspection PyBroadException,PyPep8
def encode_verboten(string='The Quick Brown Fox Jumped Over The Lazy Dog', encode=None):
    encode = encode if (isinstance(encode, dict) and encode is not {} and encode is not None) else DISPARU_ENCODE_DICT
    if isinstance(string, str) and string != '':
        for c in encode.keys():
            if c in string:
                string = string.replace(c, encode[c])
    return string


# +
# function: get_iers():
# -
# noinspection PyBroadException
def get_iers(url=DISPARU_ASTROPLAN_IERS_URL):

    # check input(s)
    if not isinstance(url, str) or url.strip() == '':
        raise Exception(f'invalid input, url={url}')
    if not (url.lower().startswith('ftp') or url.lower().startswith('http')):
        raise Exception(f'invalid input, url={url}')

    # try astroplan download
    try:
        from astroplan import download_IERS_A
        download_IERS_A()
        return 'astroplan'

    # try alternate download
    except Exception:
        from astroplan import download_IERS_A
        from astropy.utils import iers
        from astropy.utils.data import clear_download_cache
        clear_download_cache()
        iers.IERS_A_URL = f'{url}'
        download_IERS_A()
        return 'astropy'


# +
# function: get_semester()
# -
def get_semester(date=get_isot()):
    """ return tuple of (semester, code, start date isot, input isot, end date isot) """

    # check input(s)
    if not isinstance(date, str) or re.match(DISPARU_ISO_PATTERN, date) is None:
        raise Exception(f'invalid input, date={date}')

    # get semester
    _date = datetime.strptime(date, DISPARU_ISO_FORMAT)
    _semester = int(math.ceil(_date.month/6.))
    if _semester == 1:
        _ans = _semester, f'{_date.year}A', f'{_date.year}-01-01T00:00:00.000000', \
               date, f'{_date.year}-06-30T23:59:59.999999'
    elif _semester == 2:
        _ans = _semester, f'{_date.year}B', f'{_date.year}-07-01T00:00:00.000000', \
               date, f'{_date.year}-12-31T23:59:59.999999'
    else:
        _ans = -1, '', '', date, ''

    # return result
    return _ans


# +
# function: get_last_semester()
# -
def get_last_semester(date=get_isot()):
    """ return tuple of (last semester, code, last start date isot, current input isot, last end date isot) """

    # check input(s)
    if not isinstance(date, str) or re.match(DISPARU_ISO_PATTERN, date) is None:
        raise Exception(f'invalid input, date={date}')

    # get last semester
    _q, _c, _s, _d, _e = get_semester(date)
    _t = math.floor(isot_to_jd(_d) - isot_to_jd(_s)) + 1
    _n = jd_to_isot(isot_to_jd(_d) - _t)
    _q, _c, _s, _d, _e = get_semester(_n)

    # return result
    return _q, _c, _s, date, _e


# +
# function: get_next_semester()
# -
def get_next_semester(date=get_isot()):
    """ return tuple of (next semester, code, next start date isot, current input isot, next end date isot) """

    # check input(s)
    if not isinstance(date, str) or re.match(DISPARU_ISO_PATTERN, date) is None:
        raise Exception(f'invalid input, date={date}')

    # get next semester
    _q, _c, _s, _d, _e = get_semester(date)
    _t = math.floor(isot_to_jd(_e) - isot_to_jd(_d)) + 1
    _n = jd_to_isot(isot_to_jd(_d) + _t)
    _q, _c, _s, _d, _e = get_semester(_n)

    # return result
    return _q, _c, _s, date, _e
