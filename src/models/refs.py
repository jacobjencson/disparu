#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.coordinates import SkyCoord
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

import argparse
import gzip
import json
import math
import os
import sys
import urllib.request

from


# +
# __doc__ string
# -
__doc__ = """
    % python3 galaxies.py --help
"""


# +
# __text__
# -
__text__ = """
Reference image table for HST Failed Supernova Project (GO-15645)

================================================================================
The Identification of Failed Supernovae                                         
------------------------------------------------------------------------------------
Type             Cycle
GO               26       
------------------------------------------------------------------------------------
Investigators                                                                   
                                                                                     Contact?
    PI: Prof. David J. Sand               University of Arizona                         Y 
   CoI: Prof. Jay Strader                 Michigan State University                     N 
   CoI: Dr. Stefano Valenti               University of California - Davis              N 
   CoI: Dr. Nathan Smith                  University of Arizona                         N 
   CoI: Dr. Jennifer Andrews              University of Arizona                         N 
   CoI: Dr. Jacob Jencson                 University of Arizona                         N

------------------------------------------------------------------------------------
Abstract

We request 41 orbits of HST/ACS F814W imaging of a specially chosen sample of nearby
galaxies to identify failed supernovae---the literal disappearance of a massive star
after collapse into a black hole. Based on recent theoretical work on how massive   
stars end their lives, and the apparent lack of stars >18 M_sun exploding as core   
collapse supernovae, we expect to detect ~5-20 failed SNe, a sample large enough to 
provide a conclusive test of this idea. These observations will address the long    
standing mystery of missing core collapse supernova progenitors and test models of  
black hole formation, with broad-reaching consequences for our understanding of     
stellar remnants, chemical enrichment, and predictions for gravitational wave event 
rates.                                                                              
                                                                                    
Any failed supernova candidates will be prime targets for the JWST era, both to     
search for associated cold transients, and to rule out alternative explanations for 
the massive star's disappearance.                                                   

Description:

================================================================================
(End)                                             Jacob Jencson [CDS] 2020-08-06
"""

# +
# constant(s)
# -
DB_VARCHAR = 128
#GWGC_GZIP_URL = 'http://cdsarc.u-strasbg.fr/ftp/VII/267/gwgc.dat.gz'
DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
SORT_ORDER = ['asc', 'desc', 'ascending', 'descending']
SORT_VALUE = ['id', 'pgc', 'name', 'ra', 'dec', '']


# +
# (hidden) function: _get_astropy_coords()
# -
# noinspection PyBroadException
def _get_astropy_coords(_oname=''):
    try:
        _obj = SkyCoord.from_name(_oname)
        return _obj.ra.value, _obj.dec.value
    except Exception:
        return math.nan, math.nan


# +
# initialize sqlalchemy (deferred)
# -
db = SQLAlchemy()


# +
# class: galaxiesRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class refsRecord(db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'galaxies'

    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, )
    
    name = db.Column(db.String(DB_VARCHAR), nullable=False, default='')
    pgc = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    ra = db.Column(db.Float, nullable=False, index=True)
    dec = db.Column(db.Float, nullable=False, index=True)
    redshift = db.Column(db.Float, nullable=True, default=None)
    dm = db.Column(db.Float, nullable=True, default=None)
    dm_err = db.Column(db.Float, nullable=True, default=None)
    dm_method = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    dm_ref = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)

    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
            'pgc': self.pgc,
            'ra': self.ra,
            'dec': self.dec,
            'redshift': self.redshift,
            'dm': self.dm,
            'dm_err': self.dm_err,
            'dm_method': self.dm_method,
            'dm_ref': self.dm_ref,
        }

    # +
    # (overload) method: __str__()
    # -
    def __str__(self):
        return self.id

    # +
    # (static) method: serialize_list()
    # -
    @staticmethod
    def serialize_list(m_records):
        return [_a.serialized() for _a in m_records]


