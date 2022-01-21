#!/bin/sh


# +
# edit as you see fit
# -
_user=$(env | grep USERNAME | cut -d'=' -f2)
if [[ -z "${_user}" ]]; then
  export USERNAME="disparu"
fi

export DISPARU_HOME=${1:-/var/www/disparu}
export DISPARU_TYPE=${2:-""}

case ${DISPARU_TYPE} in
  dev*|DEV*)
    export DISPARU_APP_HOST=localhost
    export DISPARU_APP_PORT=5000
    export DISPARU_APP_URL="http://${DISPARU_APP_HOST}:${DISPARU_APP_PORT}/disparu"
    export DISPARU_DB_HOST=localhost
    ;;
  prod*|PROD*)
    export DISPARU_APP_HOST=$(hostname)
    export DISPARU_APP_PORT=6000
    export DISPARU_APP_URL="http://${DISPARU_APP_HOST}:${DISPARU_APP_PORT}/disparu"
    export DISPARU_DB_HOST=$(hostname)
    ;;
  *)
    export DISPARU_APP_HOST="sassy.as.arizona.edu"
    export DISPARU_APP_PORT=80
    export DISPARU_APP_URL="https://${DISPARU_APP_HOST}/disparu"
    export DISPARU_DB_HOST="localhost"
    ;;
esac


export DISPARU_DB_PORT=5435
export DISPARU_DB_NAME="disparu"
export DISPARU_DB_USER="disparu"
export DISPARU_DB_PASS="D1sparu_520"


# +
# env(s)
# -
export DISPARU_BIN=${DISPARU_HOME}/bin
export DISPARU_ETC=${DISPARU_HOME}/etc
export DISPARU_LOGS=${DISPARU_HOME}/logs
export DISPARU_SRC=${DISPARU_HOME}/dsrc

# +
# data path(s)
# -
#export DISPARU_DATA=/dataraid6/disparu:/dataraid0/disparu
#export DISPARU_DATA=/dataraid6/disparu
#export DISPARU_DATA=/dataraid0/disparu 

export DISPARU_DATA=/opt/pgdata/files

# +
# PYTHONPATH
# -
export PYTHONPATH=${DISPARU_HOME}:${DISPARU_SRC}

# +
# update ephemeris
# -
# python3 -c 'from dsrc import *; get_iers()'
