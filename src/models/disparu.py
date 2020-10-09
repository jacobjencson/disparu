#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.coordinates import SkyCoord
from astropy.time import Time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker

import argparse
import gzip
import json
import math
import os
import sys
import datetime
import urllib.request


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
Disparu database for HST Failed Supernova Project (GO-15645)

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

File Summary:
--------------------------------------------------------------------------------
 FileName                    Lrecl  Records   Explanations
--------------------------------------------------------------------------------
README                           8        0   This file
HST_FSNe_galaxies_table.dat      4       31   Basic Galaxy Data table
--------------------------------------------------------------------------------

Byte-by-byte Description of file: HST_FSNe_galaxies_table.dat
--------------------------------------------------------------------------------
   Bytes Format Units    Label    Explanations
--------------------------------------------------------------------------------
   1-  7  A7    ---      name      NGC name of galaxy
   9- 17  A9    ---      pgc       PGC number of galaxy
  19- 27  F9.5  deg      ra        Right ascension (J2000, decimal degrees)
  29- 37  F9.5  deg      dec       Declination (J2000)
  39- 46  F8.6  ---      redshift  Redshift
  48- 54  F7.2  mag      dm        Distance modulus
  56- 59  F4.2  mag      dm_err    Error on distance modulus
  61- 72  A12   ---      dm_method Method used for distance measurement
  74- 92  A19   ---      dm_ref    ADS bibcode for distance reference    
--------------------------------------------------------------------------------
Notes: 
--------------------------------------------------------------------------------

================================================================================
(End)                                             Jacob Jencson [CDS] 2020-07-31
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
# Declare classes for each table
# -

