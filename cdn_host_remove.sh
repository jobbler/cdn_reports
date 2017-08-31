#! /bin/bash

declare -A options

while getopts ":f:u:p:h" opt
do
  case ${opt} in
    u) options[user]=$OPTARG
       ;;
    p) options[password]=$OPTARG
       ;;
    f) options[file]=$OPTARG
       ;;
    h) echo -e "usage: $0 [options]"
       echo -e "\t -f \tFile that contains list of system uuids to remove."
       echo -e "\t -u \tCDN User name"
       echo -e "\t -p \tCDN User password"
       echo -e "\n\t Example usages:"
       echo -e "\n\t Enter the hosts to remove"
       echo -e "\t\t cdn_host_remove.sh -u USER -p PASSWORD"
       echo -e "\n\t Remove the hosts in /tmp/remove_list.txt"
       echo -e "\t\t cdn_host_remove.sh -u USER -p PASSWORD -f /tmp/remove_list.txt"
       echo -e "\n\t Remove the hosts in /tmp/remove_list.txt"
       echo -e "\t\t cat /tmp/remove_list.txt | cdn_host_remove.sh -u USER -p PASSWORD"
       echo -e "\n\t Remove hosts that have not checked in within the last 90 days"
       echo -e "\t\t cdn_report.py --user \${user} --password \${password} --checkin --ownerid \${ownerid} --days 90 --silent \\"
       echo -e "\t\t   | awk -F '|' '{print \$2}' \\"
       echo -e "\t\t   | cdn_host_remove.sh -u \${user} -p \${password}"
       echo -e "\n\t Remove duplicate hosts, leaving only the latest one that checked in"
       echo -e "\t\t cdn_report.py --user \${user} --password \${password} --ownerid \${ownerid} --duplicates --silent \\"
       echo -e "\t\t   | grep -v \"^#\" | awk '{print \$2}' \\"
       echo -e "\t\t   | cdn_host_remove.sh -u \${user} -p \${password}"
       echo -e "\n\n"
       exit 0
       ;;
  esac
done


[[ "x${options[file]}" = "x" ]] && options[file]="-"

  echo ${options[file]}

  count=0

  echo "Removing hosts:"

  for i in $( cat ${options[file]} | grep -v "^$|^#|^;" )
  do
    echo "    $i"
    curl --silent -X DELETE -u ${options[user]}:${options[password]} -k "https://subscription.rhsm.redhat.com/subscription/consumers/$i" | jq ".displayMessage"
    (( count++ ))
  done

echo
echo "${count} hosts removed"