# +
# function: galaxies_filters() alphabetically
# -
# noinspection PyBroadException
def galaxies_filters(query, request_args):

    # return records within astrocone search (API: ?cone=NGC1365,5.0)
    if request_args.get('astrocone'):
        try:
            _nam, _rad = request_args['astrocone'].split(',')
            _ra, _dec = _get_astropy_coords(_nam.strip().upper())
            query = query.filter(func.q3c_radial_query(galaxiesRecord.ra, galaxiesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass

    # return records within cone search (API: ?cone=23.5,29.2,5.0)
    if request_args.get('cone'):
        try:
            _ra, _dec, _rad = request_args['cone'].split(',')
            query = query.filter(func.q3c_radial_query(galaxiesRecord.ra, galaxiesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass

    # return records within ellipse search (API: ?ellipse=202.1,47.2,5.0,0.5,25.0)
    if request_args.get('ellipse'):
        try:
            _ra, _dec, _maj, _rat, _pos = request_args['ellipse'].split(',')
            query = query.filter(
                func.q3c_ellipse_query(galaxiesRecord.ra, galaxiesRecord.dec, _ra, _dec, _maj, _rat, _pos))
        except Exception:
            pass

    # return records with an Dec >= value in degrees (API: ?dec__gte=20.0)
    if request_args.get('dec__gte'):
        query = query.filter(galaxiesRecord.dec >= float(request_args['dec__gte']))

    # return records with an Dec <= value in degrees (API: ?dec__lte=20.0)
    if request_args.get('dec__lte'):
        query = query.filter(galaxiesRecord.dec <= float(request_args['dec__lte']))

    # return records where the distance to the nearest source >= value (API: ?dm__gte=20.0)
    if request_args.get('dm__gte'):
        query = query.filter(galaxiesRecord.dm >= float(request_args['dm__gte']))

    # return records where the distance to the nearest source <= value (API: ?dm__lte=20.0)
    if request_args.get('dm__lte'):
        query = query.filter(galaxiesRecord.dm <= float(request_args['dm__lte']))
        
    # return records where the distance to the nearest source >= value (API: ?dm_err__gte=0.2)
    if request_args.get('dm_err__gte'):
        query = query.filter(galaxiesRecord.dm_err >= float(request_args['dm_err__gte']))

    # return records where the distance to the nearest source <= value (API: ?dm_err__lte=0.2)
    if request_args.get('dm_err__lte'):
        query = query.filter(galaxiesRecord.dm_err <= float(request_args['dm_err__lte']))
        
    # return records with name = value (API: ?name=20)
    if request_args.get('dm_method'):
        query = query.filter(galaxiesRecord.dm_method == request_args['dm_method'])
        
    # return records with name = value (API: ?name=20)
    if request_args.get('dm_ref'):
        query = query.filter(galaxiesRecord.dm_ref == request_args['dm_ref'])

    # return records with id = value (API: ?id=20)
    if request_args.get('id'):
        query = query.filter(galaxiesRecord.id == int(request_args['id']))

    # return records with name = value (API: ?name=20)
    if request_args.get('name'):
        query = query.filter(galaxiesRecord.name == request_args['name'])

    # return records with pgc = value (API: ?pgc=20)
    if request_args.get('pgc'):
        query = query.filter(galaxiesRecord.pgc == request_args['pgc'])

    # return records with an RA >= value in degrees (API: ?ra__gte=12.0)
    if request_args.get('ra__gte'):
        query = query.filter(galaxiesRecord.ra >= float(request_args['ra__gte']))

    # return records with an RA <= value in degrees (API: ?ra__lte=12.0)
    if request_args.get('ra__lte'):
        query = query.filter(galaxiesRecord.ra <= float(request_args['ra__lte']))
    
    # return records where the distance to the nearest source >= value (API: ?redshift__gte=0.01)
    if request_args.get('redshift__gte'):
        query = query.filter(galaxiesRecord.redshift >= float(request_args['redshift__gte']))

    # return records where the distance to the nearest source <= value (API: ?redshift__lte=0.01)
    if request_args.get('redshift__lte'):
        query = query.filter(galaxiesRecord.redshift <= float(request_args['redshift__lte']))

    # sort results
    sort_value = request_args.get('sort_value', SORT_VALUE[0]).lower()
    sort_order = request_args.get('sort_order', SORT_ORDER[0]).lower()
    if sort_order in SORT_ORDER:
        if sort_order.startswith(SORT_ORDER[0]):
            query = query.order_by(getattr(galaxiesRecord, sort_value).asc())
        elif sort_order.startswith(SORT_ORDER[1]):
            query = query.order_by(getattr(galaxiesRecord, sort_value).desc())

    # return query
    return query


# +
# function: galaxies_get_text()
# -
def galaxies_get_text():
    return __text__


# +
# function: galaxies_cli_db()
# -
# noinspection PyBroadException
def galaxies_cli_db(iargs=None):

    # check input(s)
    if iargs is None:
        raise Exception('Invalid arguments')

    # it --catalog is present, dump the catalog from a well-known URL
    # not currently implemented
    if iargs.catalog:
        try:
            print(f"{gzip.decompress(urllib.request.urlopen(DISPARU_GALAXIES_URL).read()).decode('utf-8')}")
        except Exception:
            pass
        return

    # if --text is present, describe of the catalog
    if iargs.text:
        print(galaxies_get_text())
        return

    # set default(s)
    request_args = {}

    # get input(s) alphabetically
    if iargs.astrocone:
        request_args['astrocone'] = f'{iargs.astrocone}'
    if iargs.cone:
        request_args['cone'] = f'{iargs.cone}'
    if iargs.ellipse:
        request_args['ellipse'] = f'{iargs.ellipse}'

    if iargs.dec__gte:
        request_args['dec__gte'] = f'{iargs.dec__gte}'
    if iargs.dec__lte:
        request_args['dec__lte'] = f'{iargs.dec__lte}'
    if iargs.dm__gte:
        request_args['dm__gte'] = f'{iargs.dm__gte}'
    if iargs.dm__lte:
        request_args['dm__lte'] = f'{iargs.dm__lte}'
    if iargs.dm_err__gte:
        request_args['dm_err__gte'] = f'{iargs.dm_err__gte}'
    if iargs.dm_err__lte:
        request_args['dm_err__lte'] = f'{iargs.dm_err__lte}'
    if iargs.dm_method:
        request_args['dm_method'] = f'{iargs.dm_method}'
    if iargs.dm_ref:
        request_args['dm_ref'] = f'{iargs.dm_ref}'
    if iargs.id:
        request_args['id'] = f'{iargs.id}'
    if iargs.name:
        request_args['name'] = f'{iargs.name}'
    if iargs.pgc:
        request_args['pgc'] = f'{iargs.pgc}'
    if iargs.sort_order:
        request_args['sort_order'] = f'{iargs.sort_order}'
    if iargs.sort_value:
        request_args['sort_value'] = f'{iargs.sort_value}'
    if iargs.ra__gte:
        request_args['ra__gte'] = f'{iargs.ra__gte}'
    if iargs.ra__lte:
        request_args['ra__lte'] = f'{iargs.ra__lte}'
    if iargs.ra__gte:
        request_args['redshift__gte'] = f'{iargs.redshift__gte}'
    if iargs.ra__lte:
        request_args['redshift__lte'] = f'{iargs.redshift__lte}'

    # set up access to database
    try:
        if iargs.verbose:
            print(f'connecting via postgresql+psycopg2://'
                  f'{DISPARU_DB_USER}:{DISPARU_DB_PASS}@{DISPARU_DB_HOST}:{DISPARU_DB_PORT}/{DISPARU_DB_NAME}')
        engine = create_engine(
            f'postgresql+psycopg2://{DISPARU_DB_USER}:{DISPARU_DB_PASS}@{DISPARU_DB_HOST}:{DISPARU_DB_PORT}/{DISPARU_DB_NAME}')
        if iargs.verbose:
            print(f'engine = {engine}')
        get_session = sessionmaker(bind=engine)
        if iargs.verbose:
            print(f'Session = {get_session}')
        session = get_session()
        if iargs.verbose:
            print(f'session = {session}')
    except Exception as e:
        raise Exception(f'Failed to connect to database. error={e}')

    # execute query
    try:
        if iargs.verbose:
            print(f'executing query')
        query = session.query(galaxiesRecord)
        if iargs.verbose:
            print(f'query = {query}')
        query = galaxies_filters(query, request_args)
        if iargs.verbose:
            print(f'query = {query}')
    except Exception as e:
        raise Exception(f'Failed to execute query. error={e}')

    # dump output to file
    if isinstance(iargs.output, str) and iargs.output.strip() != '':
        try:
            with open(iargs.output, 'w') as _wf:
                _wf.write(f'#id,name,pgc,ra,dec,redshift,dm,dm_err,dm_method,dm_ref\n')
                for _e in galaxiesRecord.serialize_list(query.all()):
                    _wf.write(f"{_e['id']},{_e['pgc']},{_e['name']},{_e['ra']},{_e['dec']},{_e['redshift']},"
                              f"{_e['dm']},{_e['dm_err']},{_e['dm_method']},{_e['dm_ref']}\n")
        except Exception:
            pass

    # dump output to screen
    else:
        print(f'#id,name,pgc,ra,dec,redshift,dm,dm_err,dm_method,dm_ref')
        for _e in galaxiesRecord.serialize_list(query.all()):
            print(f"{_e['id']},{_e['pgc']},{_e['name']},{_e['ra']},{_e['dec']},{_e['redshift']},"
                  f"{_e['dm']},{_e['dm_err']},{_e['dm_method']},{_e['dm_ref']}")


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s) alphabetically
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description=f'Query galaxies table', formatter_class=argparse.RawTextHelpFormatter)

    _p.add_argument(f'--astrocone', help=f'Astrocone search <name,radius>')
    _p.add_argument(f'--cone', help=f'Cone search <ra,dec,radius>')
    _p.add_argument(f'--ellipse', help=f'Ellipse search <ra,dec,major_axis,axis_ratio,position_angle>')

    _p.add_argument(f'--dec__gte', help=f'Dec >= <float>')
    _p.add_argument(f'--dec__lte', help=f'Dec <= <float>')
    _p.add_argument(f'--dm__gte', help=f'Distance >= <float>')
    _p.add_argument(f'--dm__lte', help=f'Distance <= <float>')
    _p.add_argument(f'--dm_err__gte', help=f'Distance >= <float>')
    _p.add_argument(f'--dm_err__lte', help=f'Distance <= <float>')
    _p.add_argument(f'--dm_method', help=f'dm_method <str>')
    _p.add_argument(f'--dm_ref', help=f'dm_ref <str>')
    _p.add_argument(f'--id', help=f'id <int>')
    _p.add_argument(f'--name', help=f'name <str>')
    _p.add_argument(f'--pa__gte', help=f'Position angle >= <float>')
    _p.add_argument(f'--pa__lte', help=f'Position angle <= <float>')
    _p.add_argument(f'--pgc', help=f'pgc <str>')
    _p.add_argument(f'--ra__gte', help=f'RA >= <float>')
    _p.add_argument(f'--ra__lte', help=f'RA <= <float>')
    _p.add_argument(f'--redshift__gte', help=f'redshift >= <float>')
    _p.add_argument(f'--redshift__lte', help=f'redshift <= <float>')

    _p.add_argument(f'--catalog', default=False, action='store_true', help=f'if present, dump the catalog')
    _p.add_argument(f'--output', default='', help=f'Output file <str>')
    _p.add_argument(f'--sort_order', help=f"Sort order, one of {SORT_ORDER}")
    _p.add_argument(f'--sort_value', help=f"Sort value, one of {SORT_VALUE}")
    _p.add_argument(f'--text', default=False, action='store_true', help=f'if present, describe the catalog')
    _p.add_argument(f'--verbose', default=False, action='store_true', help=f'if present, produce more verbose output')
    args = _p.parse_args()

    # execute
    if args:
        galaxies_cli_db(args)
    else:
        raise Exception(f'Insufficient command line arguments specified\nUse: python {sys.argv[0]} --help')
