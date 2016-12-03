#!/usr/bin/env bash

uid=`hostname`
curl "${MIALBURI}/instance?uid=${uid}&farmid=${FARMID}"
curl "${MIALBURI}/${FARMID}.conf"
flag=1
for i in {1..5}
do
    if ip addr show eth1 2> /dev/null
    then
        flag=0
        break
    else
        sleep 5
    fi
done
if flag
then
    nginx
    while flag
    do
        ps -ef | grep -v grep | grep -q nginx || flag=1
        sleep 5
    done
else
    logger -s -p daemon.err "couldnt find eth1 after 25 seconds. aborting"
fi