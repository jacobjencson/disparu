#!/bin/sh


# +
#
# Name:        disparu.database.sh
# Description: Disparu Database Control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190415
# Execute:     % bash disparu.database.sh --help
#
# -


# +
# default(s) - edit as required
# -
def_db_name="disparu"
def_db_pass="db_secret"
def_db_host="localhost:5432"
def_db_user="disparu"

dry_run=0


# +
# variable(s)
# -
db_name="${def_db_name}"
db_pass="${def_db_pass}"
db_host="${def_db_host}"
db_user="${def_db_user}"


# +
# utility functions
# -
write_blue () {
  BLUE='\033[0;34m'
  NCOL='\033[0m'
  printf "${BLUE}${1}${NCOL}\n"
}
write_red () {
  RED='\033[0;31m'
  NCOL='\033[0m'
  printf "${RED}${1}${NCOL}\n"
}
write_yellow () {
  YELLOW='\033[0;33m'
  NCOL='\033[0m'
  printf "${YELLOW}${1}${NCOL}\n"
}
write_green () {
  GREEN='\033[0;32m'
  NCOL='\033[0m'
  printf "${GREEN}${1}${NCOL}\n"
}
write_cyan () {
  CYAN='\033[0;36m'
  NCOL='\033[0m'
  printf "${CYAN}${1}${NCOL}\n"
}
usage () {
  write_blue   ""                                                                                                 2>&1
  write_blue   "Database Control"                                                                                 2>&1
  write_blue   ""                                                                                                 2>&1
  write_green  "Use:"                                                                                             2>&1
  write_green  "  %% bash $0 --database=<str> --hostname=<str:int> --password=<str> --username=<str> [--dry-run]" 2>&1
  write_yellow ""                                                                                                 2>&1
  write_yellow "Input(s):"                                                                                        2>&1
  write_yellow "  --database=<str>,      where <str> is the database name,               default=${def_db_name}"  2>&1
  write_yellow "  --hostname=<str:int>,  where <str> is the database hostname and port,  default=${def_db_host}"  2>&1
  write_yellow "  --password=<str>,      where <str> is the database password,           default=${def_db_pass}"  2>&1
  write_yellow "  --username=<str>,      where <str> is the database username,           default=${def_db_user}"  2>&1
  write_yellow ""                                                                                                 2>&1
  write_cyan   "Flag(s):"                                                                                         2>&1
  write_cyan   "  --dry-run,             show (but do not execute) commands,             default=false"           2>&1
  write_cyan   ""                                                                                                 2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --database*|--DATABASE*)
      db_name=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --password*|--PASSWORD*)
      db_pass=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --username*|--USERNAME*)
      db_user=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --hostname*|--HOSTNAME*)
      db_host=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --help|*)
      usage
      exit 0
      ;;
  esac
done


# +
# check and (re)set variable(s)
# -
if [[ -z ${db_name} ]]; then
  db_name=${def_db_name}
fi
if [[ -z ${db_host} ]]; then
  db_host=${def_db_host}
fi
if [[ -z ${db_pass} ]]; then
  db_pass=${def_db_pass}
fi
if [[ -z ${db_user} ]]; then
  db_user=${def_db_user}
fi


# +
# write file to create database
# -
_host=$(echo ${db_host} | cut -d':' -f1)
_port=$(echo ${db_host} | cut -d':' -f2)
_os=`echo $(uname -sr) | cut -d' ' -f1`

if [[ "${_os}" == "Darwin" ]]; then
  PSQL_CMD="psql --echo-all -h ${_host} -p ${_port}"
else
  PSQL_CMD="sudo -u postgres psql --echo-all -h ${_host} -p ${_port}"
fi

if [[ -f /tmp/${db_name}.database.sh ]]; then
  rm -f /tmp/${db_name}.database.sh
fi

echo "#!/bin/sh"                                                                         >> /tmp/${db_name}.database.sh 2>&1
echo "${PSQL_CMD} << EOF"                                                                >> /tmp/${db_name}.database.sh 2>&1
echo "DROP DATABASE IF EXISTS ${db_name};"                                               >> /tmp/${db_name}.database.sh 2>&1
echo "DROP USER IF EXISTS ${db_user};"                                                   >> /tmp/${db_name}.database.sh 2>&1
echo "CREATE ROLE ${db_user} LOGIN SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS;" >> /tmp/${db_name}.database.sh 2>&1
echo "ALTER ROLE ${db_user} WITH ENCRYPTED PASSWORD '${db_pass}';"                       >> /tmp/${db_name}.database.sh 2>&1
echo "CREATE DATABASE ${db_name};"                                                       >> /tmp/${db_name}.database.sh 2>&1
echo "CREATE EXTENSION postgis;"                                                         >> /tmp/${db_name}.database.sh 2>&1
echo "CREATE EXTENSION postgis_topology;"                                                >> /tmp/${db_name}.database.sh 2>&1
echo "CREATE EXTENSION q3c;"                                                             >> /tmp/${db_name}.database.sh 2>&1
echo "GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${db_user};"                        >> /tmp/${db_name}.database.sh 2>&1
echo "ALTER DATABASE ${db_name} OWNER TO ${db_user};"                                    >> /tmp/${db_name}.database.sh 2>&1
echo "EOF"                                                                               >> /tmp/${db_name}.database.sh 2>&1



# +
# execute
# -
_user=$(env | grep '^USER=' | cut -d'=' -f2)
write_blue "%% bash $0 --database=${db_name} --hostname=${db_host} --password=${db_pass} --username=${db_user} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  if [[ "${_user}" != "root" ]]; then
    write_red "WARNING: you need to be root to execute these commands!"
  fi
  if [[ ! -f /tmp/${db_name}.database.sh ]]; then
    write_red "WARNING: /tmp/${db_name}.database.sh does not exist!"
  fi
  write_yellow "Dry-Run> chmod a+x /tmp/${db_name}.database.sh"
  write_yellow "Dry-Run> bash /tmp/${db_name}.database.sh"
  write_yellow "Dry-Run> rm -f /tmp/${db_name}.database.sh"

else
  if [[ "${_user}" != "root" ]]; then
    write_red "ERROR: you need to be root to execute these commands!"
    usage
    exit
  fi
  if [[ ! -f /tmp/${db_name}.database.sh ]]; then
    write_red "ERROR: /tmp/${db_name}.database.sh does not exist!"
    usage
    exit
  fi
  write_green "Executing> chmod a+x /tmp/${db_name}.database.sh"
  chmod a+x /tmp/${db_name}.database.sh
  write_green "Executing> bash /tmp/${db_name}.database.sh"
  bash /tmp/${db_name}.database.sh
  write_green "Executing> rm -f /tmp/${db_name}.database.sh"
  rm -f /tmp/${db_name}.database.sh
fi


# +
# exit
# -
exit 0
