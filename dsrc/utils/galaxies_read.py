#!/usr/bin/env python3


# +
# import(s)
# -
from dsrc.models.disparu import galaxiesRecord
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import argparse
import math
import os
import sys


# +
# __doc__ string
# -
__doc__ = """
    % python3 galaxies_read.py --help
"""


# +
# constant(s)
# -
GALAXIES_CATALOG_FILE = os.path.abspath(os.path.expanduser('HST_FSNe_galaxies_table.dat'))
GALAXIES_FORMAT = {
    'name':      [0,     7,  'string',  'None',    'Common name of galaxy'],
    'pgc':       [8,    17,  'string',  'None',    'PGC catalog number'],
    'ra':        [18,   27,  'float',   'degrees', 'J2000 Right Ascension'],
    'dec':       [28,   37,  'float',   'degrees', 'J2000 Declination'],
    'redshift':  [38,   46,  'float',   'None',    'Redshift'],
    'dm':        [47,   54,  'float',   'mag',     'Distance modulus'],
    'dm_err':    [55,   59,  'float',   'mag',     'Error on distance modulus'],
    'dm_method': [60,   72,  'string',  'None',    'Method used for distance measurement'],
    'dm_ref':    [73,   92,  'string',  'None',    'ADS bibcode for distance reference']
}

DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)


# +
# function: galaxies_read()
# -
def galaxies_read(_file=''):

    # check input(s)
    _file = os.path.abspath(os.path.expanduser(_file))
    if not isinstance(_file, str) or not os.path.exists(_file):
        raise Exception(f'invalid input, _file={_file}')

    # read contents
    with open(os.path.abspath(os.path.expanduser(_file)), 'r') as _fd:
        _lines = set(_fd.readlines())

    # get results
    _all_results = []
    for _i, _e in enumerate(_lines):
        _this_result = {}
        for _l in GALAXIES_FORMAT:
            _xoffset, _yoffset = GALAXIES_FORMAT[_l][0], GALAXIES_FORMAT[_l][1]
            _value = _e[_xoffset:_yoffset].strip()
            if GALAXIES_FORMAT[_l][2].strip().lower() == 'int':
                _this_result[_l] = -1 if _value == '' else int(_value)
            elif GALAXIES_FORMAT[_l][2].strip().lower() == 'float':
                _this_result[_l] = float(math.nan) if _value == '' else float(_value)
            else:
                _this_result[_l] = _value
            #_this_result['id'] = int(_i)  # let the database do this itself
        _all_results.append(_this_result)

    # noinspection PyBroadException
    try:
        # connect to database
        print(f'connection string = postgresql+psycopg2://{DISPARU_DB_USER}:{DISPARU_DB_PASS}@'
              f'{DISPARU_DB_HOST}:{DISPARU_DB_PORT}/{DISPARU_DB_NAME}')
        engine = create_engine(f'postgresql+psycopg2://{DISPARU_DB_USER}:{DISPARU_DB_PASS}@'
                               f'{DISPARU_DB_HOST}:{DISPARU_DB_PORT}/{DISPARU_DB_NAME}')
        get_session = sessionmaker(bind=engine)
        session = get_session()
    except Exception as e:
        raise Exception(f'Failed to connect to database, error={e}')

    # noinspection PyBroadException
    _record = None
    try:
        # loop around records
        for _record in _all_results:
            # create object for each record
            _galaxies = galaxiesRecord(
                    #id=_record['id'],   #should default to next value in sequence
                    name=_record['name'], 
                    pgc=_record['pgc'],
                    ra=_record['ra'], 
                    dec=_record['dec'], 
                    redshift=_record['redshift'],
                    dm=_record['dm'],
                    dm_err=_record['dm_err'],
                    dm_method=_record['dm_method'],
                    dm_ref=_record['dm_ref'])
            print(f'{_galaxies.serialized()}')
            # update database with results
            print(f"Inserting object {_record['name']} database")
            session.add(_galaxies)
            session.commit()
            print(f"Inserted object {_record['name']} database")
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to insert object {_record['name']} database, error={e}")


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description='Populate galaxies table from file',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument('-f', '--file', default=GALAXIES_CATALOG_FILE, help="""Input file [%(default)s]""")
    args = _p.parse_args()

    # execute
    if args.file:
        galaxies_read(args.file.strip())
    else:
        print(f'<<ERROR>> Insufficient command line arguments specified\nUse: python3 {sys.argv[0]} --help')
