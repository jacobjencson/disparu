#!/usr/bin/env python3.7


# +
# import(s)
# -
from src import *
from src.disparu_common import *
from src.utils import *
from src.utils.candidates_save import get_source_type, get_candidate_type

import numpy as np
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import send_file
from flask import send_from_directory
from sqlalchemy import desc
from urllib.parse import urlencode

from src.models.disparu import db as db_disparu
from src.models.disparu import candidatesRecord
from src.models.disparu import subtractionsRecord
from src.models.disparu import observationsRecord
from src.models.disparu import refsRecord
from src.models.disparu import galaxiesRecord
from src.models.disparu import sourcesRecord

from src.models.disparu import galaxies_filters
from src.models.disparu import candidates_filters
from src.models.disparu import subtractions_filters

ARIZONA = pytz.timezone('America/Phoenix')
PSQL_CONNECT_MSG = f'{DISPARU_DB_HOST}:{DISPARU_DB_PORT}/{DISPARU_DB_NAME} using {DISPARU_DB_USER}:{DISPARU_DB_PASS}'
RESULTS_PER_PAGE = 200

SOURCE_MATCH_RADIUS = 0.05
SOURCE_TYPES = ['VarStar', 'Transient', 'DispStar', 'Junk']

# +
# logging
# -
logger = Logger('Disparu').logger

logger.debug(f"DISPARU_APP_HOST = {DISPARU_APP_HOST}")
logger.debug(f"DISPARU_APP_PORT = {DISPARU_APP_PORT}")
logger.debug(f"DISPARU_APP_URL = {DISPARU_APP_URL}")
logger.debug(f"DISPARU_BIN = {DISPARU_BIN}")
logger.debug(f"DISPARU_DATA = {DISPARU_DATA}")
logger.debug(f"DISPARU_DB_HOST = {DISPARU_DB_HOST}")
logger.debug(f"DISPARU_DB_NAME = {DISPARU_DB_NAME}")
logger.debug(f"DISPARU_DB_PASS = {DISPARU_DB_PASS}")
logger.debug(f"DISPARU_DB_PORT = {DISPARU_DB_PORT}")
logger.debug(f"DISPARU_DB_USER = {DISPARU_DB_USER}")
logger.debug(f"DISPARU_ETC = {DISPARU_ETC}")
logger.debug(f"DISPARU_HOME = {DISPARU_HOME}")
logger.debug(f"DISPARU_LOGS = {DISPARU_LOGS}")
logger.debug(f"DISPARU_SRC = {DISPARU_SRC}")
logger.debug(f"DISPARU_TYPE = {DISPARU_TYPE}")
logger.debug(f"PYTHONPATH = {PYTHONPATH}")


# +
# initialize
# -
app = Flask(__name__)
try:
    app.config['SECRET_KEY'] = DISPARU_SECRET_KEY
except:
    app.config['SECRET_KEY'] = hashlib.sha256(get_isot().encode('utf-8')).hexdigest()
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f'postgresql+psycopg2://{DISPARU_DB_USER}:{DISPARU_DB_PASS}@{DISPARU_DB_HOST}:{DISPARU_DB_PORT}/{DISPARU_DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# +
# initialize sqlalchemy
# -
with app.app_context():
    db_disparu.init_app(app)
    
# +
# (hidden) function: _request_wants_json()
# -
def _request_wants_json():
    if request.args.get('format', 'html', type=str) == 'json':
        return True
    else:
        best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
        return best == 'application/json' and \
            request.accept_mimetypes[best] > \
            request.accept_mimetypes['text/html']

# +
# route(s): /, /disparu
# -
#@app.route('/disparu/disparu/')
@app.route('/disparu/')
@app.route('/disparu/disparu.html')
#@app.route('/')
def disparu():
    return render_template('disparu.html', url={'url': f'{DISPARU_APP_URL}', 'page': '/disparu'})

    
