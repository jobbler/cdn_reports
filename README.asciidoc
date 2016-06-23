# cdn_reports

== Purpose

These scripts are used to query the Red Hat Content Deliver Network about systems that are subscribed to it.

These scripts were written in order to help me determine where my subscriptions were being used and to unsubscribe unneeded and old systems.

The output of the main script, cd_report.py can be used as input to the cdn_host_remove.sh script to easily unregister systems.

== cdn_report.py

This script can query CDN and display information about the poolusage, duplicate systems and days since last checking.

The output of this can be further refined by reversing the sort order of the output to be descending cwas well as show systems that have not checked in within a certain number of days.

This script requires the username, password and ownerid of the account it was used to register with.

The username and password are the same that is used to login to the Red Hat CDN system.

The owner id can be obtained by issuing the "subscription-manager identity" command from a system that is already registered to the account.

The output is wide, its about 184 characters. This was done for my ease of reading on my monitor.

----
usage: cdn_report.py [-h] [--checkin] [--days DAYS] [--poolusage]
                     [--duplicates] [--reverse] --user USER --password
                     PASSWORD --ownerid OWNERID [--silent]

Query Red Hat CDN

optional arguments:
  -h, --help           show this help message and exit
  --checkin            Display days since host checkin
  --days DAYS          Display hosts who have not checked in within this
                       number of days or longer.
  --poolusage          Display the pool usage information
  --duplicates         Display information about duplicate hosts
  --reverse            Reverse the sort order of output
  --user USER          CDN user account name. Required option.
  --password PASSWORD  CDN user account password. Required option.
  --ownerid OWNERID    The org id of the CDN user, can be retrieved using the
                       "subscription-manager identity" command on a registered
                       system. Required option.
  --silent             Just print the data, no headers or information about
                       what we are doing.
----


== Generating Reports

=== Pool Usage

A pool usage report displays the Pool name, the pool ID, the number of total subscriptions for this pool id, the amount consumed and the amount exported to for use with things like satellite.

Following each line displaying the pool name is a list of systems that are consuming these subscriptions.
The system ID, system name, and days since it has checked in are displayed for each of these systems.

----
$ cdn_report.py --user ${user} --password "${password}" --ownerid XXXXXXX --reverse --poolusage

Getting list of pools from CDN.
Getting list of hosts from CDN.
Getting list of entitlements from CDN.
                          Name   |   Pool ID    | Quantity | Consumed | Exported
--------------------------------------------------------------------------------
Operating System 1               | 123456abcdef |      300 |      101 |       30
     Attached Systems: |   System ID            | Name
                       | 12345678-abcd-1a2b3c4d | system-1  Last Checkin (days): 50
                       | 12345678-abcd-1a2eeeee | system-2  Last Checkin (days): 0

Operating System 2               | aabbcc1122dd |       10 |        8 |        0
     Attached Systems: |   System ID            | Name
                       | bcdef678-af5d-1a2cfd4d | system-3  Last Checkin (days): 9
                       | 12346fde-aeed-1a2abdce | system-4  Last Checkin (days): 5

----




=== Duplicate systems

A duplicate systems report displays the number of duplicate system for a given system name, the system name, the seconds since epoch that it was registered, and the uuid of the system.

The first instance for a system name contains a hash (#) at the beginning of the line. 
This system is the system that has the most recent registration.
The hash was placed at the beginning of the line for eay parsing when removing duplicate systems. See below.

Subsequent lines for the same system name do not list the system namei or number of its duplicates.

----
$ cdn_report.py --user ${user} --password "${password}" --ownerid XXXXXXX --reverse --duplicates

Getting list of pools from CDN.
Getting list of hosts from CDN.
Getting list of entitlements from CDN.
Hosts with duplicates:  197
Duplicate systems:  276
Freeable systems:  79
# 11  system-1                                 1466648032 12345678-abcd-1a2b3c4d
          1466639184 1b2b32b3-1234-867ab210
          1466132041 3b2ds525-abdd-a1b1c1d1
          1465339439 3232bb32-43bc-abcdabcd
          1464219749 423443dd-7652-12341234
# 10  system-2                                 1466649410 12345678-abcd-1a2eeeee
          1466638967 3421dd11-abcd-bdcdeeed
          1465339174 787dbb8a-42dc-abcdef11
# 10  system-3                                 1466649256 bcdef678-af5d-1a2cfd4d
          1466638709 678acb26-6421-bcccad12
          1464196357 5673ffff-ab12-123bcddd
----







=== Last Checkin

A checkin report can display when the systems last checked in or the systems that have not checked in within a certain number of days. (you must specify the --days option).

This report lists the system name, system id, the number of days since last checkin, and the number of entitlements the system is consuming.

----
$ cdn_report.py --user ${user} --password "${password}" --ownerid XXXXXXX --reverse --checkin --days 30

Getting list of pools from CDN.
Getting list of hosts from CDN.
Getting list of entitlements from CDN.
Host                 |                  ID    | Last Checking (Days) | Entitlements Consumed

--------------------------------------------------------------------------------------------
system-1             | 12345678-abcd-1a2b3c4d | 162                  |            1
system-2             | 12345678-abcd-1a2eeeee | 156                  |            1
system-3             | bcdef678-af5d-1a2cfd4d | 156                  |            0
system-4             | 23422323-1234-11223344 | 155                  |            0
system-5             | ababaaba-4321-aabbccdd | 153                  |            1
system-2             | 3421dd11-abcd-bdcdeeed | 153                  |            0
system-2             | 787dbb8a-42dc-abcdef11 | 142                  |            1
system-1             | 3232bb32-43bc-abcdabcd | 141                  |            1
system-1             | 423443dd-7652-12341234 | 140                  |            1
----


== Generating all three reports

A bash script called cdn_gen_reports.sh is included that will generate a pool usage, duplicate systems, and last checkin report.

The script can either use environment variables $user, $password, and $ownerid or it can use a cdnrc file (by default in the ~/bin) directory. 
The cdnrn file simply defines these variables.

The script will generate the reports and place them into the /tmp directory.



== Removing Hosts

Be careful when doing this. This will remove systems from being registered. Use this as well as the other scripts at your own risk.

----
usage: ./cdn_host_remove.sh [options]
	 -f 	File that contains list of system uuids to remove.
	 -u 	CDN User name
	 -p 	CDN User password

	 Example usages:

	 Enter the hosts to remove
		 cdn_host_remove.sh -u USER -p PASSWORD

	 Remove the hosts in /tmp/remove_list.txt
		 cdn_host_remove.sh -u USER -p PASSWORD -f /tmp/remove_list.txt

	 Remove the hosts in /tmp/remove_list.txt
		 cat /tmp/remove_list.txt | cdn_host_remove.sh -u USER -p PASSWORD

	 Remove hosts that have not checked in within the last 90 days
		 cdn_report.py --user ${user} --password ${password} --checkin --ownerid ${ownerid} --days 90 --silent \
		   | awk -F '|' '{print $2}' \
		   | cdn_host_remove.sh -u ${user} -p ${password}

	 Remove duplicate hosts, leaving only the latest one that checked in
		 cdn_report.py --user ${user} --password ${password} --ownerid ${ownerid} --duplicates --silent \
		   | grep -v "^#" | awk '{print $2}' \
		   | cdn_host_remove.sh -u ${user} -p ${password}
----