# +
# class: galaxiesRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class galaxiesRecord(db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'galaxies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(DB_VARCHAR), nullable=False, default='')
    pgc = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    ra = db.Column(db.Float, nullable=False, index=True)
    dec = db.Column(db.Float, nullable=False, index=True)
    redshift = db.Column(db.Float, nullable=True, default=None)
    dm = db.Column(db.Float, nullable=True, default=None)
    dm_err = db.Column(db.Float, nullable=True, default=None)
    dm_method = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    dm_ref = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    
    refs = db.relationship('refsRecord', backref='galaxy', lazy=True)
    observations = db.relationship('observationsRecord', backref='galaxy', lazy=True)

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
# class: galaxiesRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class refsRecord(db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'refs'

    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxies.id'), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    mjdstart = db.Column(db.Float, nullable=True, default=None)
    mjdend = db.Column(db.Float, nullable=True, default=None)
    exptime = db.Column(db.Float, nullable=True, default=None)
    tel = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    inst = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    filter = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    base_dir = db.Column(db.Text, nullable=False, default='')
    filename = db.Column(db.Text, nullable=False, default='')
    version = db.Column(db.String(7), nullable=False, default='')
    
    subtractions = db.relationship('subtractionsRecord', backref='ref', lazy=True)

    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    def serialized(self):
        return {
            'id': self.id,
            'galaxy_id': self.galaxy_id,
            'creation_date': self.creation_date,
            'mjdstart': self.mjdstart,
            'mjdend': self.mjdend,
            'tel': self.tel,
            'inst': self.inst,
            'filter': self.filter,
            'base_dir': self.base_dir,
            'filename': self.filename,
            'version': self.version,
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
# class: observationsRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class observationsRecord(db.Model):
    
    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'observations'

    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxies.id'), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    mjdstart = db.Column(db.Float, nullable=True, default=None)
    mjdend = db.Column(db.Float, nullable=True, default=None)
    exptime = db.Column(db.Float, nullable=True, default=None)
    tel = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    inst = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    filter = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    base_dir = db.Column(db.Text, nullable=False, default='')
    filename = db.Column(db.Text, nullable=False, default='')
    version = db.Column(db.String(7), nullable=False, default='')
    
    subtractions = db.relationship('subtractionsRecord', backref='observation', lazy=True)

    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    def serialized(self):
        return {
            'id': self.id,
            'galaxy_id': self.galaxy_id,
            'creation_date': self.creation_date,
            'mjdstart': self.mjdstart,
            'mjdend': self.mjdend,
            'tel': self.tel,
            'inst': self.inst,
            'filter': self.filter,
            'base_dir': self.base_dir,
            'filename': self.filename,
            'version': self.version,
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
# class: subtractionsRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class subtractionsRecord(db.Model):
    
    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'subtractions'

    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxies.id'), nullable=False)
    obs_id = db.Column(db.Integer, db.ForeignKey('observations.id'), nullable=False)
    ref_id = db.Column(db.Integer, db.ForeignKey('refs.id'), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    mjdstart = db.Column(db.Float, nullable=True, default=None)
    mjdend = db.Column(db.Float, nullable=True, default=None)
    exptime = db.Column(db.Float, nullable=True, default=None)
    tel = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    inst = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    filter = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    base_dir = db.Column(db.Text, nullable=False, default='')
    filename = db.Column(db.Text, nullable=False, default='')
    version = db.Column(db.String(7), nullable=False, default='')

    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    def serialized(self):
        return {
            'id': self.id,
            'galaxy_id': self.galaxy_id,
            'obs_id': self.obs_id,
            'ref_id': self.ref_id,
            'creation_date': self.creation_date,
            'mjdstart': self.mjdstart,
            'mjdend': self.mjdend,
            'tel': self.tel,
            'inst': self.inst,
            'filter': self.filter,
            'base_dir': self.base_dir,
            'filename': self.filename,
            'version': self.version,
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
# class: candidatesRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class candidatesRecord(db.Model):
    
    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    sub_id = db.Column(db.Integer, db.ForeignKey('subtractions.id'), nullable=False)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxies.id'), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    xpos = db.Column(db.Float, nullable=True, default=None)
    ypos = db.Column(db.Float, nullable=True, default=None)
    ra = db.Column(db.Float, nullable=True, default=None)
    dec = db.Column(db.Float, nullable=True, default=None)
    photflags = db.Column(db.Integer, nullable=True, default=None)
    snr = db.Column(db.Float, nullable=True, default=None)
    flux_aper = db.Column(db.Float, nullable=True, default=None)
    fluxerr_aper = db.Column(db.Float, nullable=True, default=None)
    mag_aper = db.Column(db.Float, nullable=True, default=None)
    magerr_aper = db.Column(db.Float, nullable=True, default=None)
    elongation = db.Column(db.Float, nullable=True, default=None)
    fwhm_image = db.Column(db.Float, nullable=True, default=None)
    class_star = db.Column(db.Float, nullable=True, default=None)
    scorr_peak = db.Column(db.Float, nullable=True, default=None)
    sciflux = db.Column(db.Float, nullable=True, default=None)
    diff2sciflux = db.Column(db.Float, nullable=True, default=None)
    ispos = db.Column(db.Boolean, nullable=True, default=None)

    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    def serialized(self):
        return {
            'id': self.id,
            'sub_id': self.sub_id,
            'galaxy_id': self.galaxy_id,
            'creation_date': self.creation_date,
            'xpos': self.xpos,
            'ypos': self.ypos,
            'ra': self.ra,
            'dec': self.dec,
            'photflags': self.photflags,
            'snr': self.snr,
            'flux_aper': self.flux_aper,
            'fluxerr_aper': self.fluxerr_aper,
            'mag_aper': self.mag_aper,
            'magerr_aper': self.magerr_aper,
            'elongation': self.elongation,
            'fwhm_image': self.fwhm_image,
            'class_star': self.class_star,
            'scorr_peak': self.scorr_peak,
            'sciflux': self.sciflux,
            'diff2sciflux': self.diff2sciflux,
            'ispos': self.ispos
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
# class: sourcesRecord(), inherits from db.Model
# -
# noinspection PyUnresolvedReferences
class sourcesRecord(db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'sources'

    id = db.Column(db.Integer, primary_key=True)
    sub_id = db.Column(db.Integer, db.ForeignKey('subtractions.id'), nullable=True)
    cand_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxies.id'), nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    name = db.Column(db.String(DB_VARCHAR), nullable=False, default='')
    ra = db.Column(db.Float, nullable=True, default=None)
    dec = db.Column(db.Float, nullable=True, default=None)
    type = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    classification = db.Column(db.String(DB_VARCHAR), nullable=True, default=None)
    redshift = db.Column(db.Float, nullable=True, default=None)

    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    def serialized(self):
        return {
            'id': self.id,
            'sub_id': self.sub_id,
            'cand_id': self.cand_id,
            'galaxy_id': self.galaxy_id,
            'creation_date': self.creation_date,
            'name': self.name,
            'ra': self.ra,
            'dec': self.dec,
            'type': self.type,
            'classification': self.classification,
            'redshift': self.redshift
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
# function: candidates_filters() alphabetically
# -
# noinspection PyBroadException
def candidates_filters(query, request_args):
    
    # return records within astrocone search (API: ?cone=NGC1365,5.0)
    if request_args.get('cand_astrocone'):
        try:
            _nam, _rad = request_args['cand_astrocone'].split(',')
            _ra, _dec = _get_astropy_coords(_nam.strip().upper())
            query = query.filter(func.q3c_radial_query(candidatesRecord.ra, candidatesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass
    
    # return records within cone search (API: ?cone=23.5,29.2,5.0)
    if request_args.get('cand_cone'):
        try:
            _ra, _dec, _rad = request_args['cand_cone'].split(',')
            query = query.filter(func.q3c_radial_query(candidatesRecord.ra, candidatesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass
    
    # return records within ellipse search (API: ?ellipse=202.1,47.2,5.0,0.5,25.0)
    if request_args.get('cand_ellipse'):
        try:
            _ra, _dec, _maj, _rat, _pos = request_args['cand_ellipse'].split(',')
            query = query.filter(
                func.q3c_ellipse_query(candidatesRecord.ra, candidatesRecord.dec, _ra, _dec, _maj, _rat, _pos))
        except Exception:
            pass
    
    # return records with class_star >= value (API: ?class_star__gte=0.5)
    if request_args.get('class_star__gte'):
        query = query.filter(candidatesRecord.class_star >= float(request_args['class_star__gte']))

    # return records with class_star <= value (API: ?class_star__lte=0.5)
    if request_args.get('class_star__lte'):
        query = query.filter(candidatesRecord.class_star <= float(request_args['class_star__lte']))
    
    # return records with an Dec >= value in degrees (API: ?dec__gte=20.0)
    if request_args.get('cand_dec__gte'):
        query = query.filter(candidatesRecord.dec >= float(request_args['cand_dec__gte']))

    # return records with an Dec <= value in degrees (API: ?dec__lte=20.0)
    if request_args.get('cand_dec__lte'):
        query = query.filter(candidatesRecord.dec <= float(request_args['cand_dec__lte']))
        
    # return records with diff2sciflux >= value (API: ?diff2sciflux__gte=0.5)
    if request_args.get('diff2sciflux__gte'):
        query = query.filter(candidatesRecord.diff2sciflux >= float(request_args['diff2sciflux__gte']))

    # return records with diff2sciflux <= value (API: ?diff2sciflux__lte=0.5)
    if request_args.get('diff2sciflux__lte'):
        query = query.filter(candidatesRecord.diff2sciflux <= float(request_args['diff2sciflux__lte']))
    
    # return records with an elongation >= value (API: ?elongation__gte=1.5)
    if request_args.get('elongation__gte'):
        query = query.filter(candidatesRecord.elongation >= float(request_args['elongation__gte']))

    # return records with an elongation <= value (API: ?elongation__lte=1.5)
    if request_args.get('elongation__lte'):
        query = query.filter(candidatesRecord.elongation <= float(request_args['elongation__lte']))
    
    # return records with flux_aper >= value (API: ?flux_aper__gte=10.0)
    if request_args.get('flux_aper__gte'):
        query = query.filter(candidatesRecord.flux_aper >= float(request_args['flux_aper__gte']))

    # return records with an flux_aper <= value (API: ?flux_aper__lte=10.0)
    if request_args.get('flux_aper__lte'):
        query = query.filter(candidatesRecord.flux_aper <= float(request_args['flux_aper__lte']))
        
    # return records with fluxerr_aper >= value (API: ?fluxerr_aper__gte=0.2)
    if request_args.get('fluxerr_aper__gte'):
        query = query.filter(candidatesRecord.fluxerr_aper >= float(request_args['fluxerr_aper__gte']))
        
    # return records with fluxerr_aper >= value (API: ?fluxerr_aper__lte=0.2)
    if request_args.get('fluxerr_aper__lte'):
        query = query.filter(candidatesRecord.fluxerr_aper <= float(request_args['fluxerr_aper__lte']))

    # return records with an fwhm_image >= value in pixels (API: ?fwhm_value__gte=1.5)
    if request_args.get('fwhm_image__gte'):
       query = query.filter(candidatesRecord.fwhm_image >= float(request_args['fwhm_image__gte']))

    # return records with an fwhm_image <= value in degrees (API: ?fwhm_value__lte=1.5)
    if request_args.get('fwhm_image__lte'):
        query = query.filter(candidatesRecord.fwhm_image <= float(request_args['fwhm_image__lte']))
    
    # return records with galaxy_id = value (API: ?galaxy_id=20)
    if request_args.get('galaxy_id'):
        query = query.filter(candidatesRecord.galaxy_id == int(request_args['galaxy_id']))
        
    # return records with id = value (API: ?id=20)
    if request_args.get('cand_id'):
        query = query.filter(candidatesRecord.id == int(request_args['cand_id']))
        
    # return records with ispos = value (API: ?ispos=True)
    if request_args.get('ispos'):
        if request_args['ispos'] == 'True':
            query = query.filter(candidatesRecord.ispos == True)
        elif request_args['ispos'] == 'False':
            query = query.filter(candidatesRecord.ispos == False)
            
    # return records with mag_aper >= value in mag (API: ?mag_aper__gte=20.0)
    if request_args.get('mag_aper__gte'):
        query = query.filter(candidatesRecord.mag_aper >= float(request_args['mag_aper__gte']))

    # return records with mag_aper <= value in mag (API: ?mag_aper__lte=20.0)
    if request_args.get('mag_aper__lte'):
        query = query.filter(candidatesRecord.mag_aper <= float(request_args['mag_aper__lte']))
        
    # return records with magerr_aper >= value in mag (API: ?magerr_aper__gte=0.2)
    if request_args.get('magerr_aper__gte'):
        query = query.filter(candidatesRecord.magerr_aper >= float(request_args['magerr_aper__gte']))

    # return records with magerr_aper <= value in mag (API: ?magerr_aper__lte=0.2)
    if request_args.get('magerr_aper__lte'):
        query = query.filter(candidatesRecord.magerr_aper <= float(request_args['magerr_aper__lte']))
        
    # return records with photflags = value (API: ?photflags=0)
    if request_args.get('photflags'):
        query = query.filter(candidatesRecord.photflags == int(request_args['photflags']))
    
    # return records with an photflags >= value in degrees (API: ?photflags__gte=1)
    if request_args.get('photflags__gte'):
        query = query.filter(candidatesRecord.photflags >= int(request_args['photflags__gte']))

    # return records with photflags <= value in degrees (API: ?photflags__lte=1)
    if request_args.get('photflags__lte'):
        query = query.filter(candidatesRecord.photflags <= int(request_args['photflags__lte']))
        
    # return records with an RA >= value in degrees (API: ?ra__gte=12.0)
    if request_args.get('cand_ra__gte'):
        query = query.filter(candidatesRecord.ra >= float(request_args['cand_ra__gte']))

    # return records with an RA <= value in degrees (API: ?ra__lte=12.0)
    if request_args.get('cand_ra__lte'):
        query = query.filter(candidatesRecord.ra <= float(request_args['cand_ra__lte']))
        
    # return records with sciflux >= value (API: ?sciflux__gte=1.0)
    if request_args.get('sciflux__gte'):
        query = query.filter(candidatesRecord.sciflux >= float(request_args['sciflux__gte']))

    # return records with sciflux <= value (API: ?sciflux__lte=1.0)
    if request_args.get('sciflux__lte'):
        query = query.filter(candidatesRecord.sciflux <= float(request_args['sciflux__lte']))
        
    # return records with scorr_peak >= value (API: ?scorr_peak__gte=5.0)
    if request_args.get('scorr_peak__gte'):
        query = query.filter(candidatesRecord.scorr_peak >= float(request_args['scorr_peak__gte']))

    # return records with scorr_peak <= value (API: ?scorr_peak__lte=5.0)
    if request_args.get('scorr_peak__lte'):
        query = query.filter(candidatesRecord.scorr_peak <= float(request_args['scorr_peak__lte']))
        
    # return records with sub_id = value (API: ?sub_id=20)
    if request_args.get('sub_id'):
        query = query.filter(candidatesRecord.sub_id == int(request_args['sub_id']))
    
    # return records with xpos >= value in pixels (API: ?xpos__gte=1000.0)
    if request_args.get('xpos__gte'):
        query = query.filter(candidatesRecord.xpos >= float(request_args['xpos__gte']))

    # return records with xpos <= value in pixels (API: ?xpos__lte=1000.0)
    if request_args.get('xpos__lte'):
        query = query.filter(candidatesRecord.xpos <= float(request_args['xpos__lte']))
    
    # return records with ypos >= value in pixels (API: ?ypos__gte=1000.0)
    if request_args.get('ypos__gte'):
        query = query.filter(candidatesRecord.ypos >= float(request_args['ypos__gte']))

    # return records with ypos <= value in pixels (API: ?ypos__lte=1000.0)
    if request_args.get('ypos__lte'):
        query = query.filter(candidatesRecord.ypos <= float(request_args['ypos__lte']))
    
    # sort results
    sort_value = request_args.get('sort_value', SORT_VALUE[0]).lower()
    sort_order = request_args.get('sort_order', SORT_ORDER[0]).lower()
    if sort_order in SORT_ORDER:
        if sort_order.startswith(SORT_ORDER[0]):
            query = query.order_by(getattr(candidatesRecord, sort_value).asc())
        elif sort_order.startswith(SORT_ORDER[1]):
            query = query.order_by(getattr(candidatesRecord, sort_value).desc())

    # return query
    return query
    

# +
# function: galaxies_filters() alphabetically
# -
# noinspection PyBroadException
def galaxies_filters(query, request_args):

    # return records within astrocone search (API: ?cone=NGC1365,5.0)
    if request_args.get('gal_astrocone'):
        try:
            _nam, _rad = request_args['gal_astrocone'].split(',')
            _ra, _dec = _get_astropy_coords(_nam.strip().upper())
            query = query.filter(func.q3c_radial_query(galaxiesRecord.ra, galaxiesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass

    # return records within cone search (API: ?cone=23.5,29.2,5.0)
    if request_args.get('gal_cone'):
        try:
            _ra, _dec, _rad = request_args['gal_cone'].split(',')
            query = query.filter(func.q3c_radial_query(galaxiesRecord.ra, galaxiesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass

    # return records within ellipse search (API: ?ellipse=202.1,47.2,5.0,0.5,25.0)
    if request_args.get('gal_ellipse'):
        try:
            _ra, _dec, _maj, _rat, _pos = request_args['gal_ellipse'].split(',')
            query = query.filter(
                func.q3c_ellipse_query(galaxiesRecord.ra, galaxiesRecord.dec, _ra, _dec, _maj, _rat, _pos))
        except Exception:
            pass

    # return records with an Dec >= value in degrees (API: ?dec__gte=20.0)
    if request_args.get('gal_dec__gte'):
        query = query.filter(galaxiesRecord.dec >= float(request_args['gal_dec__gte']))

    # return records with an Dec <= value in degrees (API: ?dec__lte=20.0)
    if request_args.get('gal_dec__lte'):
        query = query.filter(galaxiesRecord.dec <= float(request_args['gal_dec__lte']))

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
    if request_args.get('gal_id'):
        query = query.filter(galaxiesRecord.id == int(request_args['gal_id']))

    # return records with name = value (API: ?name=20)
    if request_args.get('gal_name'):
        query = query.filter(galaxiesRecord.name == request_args['gal_name'])

    # return records with pgc = value (API: ?pgc=20)
    if request_args.get('pgc'):
        query = query.filter(galaxiesRecord.pgc == request_args['pgc'])

    # return records with an RA >= value in degrees (API: ?ra__gte=12.0)
    if request_args.get('gal_ra__gte'):
        query = query.filter(galaxiesRecord.ra >= float(request_args['gal_ra__gte']))

    # return records with an RA <= value in degrees (API: ?ra__lte=12.0)
    if request_args.get('gal_ra__lte'):
        query = query.filter(galaxiesRecord.ra <= float(request_args['gal_ra__lte']))
    
    # return records where the distance to the nearest source >= value (API: ?redshift__gte=0.01)
    if request_args.get('redshift__gte'):
        query = query.filter(galaxiesRecord.redshift >= float(request_args['redshift__gte']))

    # return records where the distance to the nearest source <= value (API: ?redshift__lte=0.01)
    if request_args.get('redshift__lte'):
        query = query.filter(galaxiesRecord.redshift <= float(request_args['redshift__lte']))

    # sort results
    sort_value = request_args.get('gal_sort_value', SORT_VALUE[0]).lower()
    sort_order = request_args.get('gal_sort_order', SORT_ORDER[0]).lower()
    if sort_order in SORT_ORDER:
        if sort_order.startswith(SORT_ORDER[0]):
            query = query.order_by(getattr(galaxiesRecord, sort_value).asc())
        elif sort_order.startswith(SORT_ORDER[1]):
            query = query.order_by(getattr(galaxiesRecord, sort_value).desc())

    # return query
    return query
    
# +
# function: candidates_filters() alphabetically
# -
# noinspection PyBroadException
def sources_filters(query, request_args):
    
    # return records within astrocone search (API: ?cone=NGC1365,5.0)
    if request_args.get('source_astrocone'):
        try:
            _nam, _rad = request_args['source_astrocone'].split(',')
            _ra, _dec = _get_astropy_coords(_nam.strip().upper())
            query = query.filter(func.q3c_radial_query(sourcesRecord.ra, sourcesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass
    
    # return records within cone search (API: ?cone=23.5,29.2,5.0)
    if request_args.get('source_cone'):
        try:
            _ra, _dec, _rad = request_args['source_cone'].split(',')
            query = query.filter(func.q3c_radial_query(candidatesRecord.ra, candidatesRecord.dec, _ra, _dec, _rad))
        except Exception:
            pass
    
    # return records within ellipse search (API: ?ellipse=202.1,47.2,5.0,0.5,25.0)
    if request_args.get('source_ellipse'):
        try:
            _ra, _dec, _maj, _rat, _pos = request_args['souce_ellipse'].split(',')
            query = query.filter(
                func.q3c_ellipse_query(candidatesRecord.ra, candidatesRecord.dec, _ra, _dec, _maj, _rat, _pos))
        except Exception:
            pass
            
    # return records with id = value (API: ?id=20)
    if request_args.get('source_class'):
        query = query.filter(sourcesRecord.classification == request_args['source_class'])
    
    # return records with an Dec >= value in degrees (API: ?dec__gte=20.0)
    if request_args.get('source_dec__gte'):
        query = query.filter(sourcesRecord.dec >= float(request_args['source_dec__gte']))

    # return records with an Dec <= value in degrees (API: ?dec__lte=20.0)
    if request_args.get('source_dec__lte'):
        query = query.filter(sourcesRecord.dec <= float(request_args['source_dec__lte']))
    
    # return records with galaxy_id = value (API: ?galaxy_id=20)
    if request_args.get('galaxy_id'):
        query = query.filter(sourcesRecord.galaxy_id == int(request_args['galaxy_id']))
        
    # return records with id = value (API: ?id=20)
    if request_args.get('cand_id'):
        query = query.filter(sourcesRecord.cand_id == int(request_args['cand_id']))
    
    # return records with id = value (API: ?id=20)
    if request_args.get('source_id'):
        query = query.filter(sourcesRecord.id == int(request_args['source_id']))
        
    # return records with id = value (API: ?id=20)
    if request_args.get('source_name'):
        query = query.filter(sourcesRecord.name == request_args['source_name'])
    
    # return records with id = value (API: ?id=20)
    if request_args.get('source_type'):
        query = query.filter(sourcesRecord.type == request_args['source_type'])
        
    # return records with an RA >= value in degrees (API: ?ra__gte=12.0)
    if request_args.get('source_ra__gte'):
        query = query.filter(sourcesRecord.ra >= float(request_args['source_ra__gte']))

    # return records with an RA <= value in degrees (API: ?ra__lte=12.0)
    if request_args.get('source_ra__lte'):
        query = query.filter(sourcesRecord.ra <= float(request_args['source_ra__lte']))
        
    # return records with sub_id = value (API: ?sub_id=20)
    if request_args.get('sub_id'):
        query = query.filter(sourcesRecord.sub_id == int(request_args['sub_id']))
    
    # return records with sub_id = value (API: ?sub_id=20)
    if request_args.get('source_redshift'):
        query = query.filter(sourcesRecord.redshift == int(request_args['source_redshift']))
    
    # sort results
    sort_value = request_args.get('source_sort_value', SORT_VALUE[0]).lower()
    sort_order = request_args.get('source_sort_order', SORT_ORDER[0]).lower()
    if sort_order in SORT_ORDER:
        if sort_order.startswith(SORT_ORDER[0]):
            query = query.order_by(getattr(sourcesRecord, sort_value).asc())
        elif sort_order.startswith(SORT_ORDER[1]):
            query = query.order_by(getattr(sourcesRecord, sort_value).desc())

    # return query
    return query

# +
# function: candidates_filters() alphabetically
# -
# noinspection PyBroadException
def subtractions_filters(query, request_args):
    
    # return records with galaxy_id = value (API: ?galaxy_id=20)
    if request_args.get('galaxy_id'):
        query = query.filter(subtractionsRecord.galaxy_id == int(request_args['galaxy_id']))
    
    # return records with galaxy_id = value (API: ?obs_id=20)
    if request_args.get('obs_id'):
        query = query.filter(subtractionsRecord.obs_id == int(request_args['obs_id']))
    
    # return records with galaxy_id = value (API: ?ref_id=20)
    if request_args.get('ref_id'):
        query = query.filter(subtractionsRecord.ref_id == int(request_args['ref_id']))
        
    # return records with galaxy_id = value (API: ?sub_id=20)
    if request_args.get('sub_id'):
        query = query.filter(subtractionsRecord.id == int(request_args['sub_id']))
    
    # return records with galaxy_id = value (API: ?sub_id=20)
    if request_args.get('sub_version'):
        query = query.filter(subtractionsRecord.version == (request_args['sub_version']))
        
    # return records with sub_obs_date_id = value (API: ?sub_obs_date=YYYYMMDD or ?sub_obs_date=YYYYMMDD-YYYYMMDD)
    if request_args.get('sub_obs_dates'):
        mjd_min = Time(f"{request_args['sub_obs_dates'][:4]}-{request_args['sub_obs_dates'][4:6]}-{request_args['sub_obs_dates'][6:8]}", format='fits').mjd
        
        if len(request_args['sub_obs_dates']) == 8:
            mjd_max = mjd_min+1.0
        if len(request_args['sub_obs_dates']) == 17:
            mjd_max = Time(f"{request_args['sub_obs_dates'][9:13]}-{request_args['sub_obs_dates'][13:15]}-{request_args['sub_obs_dates'][15:17]}", format='fits').mjd
        
        query = query.filter(subtractionsRecord.mjdstart >= mjd_min)
        query = query.filter(subtractionsRecord.mjdstart < mjd_max)
    
    # sort results
    sort_value = request_args.get('sub_sort_value', SORT_VALUE[0]).lower()
    sort_order = request_args.get('sub_sort_order', SORT_ORDER[0]).lower()
    
    if sort_order in SORT_ORDER:
        if sort_order.startswith(SORT_ORDER[0]):
            query = query.order_by(getattr(subtractionsRecord, sort_value).asc())
        elif sort_order.startswith(SORT_ORDER[1]):
            query = query.order_by(getattr(subtractionsRecord, sort_value).desc())

    # return query
    return query


# +
# function: disparu_get_text()
# -
def disparu_get_text():
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

    # if --text is present, describe of the database
    if iargs.text:
        print(disparu_get_text())
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