# +
# route(s): /, /disparu/candidates.html
# -
@app.route('/disparu/candidates/', methods=["GET", "POST"])
def candidates():
    logger.debug(f'route /disparu/candidates entry')
    
    # report where request is coming from
    forwarded_ips = request.headers.getlist('X-Forwarded-For')
    client_ip = forwarded_ips[0].split(',')[0] if len(forwarded_ips) >= 1 else ''
    logger.info('incoming request', extra={'tags': {'requesting_ip': client_ip, 'request_args': request.args}})
    page = request.args.get('page', 1, type=int)
    response = {}
    
    # set default(s)
    latest = None
    paginator = None
    _args = request.args.copy()
    if 'sort_order' not in _args:
        _args['sort_order'] = 'ascending'
    if 'sort_value' not in _args:
        _args['sort_value'] = 'id'
        
    # GET request
    if request.method == 'GET':
        #need a list of all galaxies
        all_galaxies = db_disparu.session.query(galaxiesRecord).order_by(galaxiesRecord.name)
        _all_galaxies_results = galaxiesRecord.serialize_list(all_galaxies)
        
        #get subtraction dates
        gal_subs = db_disparu.session.query(subtractionsRecord, galaxiesRecord).filter(subtractionsRecord.galaxy_id==galaxiesRecord.id).order_by(subtractionsRecord.mjdstart).distinct(subtractionsRecord.mjdstart)
        gal_subs = galaxies_filters(gal_subs, _args)
        _gal_subs_results = subtractionsRecord.serialize_list([row[0] for row in gal_subs.all()])
        _gal_sub_dates = [Time(_this_sub_dict['mjdstart'], format='mjd').fits[:10].replace('-','') for _this_sub_dict in _gal_subs_results]
        
        sub_versions = db_disparu.session.query(subtractionsRecord, galaxiesRecord).filter(subtractionsRecord.galaxy_id==galaxiesRecord.id).order_by(desc(subtractionsRecord.version))
        sub_versions = galaxies_filters(sub_versions, _args)
        _sub_versions_results = subtractionsRecord.serialize_list([row[0] for row in sub_versions.all()])
        
        #query all the tables, I think this is ok. 
        query = db_disparu.session.query(candidatesRecord, subtractionsRecord, galaxiesRecord).filter(candidatesRecord.sub_id == subtractionsRecord.id, 
                                                                                                      candidatesRecord.galaxy_id == galaxiesRecord.id)
        query = galaxies_filters(query, _args)
        query = subtractions_filters(query, _args)
        query = candidates_filters(query, _args)
        paginator = query.paginate(page, RESULTS_PER_PAGE, True)
    
        _c_results = candidatesRecord.serialize_list([row[0] for row in paginator.items])
        _s_results = subtractionsRecord.serialize_list([row[1] for row in paginator.items])
        _g_results = subtractionsRecord.serialize_list([row[2] for row in paginator.items])
        
        #determine source types:
        
        #get the thumbnails, default candidate types, and any matching sources. 
        _s_types = [None] * len(_c_results)
        _thumbnails = [None] * len(_c_results)
        _s_matches = [None] * len(_c_results)
        for i in range(len(_c_results)):
            _xpos_int = int(_c_results[i]['xpos'])
            _ypos_int = int(_c_results[i]['ypos'])
            _this_id = int(_c_results[i]['id'])
            _this_tn = (f"scithumb_x{_xpos_int}_y{_ypos_int}_id{_this_id}.png", 
                        f"refthumb_x{_xpos_int}_y{_ypos_int}_id{_this_id}.png",
                        f"diffthumb_x{_xpos_int}_y{_ypos_int}_id{_this_id}.png")
            _thumbnails[i] = _this_tn
            
            _s_types[i] = get_candidate_type(_c_results[i])
            
            _c_coord = SkyCoord(ra=_c_results[i]['ra']*u.degree, dec=_c_results[i]['dec']*u.degree)
            _g_s_query = db_disparu.session.query(sourcesRecord).filter(sourcesRecord.galaxy_id==_c_results[i]['galaxy_id'])
            _g_s_results = sourcesRecord.serialize_list([row for row in _g_s_query.all()])
            _g_s_ra = np.array([_g_source['ra'] for _g_source in _g_s_results])
            _g_s_dec = np.array([_g_source['dec'] for _g_source in _g_s_results])
            _g_s_coord = SkyCoord(ra=_g_s_ra*u.degree, dec=_g_s_dec*u.degree)
            _g_s_matches = np.where(_g_s_coord.separation(_c_coord) <= SOURCE_MATCH_RADIUS*u.arcsec)[0]
            if len(_g_s_matches) > 0:
                _s_match_names = [None]*len(_g_s_matches)
                for j in range(len(_g_s_matches)):
                    match_ix = _g_s_matches[j]
                    _s_match_names[j] = _g_s_results[match_ix]['name']
            else:
                _s_match_names = ['']
            _s_matches[i] = _s_match_names
        
        # set response dictionary
        response = {
            'all_galaxies': _all_galaxies_results,
            'gal_sub_dates': _gal_sub_dates,
            'sub_versions': _sub_versions_results,
            'total': paginator.total,
            'pages': paginator.pages,
            'has_next': paginator.has_next,
            'has_prev': paginator.has_prev,
            'sub_results': _s_results,
            'results': _c_results,
            'thumbnails': _thumbnails,
            's_types': _s_types,
            'type_options': SOURCE_TYPES,
            's_matches': _s_matches
        }
    
    # POST request
    if request.method == 'POST':

        # get search criteria
        searches = request.get_json().get('queries')

        # initialize output(s)
        search_results = []
        total = 0

        # iterate over searches
        for search_args in searches:

            # initialize result(s)
            search_result = {}

            # query database
            query = db_disparu.session.query(candidatesRecord)
            query = candidates_filters(query, search_args)

            # extract,transform and load (ETL) into result(s)
            search_result['query'] = search_args
            search_result['num_alerts'] = query.count()
            search_result['results'] = candidatesRecord.serialize_list(query.all())
            search_results.append(search_result)
            total += search_result['num_alerts']

        # set response dictionary
        response = {
            'total': total,
            'results': search_results
        }
    
    # return response in desired format
    if _request_wants_json() or request.method == 'POST':
        return jsonify(response)
    else:
        _args = request.args.copy()
        try:
            _args.pop('page')
        except:
            pass
        arg_str = urlencode(_args)
        return render_template('candidates.html', context=response, page=paginator.page, arg_str=arg_str, latest=latest,
                               url={'url': f'{DISPARU_APP_URL}', 'page': 'candidates'})

