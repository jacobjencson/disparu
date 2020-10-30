#!/usr/bin/env python3


# +
# import(s)
# -
from dsrc.models.disparu import subtractionsRecord
from dsrc.models.disparu import observationsRecord
from dsrc.models.disparu import refsRecord
from dsrc.models.disparu import galaxiesRecord
from dsrc.utils.refs_load import refs_load
from dsrc.utils.observations_load import observations_load
from dsrc.utils.disparu_instruments import ACS_utils, WFC3_UVIS_utils
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
    % python3 subtractions_load.py --help
"""
# +
# constant(s)
# -
SUBTRACTION_FILE = os.path.abspath(os.path.expanduser('/Users/jacobjencson/HST_FSNe/data/subtractions/NGC1058/WFC3_UVIS/v200813/f814w_20131213_WFC3-UVIS_arc1_drc_sci_eps_bgsub_D.fits'))

DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)
DISPARU_DATA = os.getenv('DISPARU_DATA', None)


# +
# function: subtractions_load()
# -
def subtractions_load(_file=''):
    """
    Loads a subtraction image and relevant catalogs into the Disparu database. 

    Parameters:
        _file (str): the input fits file to be loaded.
    Returns:
    
    """
    
    # check input(s)
    _file = os.path.abspath(os.path.expanduser(os.path.expandvars(_file)))
    if not isinstance(_file, str) or not os.path.exists(_file):
        raise Exception(f'invalid input, _file={_file}')
    
    #get basic image info
    _base_dir = os.path.dirname(_file).replace(DISPARU_DATA, '$DISPARU_DATA')
    _filename = os.path.basename(_file)
    _arcnum = _filename.split('arc')[1].split('_')[0]
    _galaxy_name = _base_dir.split('/')[-3]
    _inst = _base_dir.split('/')[-2]
    _version = _base_dir.split('/')[-1]
    
    #get ref image and obs image, and load into databse if they aren't already. 
    _record_file = os.path.expandvars(os.path.join(_base_dir, f'arc{_arcnum}_subtraction_record.txt'))
    _ref_file, _obs_file = read_subtraction_record(_record_file)
    _ref_base_dir = os.path.dirname(_ref_file).replace(DISPARU_DATA, '$DISPARU_DATA')
    _ref_filename = os.path.basename(_ref_file)
    _obs_base_dir = os.path.dirname(_obs_file).replace(DISPARU_DATA, '$DISPARU_DATA')
    _obs_filename = os.path.basename(_obs_file)

    try:
        print(f"Loading reference image {_ref_file} into database.")
        refs_load(_ref_file)
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to load reference image {_ref_file} into database, error={e}")
        
    try:
        print(f"Loading archival observation image {_obs_file} into database.")
        observations_load(_obs_file)
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to load archival observation image {_obs_file} into database, error={e}")
    
    #read header info from the original observation file
    #this is because not all header keywords are transfered to difference image. 
    if _inst == 'WFC3_UVIS':
        _record = WFC3_UVIS_utils().get_WFC3_UVIS_img_info(_obs_file)
        _filter = _record['filter']
    elif _inst == 'ACS_WFC':
        _record = ACS_utils().get_ACS_img_info(_obs_file)
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
    _ref_id = session.query(refsRecord).filter(refsRecord.filename == _ref_filename,
                                               refsRecord.base_dir == _ref_base_dir).first().id
    _obs_id = session.query(observationsRecord).filter(observationsRecord.filename == _obs_filename,
                                                       observationsRecord.base_dir == _obs_base_dir).first().id
                                              
    #check if entry already exists, if so skip. 
    _check_q = session.query(subtractionsRecord).filter(subtractionsRecord.galaxy_id == _galaxy_id, 
                             subtractionsRecord.version == _version,
                             subtractionsRecord.filename == _filename)
    if session.query(_check_q.exists()).scalar():
        print(f"Entry for {_galaxy_name} subtraction image {_filename} {_version} already exists. Skipping.")
    else:
        try:
            _subtraction = subtractionsRecord(
                                galaxy_id=_galaxy_id, 
                                obs_id=_obs_id,
                                ref_id=_ref_id,
                                mjdstart=_record['mjdstart'],
                                mjdend=_record['mjdend'], 
                                exptime=_record['exptime'], 
                                tel = _record['tel'],
                                inst =  _inst,
                                filter = _filter,
                                base_dir = _base_dir,
                                filename = _filename,
                                version= _version)
        
            print(f'{_subtraction.serialized()}')
            # update database with results
            print(f"Inserting {_galaxy_name} subtraction image {_filename} {_version} into database")
            session.add(_subtraction)
            session.commit()
            print(f"Inserted {_galaxy_name} subtraction image {_filename} {_version} into database")
        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to insert {_galaxy_name} subtraction image {_filename} {_version} into database, error={e}")

# +
# function: read_subtraction_record()
# -
def read_subtraction_record(_record_file):
    """
    Reads the record file for a subtraction and retrieves info on 
    reference image and archival observation. 

    Parameters:
        _record_file (str): the input record file to be read.
    Returns:
        _ref_file: the corresponding reference file
        _obs_file: the corresponding observation file
    """
    
    _record_f = open(_record_file, 'r')
    _record_lines = _record_f.readlines()

    _ref_file = os.path.expandvars(_record_lines[4].split(':')[-1].strip())
    _obs_file = os.path.expandvars(_record_lines[5].split(':')[-1].strip())

    return(_ref_file, _obs_file)
    

# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description='Read a subtraction image into the database',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument('-f', '--file', default=SUBTRACTION_FILE, help="""Input file [%(default)s]""")
    args = _p.parse_args()

    # execute
    if args.file:
        subtractions_load(args.file.strip())
    else:
        print(f'<<ERROR>> Insufficient command line arguments specified\nUse: python3 {sys.argv[0]} --help')
