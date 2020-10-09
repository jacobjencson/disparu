#!/bin/sh


# +
#
# Name:        disparu.subtractions.sh
# Description: DISPARU subtractions control
# Author:      Jacob Jencson (jjencson@email.arizona.edu)
# Date:        20200805
# Execute:     % bash disparu.subtractions.sh --help
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
disparu_db_name="${def_db_name}"
disparu_db_pass="${def_db_pass}"
disparu_db_host="${def_db_host}"
disparu_db_user="${def_db_user}"


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
  write_blue   "DISPARU subtractions Control"                                                                       2>&1
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
      disparu_db_name=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --password*|--PASSWORD*)
      disparu_db_pass=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --username*|--USERNAME*)
      disparu_db_user=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --hostname*|--HOSTNAME*)
      disparu_db_host=$(echo $1 | cut -d'=' -f2)
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
if [[ -z ${disparu_db_name} ]]; then
  disparu_db_name=${def_db_name}
fi
if [[ -z ${disparu_db_host} ]]; then
  disparu_db_host=${def_db_host}
fi
if [[ -z ${disparu_db_pass} ]]; then
  disparu_db_pass=${def_db_pass}
fi
if [[ -z ${disparu_db_user} ]]; then
  disparu_db_user=${def_db_user}
fi


# +
# write file to create database
# -
_host=$(echo ${disparu_db_host} | cut -d':' -f1)
_port=$(echo ${disparu_db_host} | cut -d':' -f2)
PSQL_CMD="PGPASSWORD=\"${disparu_db_pass}\" psql --echo-all -h ${_host} -p ${_port} -U ${disparu_db_user} -d ${disparu_db_name}"
if [[ -f /tmp/disparu.subtractions.sh ]]; then
  rm -f /tmp/disparu.subtractions.sh
fi


# +
# create table
# -
echo "Creating /tmp/disparu.subtractions.sh"
echo "#!/bin/sh"                                                                        >> /tmp/disparu.subtractions.sh 2>&1
echo ""                                                                                 >> /tmp/disparu.subtractions.sh 2>&1
echo "${PSQL_CMD} << END_TABLE"                                                         >> /tmp/disparu.subtractions.sh 2>&1
echo "DROP TABLE IF EXISTS subtractions;"                                               >> /tmp/disparu.subtractions.sh 2>&1
echo "CREATE TABLE subtractions ("                                                      >> /tmp/disparu.subtractions.sh 2>&1
echo "  id serial PRIMARY KEY,"                                                         >> /tmp/disparu.subtractions.sh 2>&1
echo "  galaxy_id integer,"                                                             >> /tmp/disparu.subtractions.sh 2>&1
echo "  obs_id integer,"                                                                >> /tmp/disparu.subtractions.sh 2>&1
echo "  ref_id integer,"                                                                >> /tmp/disparu.subtractions.sh 2>&1
echo "  creation_date timestamp without time zone default (now() at time zone 'utc'),"  >> /tmp/disparu.subtractions.sh 2>&1
echo "  mjdstart double precision,"                                                     >> /tmp/disparu.subtractions.sh 2>&1
echo "  mjdend double precision,"                                                       >> /tmp/disparu.subtractions.sh 2>&1
echo "  exptime double precision,"                                                      >> /tmp/disparu.subtractions.sh 2>&1
echo "  tel  VARCHAR(128),"                                                             >> /tmp/disparu.subtractions.sh 2>&1
echo "  inst VARCHAR(128),"                                                             >> /tmp/disparu.subtractions.sh 2>&1
echo "  filter VARCHAR(128),"                                                           >> /tmp/disparu.subtractions.sh 2>&1
echo "  base_dir text,"                                                                 >> /tmp/disparu.subtractions.sh 2>&1  
echo "  filename text,"                                                                 >> /tmp/disparu.subtractions.sh 2>&1
echo "  version CHAR(7),"                                                               >> /tmp/disparu.subtractions.sh 2>&1
echo "  CONSTRAINT fk_galaxy"                                                           >> /tmp/disparu.subtractions.sh 2>&1
echo "    FOREIGN KEY(galaxy_id)"                                                       >> /tmp/disparu.subtractions.sh 2>&1
echo "    REFERENCES galaxies(id)"                                                      >> /tmp/disparu.subtractions.sh 2>&1
echo "    ON DELETE CASCADE,"                                                           >> /tmp/disparu.subtractions.sh 2>&1
echo "  CONSTRAINT fk_obs"                                                              >> /tmp/disparu.subtractions.sh 2>&1
echo "    FOREIGN KEY(obs_id)"                                                          >> /tmp/disparu.subtractions.sh 2>&1
echo "    REFERENCES observations(id)"                                                  >> /tmp/disparu.subtractions.sh 2>&1
echo "    ON DELETE CASCADE,"                                                           >> /tmp/disparu.subtractions.sh 2>&1
echo "  CONSTRAINT fk_ref"                                                              >> /tmp/disparu.subtractions.sh 2>&1
echo "    FOREIGN KEY(ref_id)"                                                          >> /tmp/disparu.subtractions.sh 2>&1
echo "    REFERENCES refs(id)"                                                          >> /tmp/disparu.subtractions.sh 2>&1
echo "    ON DELETE CASCADE"                                                            >> /tmp/disparu.subtractions.sh 2>&1
echo ");"                                                                               >> /tmp/disparu.subtractions.sh 2>&1
echo "END_TABLE"                                                                        >> /tmp/disparu.subtractions.sh 2>&1
echo ""                                                                                 >> /tmp/disparu.subtractions.sh 2>&1

# +
# execute
# -
_user=$(env | grep '^USER=' | cut -d'=' -f2)
write_blue "%% bash $0 --database=${disparu_db_name} --hostname=${disparu_db_host} --password=${disparu_db_pass} --username=${disparu_db_user} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  if [[ "${_user}" != "root" ]]; then
    write_red "WARNING: you need to be root to execute these commands!"
  fi
  if [[ ! -f /tmp/disparu.subtractions.sh ]]; then
    write_red "WARNING: /tmp/disparu.subtractions.sh does not exist!"
  fi
  write_yellow "Dry-Run> chmod a+x /tmp/disparu.subtractions.sh"
  write_yellow "Dry-Run> bash /tmp/disparu.subtractions.sh"
  write_yellow "Dry-Run> rm -f /tmp/disparu.subtractions.sh"

else
  if [[ "${_user}" != "root" ]]; then
    write_red "ERROR: you need to be root to execute these commands!"
    usage
    exit
  fi
  if [[ ! -f /tmp/disparu.subtractions.sh ]]; then
    write_red "ERROR: /tmp/disparu.subtractions.sh does not exist!"
    usage
    exit
  fi
  write_green "Executing> chmod a+x /tmp/disparu.subtractions.sh"
  chmod a+x /tmp/disparu.subtractions.sh
  write_green "Executing> bash /tmp/disparu.subtractions.sh"
  bash /tmp/disparu.subtractions.sh
  write_green "Executing> rm -f /tmp/disparu.subtractions.sh"
  rm -f /tmp/disparu.subtractions.sh
fi


# +
# exit
# -
exit 0