# +
# route(s): /, /disparu/candidates/save
# -
@app.route('/disparu/candidates/save/<int:id>')
#@app.route('/disparu/candidates/save/<int:id>/<string:s_type>')
def save_candidate(id=0, methods=["GET"]):
    # get record from original table
    _args = request.args.copy()
    if 'source_type' not in _args:
        s_type = ''
    else:
        s_type = _args['source_type']
    
    _c_query = db_disparu.session.query(candidatesRecord).filter(candidatesRecord.id==id).first_or_404()

    #check if a matching sorce already exists
    _c_coord = SkyCoord(ra=_c_query.ra*u.degree, dec=_c_query.dec*u.degree)
    
    _g_s_query = db_disparu.session.query(sourcesRecord).filter(sourcesRecord.galaxy_id==_c_query.galaxy_id)
    _g_s_results = sourcesRecord.serialize_list([row for row in _g_s_query.all()])
    _g_s_ra = np.array([_g_source['ra'] for _g_source in _g_s_results])
    _g_s_dec = np.array([_g_source['dec'] for _g_source in _g_s_results])
    _g_s_coord = SkyCoord(ra=_g_s_ra*u.degree, dec=_g_s_dec*u.degree)
    _g_s_matches = np.where(_g_s_coord.separation(_c_coord) <= SOURCE_MATCH_RADIUS*u.arcsec)[0]
    
    if len(_g_s_matches) > 0:
        _message = f"Found {len(_g_s_matches)} matching source(s) in database: "
        for match_ix in _g_s_matches:
            _message+=f"{_g_s_results[match_ix]['name']}, "
        _message+=f"candidate {id} not saved as new source."
        return render_template('candidate_save.html', context=_message, url={'url': f'{DISPARU_APP_URL}', 'page': 'candidates/save'})
    
    else:
        #name the source
        _g_query = db_disparu.session.query(galaxiesRecord).filter(galaxiesRecord.id==_c_query.galaxy_id).first()
        _g_name = _g_query.name
        _g_s_query = db_disparu.session.query(sourcesRecord).filter(sourcesRecord.galaxy_id==_c_query.galaxy_id).all()
        _g_s_num = len(_g_s_query) + 1
        _s_name = f"{_g_name}_DS{_g_s_num}"
    
        if s_type != '':
            if s_type in SOURCE_TYPES:
                s_type = s_type
            else:
                s_type = get_source_type(_c_query)
        else:
            s_type = get_source_type(_c_query)
        
        _source = sourcesRecord(
                    sub_id = _c_query.sub_id,
                    cand_id = _c_query.id,
                    galaxy_id = _c_query.galaxy_id,
                    name = _s_name,
                    ra = _c_query.ra,
                    dec = _c_query.dec,
                    type = s_type,
                    redshift = _g_query.redshift
        )
                    
        #save the source
        try:
            db_disparu.session.add(_source)
            db_disparu.session.commit()
            _message = f"Successfully saved candidate {id} to database as {_s_name} with type {s_type}."
            return render_template('candidate_save.html', context=_message, url={'url': f'{DISPARU_APP_URL}', 'page': 'candidates/save'})
            
        except Exception as e:
            db_disparu.session.rollback()
            _message = f"Failed to save candidate {id} to database as {_s_name}, error={e}"
            return render_template('candidate_save.html', context=_message, url={'url': f'{DISPARU_APP_URL}', 'page': 'candidates/save'})
                               
# +
# main()
# -
if __name__ == '__main__':
    app.run(host=os.getenv("DISPARU_APP_HOST"), port=int(os.getenv("DISPARU_APP_PORT")), threaded=True, debug=False)

# DISPARU_SRC=/Users/pnd/PycharmProjects/Disparu/src
# DISPARU_DB_PASS=D1sparu_520
# DISPARU_DB_HOST=localhost
# DISPARU_DATA=/System/Volumes/Data/dataraid6/ztf:/dataraid6/ztf:/dataraid0/ztf
# DISPARU_LOGS=/Users/pnd/PycharmProjects/Disparu/logs
# DISPARU_HOME=/Users/pnd/PycharmProjects/Disparu
# DISPARU_ETC=/Users/pnd/PycharmProjects/Disparu/etc
# DISPARU_APP_URL=http://localhost:5000/disparu
# DISPARU_DB_USER=disparu
# DISPARU_DB_NAME=disparu
# DISPARU_BIN=/Users/pnd/PycharmProjects/Disparu/bin
# DISPARU_DB_PORT=5432
# DISPARU_APP_HOST=localhost
# DISPARU_TYPE=dev
# DISPARU_APP_PORT=5000
