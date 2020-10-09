#!/usr/bin/env python3

# +
# import(s)
# -
from astropy.time import Time
from datetime import datetime
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import FloatField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import NumberRange
from wtforms.validators import Regexp

import re
import math

# +
# constant(s)
# -
SOURCE_TYPES = [('', 'Auto'), ('VarStar', 'VarStar'), ('DispStar', 'DispStar'), ('Transient', 'Transient'), ('Junk', 'Junk')]

# +
# class: MMTLongslitForm(), inherits from FlaskForm
# -
class CandidateSaveForm(FlaskForm):
    
    # fields
    s_type = SelectField('Catalog', choices=SOURCE_TYPES, default=SOURCE_TYPES[0][0], validators=[DataRequired()])

    # submit
    submit = SubmitField('Save Candidate')

