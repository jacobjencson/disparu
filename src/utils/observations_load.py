#!/usr/bin/env python3


# +
# import(s)
# -
from src.models.disparu import observationsRecord
from src.models.disparu import galaxiesRecord
from src.utils.disparu_instruments import ACS_utils, WFC3_UVIS_utils
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
    % python3 observations_load.py --help
"""
# +
# constant(s)
# -
OBSERVATION_FILE = os.path.abspath(os.path.expanduser('/Users/jacobjencson/HST_FSNe/data/observations/NGC1058/WFC3_UVIS/v200812/f814w_20131213_WFC3-UVIS_arc1_drc.fits'))

DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)

# +
# function: galaxies_read()
# -
def observations_load(_file=''):
    """
    Loads an observation into the Disparu database. 

    Parameters:
        _file (str): the input fits file to be loaded.
    Returns:
        

    """
    
    # check input(s)
    _file = os.path.abspath(os.path.expanduser(_file))
    if not isinstance(_file, str) or not os.path.exists(_file):
        raise Exception(f'invalid input, _file={_file}')
    
    #get basic image info
    _base_dir = os.path.dirname(_file)
    _filename = os.path.basename(_file)
    _galaxy_name = _base_dir.split('/')[-3]
    _inst = _base_dir.split('/')[-2]
    _version = _base_dir.split('/')[-1]
    
    if _inst == 'WFC3_UVIS':
        _record = WFC3_UVIS_utils().get_WFC3_UVIS_img_info(_file)
        _filter = _record['filter']
    elif _inst == 'ACS_WFC':
        _record = ACS_utils().get_ACS_img_info(_file)
        _filter = ACS_utils.get_ACS_filter_name(_record['filter1'], _record['filter2'])
    
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
    
    _galaxy_id = session.query(galaxiesRecord).filter(galaxiesRecord.name == _galaxy_name).first().id
    
    #check if entry already exists, if so skip. 
    _check_q = session.query(observationsRecord).filter(observationsRecord.galaxy_id == _galaxy_id, 
                             observationsRecord.version == _version,
                             observationsRecord.filename == _filename)
    if session.query(_check_q.exists()).scalar():
        print(f"Entry for {_galaxy_name} observation {_filename} {_version} already exists. Skipping.")
    else:
        try:
            _observation = observationsRecord(
                                galaxy_id=_galaxy_id, 
                                mjdstart=_record['mjdstart'],
                                mjdend=_record['mjdend'], 
                                exptime=_record['exptime'], 
                                tel = _record['tel'],
                                inst =  _inst,
                                filter = _filter,
                                base_dir = _base_dir,
                                filename = _filename,
                                version= _version)
        
            print(f'{_observation.serialized()}')
            # update database with results
            print(f"Inserting {_galaxy_name} image file {_filename} {_version} into database")
            session.add(_observation)
            session.commit()
            print(f"Inserted {_galaxy_name} image file {_filename} {_version} into database")
        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to insert {_galaxy_name} image file {_filename} {_version} into database, error={e}")
    

# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description='Read an observation into the database',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument('-f', '--file', default=OBSERVATION_FILE, help="""Input file [%(default)s]""")
    args = _p.parse_args()

    # execute
    if args.file:
        observations_load(args.file.strip())
    else:
        print(f'<<ERROR>> Insufficient command line arguments specified\nUse: python3 {sys.argv[0]} --help')