#!/usr/bin/env python3


# +
# import(s)
# -
from dsrc.models.disparu import candidatesRecord
from dsrc.models.disparu import subtractionsRecord
from dsrc.models.disparu import observationsRecord
from dsrc.models.disparu import refsRecord
from dsrc.models.disparu import galaxiesRecord
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import argparse
import math
import os
import sys
import glob
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt


# +
# __doc__ string
# -
__doc__ = """
    % python3 candidates_load.py --help
"""
# +
# constant(s)
# -
CANDIDATES_CATALOG_FILE = os.path.abspath(os.path.expanduser(''))
CANDIDATES_FORMAT = {
    'num':            [0,     6,  'int',      'None',     'index number'],
    'XWIN_IMAGE':     [7,    17,  'float',    'pixels',   'x image position'],
    'YWIN_IMAGE':     [18,   28,  'float',    'pixels',   'y image position'],
    'ALPHAWIN_J2000': [29,   43,  'float',    'degrees',  'J2000 Right Ascension'],
    'DELTAWIN_J2000': [44,   58,  'float',    'degrees',  'J2000 Declination'],
    'FLAGS':          [59,   64,  'int',      'None',     'photometry flags'],
    'snr':            [65,   73,  'float',    'mag',      'signal-to-noise ratio'],
    'FLUX_APER':      [75,   84,  'float',    'counts',   'aperture flux measurement'],
    'FLUXERR_APER':   [85,   97,  'float',    'counts',   'error on aperture flux measurement'],
    'MAG_APER':       [98,  106,  'float',    'mag',      'aperture flux measurement'],
    'MAGERR_APER':    [107, 118,  'float',    'mag',      'error on aperture flux measurement'],
    'ELONGATION':     [119, 129,  'float',    'None',     'elongation measurement'],
    'FWHM_IMAGE':     [130, 140,  'float',    'pixels',   'FWHM measurement'],
    'CLASS_STAR':     [141, 151,  'float',    'None',     'Star-galaxy classifier score'],
    'Scorr_peak':     [152, 162,  'float',    'None',     'peak source value in Scorr image'],
    'sciflux':        [163, 173,  'float',    'counts',   'matched source flux in science image'],
    'diff2sciflux':   [174, 186,  'float',    'None',     'ratio of FLUX_APER to sciflux']
}

DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)

