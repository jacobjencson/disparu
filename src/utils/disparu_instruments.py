#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.io import fits
import argparse
import math
import os
import sys

DISPARU_DB_HOST = os.getenv('DISPARU_DB_HOST', None)
DISPARU_DB_USER = os.getenv('DISPARU_DB_USER', None)
DISPARU_DB_PASS = os.getenv('DISPARU_DB_PASS', None)
DISPARU_DB_NAME = os.getenv('DISPARU_DB_NAME', None)
DISPARU_DB_PORT = os.getenv('DISPARU_DB_PORT', None)

# +
# class ACS_utils
# -
class ACS_utils:
    "Class for handling ACS images."
    # +
    # constant(s)
    # -
    ACS_HDR_FORMAT = {
        'targname': 'TARGNAME',
        'mjdstart': 'EXPSTART',
        'mjdend':   'EXPEND',
        'exptime':  'EXPTIME',
        'tel':      'TELESCOP',
        'inst':     'INSTRUME',
        'filter1':  'FILTER1',
        'filter2':  'FILTER2',
    }

    # +
    # function: get_ACS_img_info()
    # -
    def get_ACS_img_info(self, _file):
        """
        Reads in an ACS reference image and returns 
        info to load into database.
    
        Parameters:
            _file (str): the input fits file.
        Returns:
            _this_result (dict): header info. 
    
        """
        
        # get results
        _hdu_list = fits.open(_file)
        _pri_hdr = _hdu_list[0].header
        _this_result = {}
        for _l in self.ACS_HDR_FORMAT:
            _key = self.ACS_HDR_FORMAT[_l]
            _value = _pri_hdr[_key]
            _this_result[_l] = _value
        
        return _this_result
        
    def get_ACS_filter_name(_filter1, _filter2):
        """
        Takes ACS filter1 and filter2 names
        and outputs one filter name.
    
        Parameters:
            filter1 (str): Header value for FILTER1
            filter2 (str): Header value for FILTER2
        Returns:
            filt (str): single string for filter 
    
        """
        
        if _filter1[:5] == 'CLEAR':
            _filter = _filter2.strip()
        elif filter2[:5] == 'CLEAR':
            _filter = _filter1.strip()
        else:
            _filter = f'{filter1.strip()}/{filter2.strip()}'
        
        return _filter

# +
# class WFC3_utils
# -       
class WFC3_UVIS_utils:
    "Class for handling WFC3_UVIS images"
    # +
    # constant(s)
    # -
    WFC3_HDR_FORMAT = {
        'targname': 'TARGNAME',
        'mjdstart': 'EXPSTART',
        'mjdend':   'EXPEND',
        'exptime':  'EXPTIME',
        'tel':      'TELESCOP',
        'inst':     'INSTRUME',
        'detector': 'DETECTOR',
        'filter':   'FILTER',
    }

    # +
    # function: get_ACS_img_info()
    # -
    def get_WFC3_UVIS_img_info(self, _file):
        """
        Reads in an WFC3 UVIS image and returns 
        info to load into database.
    
        Parameters:
            _file (str): the input fits file.
        Returns:
            _this_result (dict): header info. 
    
        """
        
        # get results
        _hdu_list = fits.open(_file)
        _pri_hdr = _hdu_list[0].header
        _this_result = {}
        for _l in self.WFC3_HDR_FORMAT:
            _key = self.WFC3_HDR_FORMAT[_l]
            _value = _pri_hdr[_key]
            _this_result[_l] = _value
        
        return _this_result
