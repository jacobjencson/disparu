#!/usr/bin/env python3


# +
# import(s)
# -
from dsrc import *
from dsrc.disparu_common import *
from dsrc.utils import *

from dsrc.models.disparu import candidatesRecord
from dsrc.models.disparu import subtractionsRecord
from dsrc.models.disparu import observationsRecord
from dsrc.models.disparu import refsRecord
from dsrc.models.disparu import galaxiesRecord
from dsrc.models.disparu import sourcesRecord
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import argparse
import math
import os
import sys
import glob
import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
import matplotlib.pyplot as plt


# +
# __doc__ string
# -
__doc__ = """
    % python3 candidates_save.py --help
"""
# +
# constant(s)
# -
DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)

SOURCE_MATCH_RADIUS = 0.05 #arcsec, one ACS/WFC pixel

# +
# function: subtractions_load()
# -
def candidates_save(_cand_id: int, _type: str):
    """
    Saves a candidate to the sources table

    Parameters:
        _cand_id (int): the id of the candidate to be saved
    Returns:
    
    """
    
    # query candidate table and check input
    if not isinstance(_cand_id, int):
        raise Exception(f"invalid input, _cand_id={_cand_id}")
    
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
    
    _c_query = session.query(candidatesRecord).filter(candidatesRecord.id==_cand_id).first()
    if _c_query == None:
        print(f'Invalid candidate ID.')
        sys.exit()
    
    #check if a matching sorce already exists
    _c_coord = SkyCoord(ra=_c_query.ra*u.degree, dec=_c_query.dec*u.degree)
    
    _g_s_query = session.query(sourcesRecord).filter(sourcesRecord.galaxy_id==_c_query.galaxy_id)
    _g_s_results = sourcesRecord.serialize_list([row for row in _g_s_query.all()])
    _g_s_ra = np.array([_g_source['ra'] for _g_source in _g_s_results])
    _g_s_dec = np.array([_g_source['dec'] for _g_source in _g_s_results])
    _g_s_coord = SkyCoord(ra=_g_s_ra*u.degree, dec=_g_s_dec*u.degree)
    _g_s_matches = np.where(_g_s_coord.separation(_c_coord) <= SOURCE_MATCH_RADIUS*u.arcsec)[0]
    
    if len(_g_s_matches) > 0:
        print(f"Found {len(_g_s_matches)} matching source(s) in database:")
        for match_ix in _g_s_matches:
            print(_g_s_results[match_ix]['name'])
        print("Candidate not saved as new source.")
        
    else:
        #name the source
        _g_query = session.query(galaxiesRecord).filter(galaxiesRecord.id==_c_query.galaxy_id).first()
        _g_name = _g_query.name
        _g_s_query = session.query(sourcesRecord).filter(sourcesRecord.galaxy_id==_c_query.galaxy_id).all()
        _g_s_num = len(_g_s_query) + 1
        _s_name = f"{_g_name}_DS{_g_s_num}"
        
        print(f"Saving candidate {_cand_id} to database as {_s_name}.")
    
        if _type != '':
            if _type in ['VarStar', 'Transient', 'DispStar', 'Junk']:
                _s_type = _type
                print(f"Source type: {_s_type}")
            else:
                _s_type = get_source_type(_c_query)
                print(f"Invalid source type. Determining source type from candidate data: {_s_type}")
        else:
            _s_type = get_source_type(_c_query)
            print(f"Determining source type from candidate data: {_s_type}")
        
        #save the source
        try:
            _source = sourcesRecord(
                        sub_id = _c_query.sub_id,
                        cand_id = _c_query.id,
                        galaxy_id = _c_query.galaxy_id,
                        name = _s_name,
                        ra = _c_query.ra,
                        dec = _c_query.dec,
                        type = _s_type,
                        redshift = _g_query.redshift
                        )
            print(f'{_source.serialized()}')
            session.add(_source)
            session.commit()
            print(f"Successfully saved candidate {_cand_id} to database as {_s_name}.")
            
        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to save candidate {_cand_id} to database as {_s_name}, error={e}")
    
    

def get_source_type(_c_query):
    """
    Determine the type (VarStar, Transient, DispStar, Junk) of a candidate
    based on it's candidate data. 

    Parameters:
        _c_query: query object for given candidate
    Returns:
        _s_type (str): source type.
    """
    
    _c_ispos = _c_query.ispos
    _c_sciflux = _c_query.sciflux
    _c_diff2sciflux = _c_query.diff2sciflux
    
    
    #if a disappearing source
    if _c_ispos:
        #if faded by half compared to an archival counterpart -> DispStar
        if _c_diff2sciflux >= 0.5:
            _s_type = 'DispStar'
        
        #otherwhise -> VarStar
        else:
            _s_type = 'VarStar'
    
    #if a brightening source, no archival counterpart, or brightened by factor of 2 -> Transient
    elif (_c_sciflux == -99.99) or (_c_diff2sciflux >= 1.0):
        _s_type = 'Transient'
    #Otherwise a variable
    else:
         _s_type = 'VarStar'
    
    return(_s_type)

def get_candidate_type(_c_query):
    """
    Determine the type (VarStar, Transient, DispStar, Junk) of a candidate
    based on it's candidate data. 

    Parameters:
        _c_query (dict): serialized query object for given candidate
    Returns:
        _s_type (str): source type.
    """
    
    _c_ispos = _c_query['ispos']
    _c_sciflux = _c_query['sciflux']
    _c_diff2sciflux = _c_query['diff2sciflux']
    
    
    #if a disappearing source
    if _c_ispos:
        #if faded by half compared to an archival counterpart -> DispStar
        if _c_diff2sciflux >= 0.5:
            _s_type = 'DispStar'
        
        #otherwhise -> VarStar
        else:
            _s_type = 'VarStar'
    
    #if a brightening source, no archival counterpart, or brightened by factor of 2 -> Transient
    elif (_c_sciflux == -99.99) or (_c_diff2sciflux >= 1.0):
        _s_type = 'Transient'
    #Otherwise a variable
    else:
         _s_type = 'VarStar'
    
    return(_s_type)
        
# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description='Save a candidate to the sources table.',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument('-c', '--cid', default='0', help="""Candidate ID [%(default)s]""")
    _p.add_argument('-t', '--type', default='', help="""Source type [%(default)s]""")
    args = _p.parse_args()
    
    _cand_id = int(args.cid)
    _type = str(args.type)
    
    # execute
    if (args.cid):
        candidates_save(_cand_id, _type)
    else:
        print(f'<<ERROR>> Insufficient command line arguments specified\nUse: python3 {sys.argv[0]} --help')
