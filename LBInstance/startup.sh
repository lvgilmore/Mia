#!/usr/bin/env bash

uid=`hostname`
default_interface=`ip -4 route show | grep default | sed 's/^.*\sdev\s\([^ ]*\)\s.*$/\1/'`
my_ip=`ip -4 addr show ${default_interface} | grep -e "^\s*inet\s" | sed 's/^\s*inet\s\([0-9\.]*\)\/.*/\1/'`

MIALBURI=$(echo ${MIALBURI} | sed 's@\([^:]\)//@\1/@g ; s@/$@@')

curl "${MIALBURI}/configs/${FARMID}.conf" -o /etc/nginx/conf.d/${FARMID}.conf
external_ip=$(grep -e "^[^\#]*proxy_pass " /etc/nginx/conf.d/${FARMID}.conf | \
  sed 's/^.*proxy_pass \([0-9\.]*\)[: \s;].*$/\1/')
curl -H "Content-Type: text/plain" -H "Client-IP: ${my_ip}" -X POST \
  -d '{"docker_uid": "'${uid}'"}' "${MIALBURI}/MiaLB/farms/${FARMID}/instances"

flag=1
for i in {1..5}
do
    echo "`ip addr show eth1 2> /dev/null; echo $?`"
    if [ "0" == "`ip addr show eth1 > /dev/null 2>&1 ; echo $?`" ]
    then
        flag=0
        break
    else
        sleep 5
    fi
done
if [ $flag -eq 0 ]
then
    nginx -g "daemon off;"
    while [ $flag -eq 0 ]
    do
        ps -ef | grep -v grep | grep -q nginx || flag=1
        sleep 5
    done
else
    logger -s -p daemon.err "couldnt find eth1 after 25 seconds. aborting"
    exit 1
fi