# +
# function: subtractions_load()
# -
def candidates_load(_file='', _ispos=True):
    """
    Loads a candidates catalog into the Disparu database. 

    Parameters:
        _catalog_file (str): the input file to be loaded.
        _ispos (bool): Is this a positive (sci - ref) or negative (ref - sci) subtraction catalog. 
    Returns:
    
    """
    
    # check input(s)
    _file = os.path.abspath(os.path.expanduser(_file))
    if not isinstance(_file, str) or not os.path.exists(_file):
        raise Exception(f'invalid input, _file={_file}')
    
    #get basic image info
    _base_dir = os.path.dirname(_file)
    _filename = os.path.basename(_file)
    _diff_filename = _filename.replace('_cand.cat', '.fits')
    _sub_filename = _filename.replace('_cand.cat', '.fits').replace('_negsub', '')
    _galaxy_name = _base_dir.split('/')[-3]
    #_inst = _base_dir.split('/')[-2]
    _version = _base_dir.split('/')[-1]
    
    # read contents of candidates catalog
    with open(os.path.abspath(os.path.expanduser(_file)), 'r') as _fd:
        _lines = set(_fd.readlines()[1:])

    # get results
    _all_results = []
    for _i, _e in enumerate(_lines):
        _this_result = {}
        for _l in CANDIDATES_FORMAT:
            _xoffset, _yoffset = CANDIDATES_FORMAT[_l][0], CANDIDATES_FORMAT[_l][1]
            _value = _e[_xoffset:_yoffset].strip()
            if CANDIDATES_FORMAT[_l][2].strip().lower() == 'int':
                _this_result[_l] = -1 if _value == '' else int(_value)
            elif CANDIDATES_FORMAT[_l][2].strip().lower() == 'float':
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
    
    _galaxy_id = session.query(galaxiesRecord).filter(galaxiesRecord.name == _galaxy_name).first().id
    _sub_id = session.query(subtractionsRecord).filter(subtractionsRecord.filename == _sub_filename,
                                                       subtractionsRecord.base_dir == _base_dir,
                                                       subtractionsRecord.version == _version).first().id                                    
    #check if candidates have already been entered for this sub. 
    _check_q = session.query(candidatesRecord).filter(candidatesRecord.galaxy_id == _galaxy_id, 
                                                       candidatesRecord.sub_id == _sub_id,
                                                       candidatesRecord.ispos == _ispos)
    if session.query(_check_q.exists()).scalar():
        print(f"Entries for candidate catalog {_filename} {_version} already exist. Skipping.")
    else:
        try:
            for _record in _all_results:
                _candidate = candidatesRecord(
                                sub_id=_sub_id,
                                galaxy_id=_galaxy_id, 
                                xpos=_record['XWIN_IMAGE'],
                                ypos=_record['YWIN_IMAGE'],
                                ra=_record['ALPHAWIN_J2000'],
                                dec=_record['DELTAWIN_J2000'],
                                photflags=_record['FLAGS'],
                                snr=_record['snr'],
                                flux_aper=_record['FLUX_APER'],
                                fluxerr_aper=_record['FLUXERR_APER'],
                                mag_aper=_record['MAG_APER'],
                                magerr_aper=_record['MAGERR_APER'],
                                elongation=_record['ELONGATION'],
                                fwhm_image=_record['FWHM_IMAGE'],
                                class_star=_record['CLASS_STAR'],
                                scorr_peak=_record['Scorr_peak'],
                                sciflux=_record['sciflux'],
                                diff2sciflux=_record['diff2sciflux'],
                                ispos=_ispos)
        
                print(f'{_candidate.serialized()}')
                # update database with results
                this_xpos = _record['XWIN_IMAGE']
                this_ypos = _record['YWIN_IMAGE']
                print(f"Inserting {_galaxy_name} candidate from {_filename} {_version} at x={this_xpos}, y={this_ypos} into database.")
                session.add(_candidate)
            
            session.commit()
            print(f"Inserted {_galaxy_name} candidate catalog {_filename} {_version} into database.")
        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to insert {_galaxy_name} candidate catalog {_filename} {_version} into database, error={e}")
            
        
    #make thumbnails
    #_thumb_path = os.path.join(_base_dir, 'candidate_thumbnails')
    _thumb_path = '/var/www/disparu/dsrc/static/img/thumbnails'
    if not os.path.isdir(_thumb_path):
        os.makedirs(_thumb_path)
        
    #get all the candidates for this subtraction
    _these_candidates = session.query(candidatesRecord).filter(candidatesRecord.sub_id == _sub_id,
                                                               candidatesRecord.ispos == _ispos)
        
    _sci_file = os.path.join(_base_dir, _sub_filename.replace('_D', ''))
    _ref_file = glob.glob(os.path.join(_base_dir, '*ref_drc_sci_eps.fits'))[0]
    _diff_file = os.path.join(_base_dir, _diff_filename)
    
    print(_sci_file)
                                                           
    for _this_candidate in _these_candidates:
        _cand_id = _this_candidate.id
        _xcen = _this_candidate.xpos
        _ycen = _this_candidate.ypos
            
        _label = f'id{_cand_id}'
        try:
            make_thumbnail_trio(_sci_file, _ref_file, _diff_file, _thumb_path, _xcen, _ycen, _size=50, _ext=0, label=_label)
        except Exception as e:
            raise Exception(f'failed to make thumbnails for candidate id {_cand_id}, error={e}')
            
        
