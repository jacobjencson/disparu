#!/bin/sh


# +
#
# Name:        Disparu.sh
# Description: Disparu control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash Disparu.sh --help
#
# -


# +
# default(s)
# -
_disparu_home=$(env | grep '^DISPARU_HOME=' | cut -d'=' -f2)
def_disparu_command="status"
def_disparu_source="${_disparu_home}"
def_disparu_type="dev"

def_dev_host="localhost"
def_dev_port=5000
def_prd_host="localhost"
def_prd_port=6000

dry_run=0


# +
# variable(s)
# -
disparu_command="${def_disparu_command}"
disparu_source="${def_disparu_source}"
disparu_type="${def_disparu_type}"

disparu_port=${def_dev_port}
disparu_host="${def_dev_host}"


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
  write_blue   ""                                                                                                  2>&1
  write_blue   "Disparu Control"                                                                                   2>&1
  write_blue   ""                                                                                                  2>&1
  write_green  "Use:"                                                                                              2>&1
  write_green  "  %% bash $0 --command=<str> --source=<str> --type=<str> [--dry-run]"                              2>&1
  write_yellow ""                                                                                                  2>&1
  write_yellow "Input(s):"                                                                                         2>&1
  write_yellow "  --command=<str>,  where <str> is { 'start', 'status', 'stop' },  default=${def_disparu_command}" 2>&1
  write_yellow "  --source=<str>,   where <str> is source code directory,          default=${def_disparu_source}"  2>&1
  write_yellow "  --type=<str>,     where <str> is { 'dev', 'prod' }               default=${def_disparu_type}"    2>&1
  write_yellow ""                                                                                                  2>&1
  write_cyan   "Flag(s):"                                                                                          2>&1
  write_cyan   " --dry-run,         show (but do not execute) commands,            default=false"                  2>&1
  write_cyan   ""                                                                                                  2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --command*|--COMMAND*)
      disparu_command=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --source*|--SOURCE*)
      disparu_source=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --type*|--TYPE*)
      disparu_type=$(echo $1 | cut -d'=' -f2)
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
case $(echo ${disparu_command} | tr '[A-Z]' '[a-z]') in
  start*|status*|stop*)
    ;;
  *)
    disparu_command=${def_disparu_command}
    ;;
esac


if [[ ! -d ${disparu_source} ]]; then
  write_red "<ERROR> directory (${disparu_source}) is unknown ... exiting"
  exit 0 
fi


case $(echo ${disparu_type} | tr '[A-Z]' '[a-z]') in
  prod*)
    disparu_type="production"
    disparu_host=$(getent hosts ${def_prd_host} | cut -d' ' -f1)
    disparu_port=${def_prd_port}
    ;;
  *)
    disparu_type="development"
    disparu_host="${def_dev_host}"
    disparu_port=${def_dev_port}
    ;;
esac


if [[ ${disparu_host} != "localhost" ]]; then
  if ! ping -c 1 -w 5 ${disparu_host} &>/dev/null; then
    write_red "<ERROR> server (${disparu_host}) is down ... exiting"
    exit 0
  fi
fi


# +
# env(s)
# -
_pythonpath=$(env | grep PYTHONPATH | cut -d'=' -f2)
if [[ -z "${_pythonpath}" ]]; then
  export PYTHONPATH=`pwd`
fi
write_blue "%% source ${disparu_source}/etc/Disparu.sh ${disparu_source} ${disparu_type}"
source ${disparu_source}/etc/Disparu.sh ${disparu_source} ${disparu_type}


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --command=${disparu_command} --dry-run=${dry_run} --source=${disparu_source} --type=${disparu_type}"
case $(echo ${disparu_command} | tr '[A-Z]' '[a-z]') in
  start*)
    if [[ ${dry_run} -eq 1 ]]; then
      if [[ "${disparu_type}" == "development" ]]; then
        write_yellow "Dry-Run> FLASK_DEBUG=True  FLASK_ENV=Development FLASK_APP=${disparu_source}/src/disparu.py flask run"
      elif [[ "${disparu_type}" == "production" ]]; then
        write_yellow "Dry-Run> FLASK_DEBUG=False FLASK_ENV=Production  FLASK_APP=${disparu_source}/src/disparu.py flask run -h ${disparu_host} -p ${disparu_port}"
      fi
    else
      if [[ "${disparu_type}" == "development" ]]; then
        write_green "Executing> FLASK_DEBUG=True  FLASK_ENV=Development FLASK_APP=${disparu_source}/src/disparu.py flask run"
        FLASK_DEBUG=True  FLASK_ENV=Development FLASK_APP=${disparu_source}/src/disparu.py flask run
      elif [[ "${disparu_type}" == "production" ]]; then
        write_green "Executing> FLASK_DEBUG=False FLASK_ENV=Production  FLASK_APP=${disparu_source}/src/disparu.py flask run -h ${disparu_host} -p ${disparu_port}"
        FLASK_DEBUG=False FLASK_ENV=Production  FLASK_APP=${disparu_source}/src/disparu.py flask run -h ${disparu_host} -p ${disparu_port}
      fi
    fi
    ;;

  stop*)
    _pid=$(ps -ef | pgrep -f 'python' | pgrep  -f flask)
    if [[ ! -z "${_pid}" ]]; then
      if [[ ${dry_run} -eq 1 ]]; then
        write_yellow "Dry-Run> kill -9 ${_pid}"
      else
        write_green "Executing> kill -9 ${_pid}"
        kill -9 ${_pid}
      fi
    fi
    ;;

  status*)
      if [[ ${dry_run} -eq 1 ]]; then
        write_yellow "Dry-Run> ps -ef | grep -i python | grep -i flask"
      else
        write_green "Executing> ps -ef | grep -i python | grep -i flask"
        ps -ef | grep -i python | grep -i flask
      fi
    ;;
esac


# +
# exit
# -
exit 0
