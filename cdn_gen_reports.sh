#! /bin/bash

. ~/bin/cdnrc

date=$(date "+%H%M%y")

echo "Generating duplicates report"
cdn_report.py --duplicates --reverse --ownerid ${ownerid} --user ${user} --password ${password} > /tmp/cdn_dups_${date}

echo "Generating checkin report"
cdn_report.py --ownerid ${ownerid} --user ${user} --password ${password} --checkin --days 30 > /tmp/cdn_30_${date}