def str2bool(_in_str):
    """
    Take an input T/F string and output the boolean value.  

    Parameters:
        _in_str (str): input string, english word or letter to be interpreted as T/F boolean..
    Returns:
        (boolean): True or false boolean value corresponding to input string. 
    
    """
    
    if _in_str in ['True', 'true', 'TRUE', 'yes', 'YES', 'Yes', 'y', 'Y', 't', 'T']:
        return True
    elif  _in_str in ['False', 'false', 'FALSE', 'no', 'NO', 'No', 'n', 'N', 'f', 'F']:
        return False    
    else:
        raise Exception("""Input error: acceptable inputs for --ispos: 
        'True', 'true', 'TRUE', 'yes', 'YES', 'Yes', 'y', 'Y', 't', 'T',
        'False', 'false', 'FALSE', 'no', 'NO', 'No', 'n', 'N', 'f', 'F'""")
        

def make_thumbnail_trio(_sci_file, _ref_file, _diff_file, _out_dir, _xcen, _ycen, _size=50, _ext=0, label=''):
    """
    Create a sci/ref/diff thumbnail trio centered at _xcen, _ycen of _size pixels from input images.
    
    Parameters:
        _sci_file (str): input science image fits file. 
        _ref_file (str): input science image fits file. 
        _diff_file (str): input science image fits file. 
        _xcen (int): x position where thumbnail should be centered
        _ycen (int): y position where thumbnail should be centered
        _size (int): size of square in pixels for thumbnail 
        _ext (int or str): fits extension to be read. 
    
    Returns:
    
    """
    
    out_sci = os.path.join(_out_dir, f"scithumb_x{int(_xcen)}_y{int(_ycen)}_{label}.png")
    out_ref = os.path.join(_out_dir, f"refthumb_x{int(_xcen)}_y{int(_ycen)}_{label}.png")
    out_diff = os.path.join(_out_dir, f"diffthumb_x{int(_xcen)}_y{int(_ycen)}_{label}.png")
    
    _sci_hdu = fits.open(_sci_file)
    _sci_data = _sci_hdu[_ext].data
    
    _ref_hdu = fits.open(_ref_file)
    _ref_data = _ref_hdu[_ext].data
    
    _diff_hdu = fits.open(_diff_file)
    _diff_data = _diff_hdu[_ext].data
    
    _ymin = int(np.maximum(_ycen-_size/2, 0.0))
    _ymax = int(np.minimum(_ycen+_size/2, np.shape(_sci_data)[0]))
    _xmin = int(np.maximum(_xcen-_size/2, 0.0))
    _xmax = int(np.minimum(_xcen+_size/2, np.shape(_sci_data)[1]))
    
    _sci_thumb =  _sci_data[_ymin:_ymax, _xmin:_xmax]
    _ref_thumb =  _ref_data[_ymin:_ymax, _xmin:_xmax]
    _diff_thumb =  _diff_data[_ymin:_ymax, _xmin:_xmax]

    #sci and ref file should be scaled the same way for display.
    _sciref_min = np.minimum(np.amin(_sci_thumb.flatten()), np.amin(_ref_thumb.flatten()))
    _sciref_max = np.maximum(np.amax(_sci_thumb.flatten()), np.amax(_ref_thumb.flatten()))
    
    plt.imsave(out_sci, _sci_thumb, cmap='gray', vmin=_sciref_min, vmax=_sciref_max)
    plt.imsave(out_ref, _ref_thumb, cmap='gray', vmin=_sciref_min, vmax=_sciref_max)
    plt.imsave(out_diff, _diff_thumb, cmap='gray')
    
    _sci_hdu.close()
    _ref_hdu.close()
    _diff_hdu.close()


        
# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description='Load a candidate catalog into the database',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument('-f', '--file', default=CANDIDATES_CATALOG_FILE, help="""Input file [%(default)s]""")
    _p.add_argument('--ispos', default='True', help=""" [%(default)s]""")
    args = _p.parse_args()
    
    _ispos = str2bool(args.ispos)
    
    # execute
    if (args.file and args.ispos):
        candidates_load(args.file.strip(), _ispos)
    else:
        print(f'<<ERROR>> Insufficient command line arguments specified\nUse: python3 {sys.argv[0]} --help')
