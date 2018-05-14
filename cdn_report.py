#! /usr/bin/python3

# This script queries the Red Hat Content delivery Network and reports on 
# system and entitlement usage
#
# Author: John Herr
#


import json,sys
import time
import argparse
import requests
from datetime import datetime
from natsort import natsorted

consumer  = {}
pool      = {}
poolusage = {}
hosts     = {}
consumersortlist  = []
duplicatesortlist  = []
usagesortlist  = []

requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description="Query Red Hat CDN")
parser.add_argument('--checkin',    action='store_true', help = 'Display days since host checkin') 
parser.add_argument('--days',       type=int,            help = 'Display hosts who have not checked in within this number of days or longer.') 
parser.add_argument('--poolusage',  action='store_true', help = 'Display the pool usage information')
parser.add_argument('--duplicates', action='store_true', help = 'Display information about duplicate hosts')
parser.add_argument('--reverse',    action='store_true', help = 'Reverse the sort order of output')
parser.add_argument('--user',       required=True,       help = 'CDN user account name. Required option.')
parser.add_argument('--password',   required=True,       help = 'CDN user account password. Required option.')
parser.add_argument('--ownerid',    required=True,       help = 'The org id of the CDN user, can be retrieved using the "subscription-manager identity" command on a registered system. Required option.')
parser.add_argument('--silent',     action='store_true', help = 'Just print the data, no headers or information about what we are doing.')

cliopts = parser.parse_args()


if cliopts.reverse:
    reverse_sort = True
else:
    reverse_sort = False




def print_checkin():
    # Print Checkin Report
    #
    if not cliopts.silent:
        print("{:70} | {:^36} | {:^20} | {:^12}".format( 
            "Host",
            "ID",
            "Last Checking (Days)",
            "Entitlements Consumed",
            )
        )

        print("\n" + '-' * 156)

    if not cliopts.days:
        days = 0
    else:
        days = cliopts.days

    for sitem in natsorted(consumersortlist, reverse=reverse_sort):

        item = sitem.split()[1]

    
        if consumer[item]["checkin"] >= days:
            print("{:70} | {:36} | {!s:20} | {:12}".format( 
                consumer[item]["name"],
                consumer[item]["uuid"],
                consumer[item]["checkin"],
                consumer[item]["entitlementcount"],
                )
            )

  
  
def print_pool_usage():
    ## Print Pool usage
    #

    if not cliopts.silent:
        print("{:^110} | {:^34} | {:^12} | {:^8} | {:^8}".format( 
            "Name",
            "Pool ID",
            "Quantity",
            "Consumed",
            "Exported",
            )
        )
        print("\n" + '-' * 184)
  
    for item in pool:
        usagesortlist.append( "{} {}".format( len( pool[item]['usage'] ), item ) )

    for sitem in natsorted(usagesortlist, reverse=reverse_sort):

        item = sitem.split()[1]

        if pool[item]['quantity'] < 0:
            quantity = "unlimited"
        else:
            quantity = pool[item]['quantity']

#        print("\n" + '-' * 184)
        print("{:110} | {:34} | {:12} | {:8} | {:8}".format( 
            pool[item]['name'],
            item,
            quantity,
            pool[item]['consumed'],
            pool[item]['exported'],
            )
        )
  
        if len(pool[item]['usage']) > 0:
            if not cliopts.silent:
                print("{:>30} | {:^36} | {:70}".format( "Attached Systems:", "System ID", "Name" ))
  
            for id in pool[item]['usage']:
                print("{:30} | {:36} | {:70} Last Checkin (days): {}".format( "", consumer[id]['uuid'], consumer[id]["name"], consumer[id]["checkin"]))



def print_consumer_duplicates():

    duplicate_count   = 0
    duplicate_systems = 0


    for host in consumer:
        name    = consumer[host]['name']
        uuid    = consumer[host]['uuid']
        seconds = consumer[host]['checkin_secs']

        if name not in hosts:
            hosts[name] = {}

#        hosts[name][seconds] = host
        hosts[name][seconds] = uuid

    for item in hosts:
        dup_num = len(hosts[item])

        if dup_num > 1:
            duplicate_count += dup_num
            duplicate_systems += 1

        duplicatesortlist.append( "{} {}".format( len(hosts[item]), item))


    if not cliopts.silent:
        print("Hosts with duplicates: ", duplicate_systems)
        print("Duplicate systems: ", duplicate_count)
        print("Freeable systems: ", duplicate_count - duplicate_systems)

        print("{:^3} | {:^74} | {:^12} | {:^8}".format( 
            "Count",
            "Name",
            "Last Checkin (EPOCH)",
            "ID",
            )
        )
        print('-' * 124)
  

    for sitem in natsorted(duplicatesortlist, reverse=reverse_sort):
        count, item = sitem.split(' ')
        print ( "# {:3} {:80} ".format(count, item), end="")

        for tim in natsorted(hosts[item], reverse=True):
            print ("{:>20} {}".format(tim, hosts[item][tim]))





# Build a dictionary of all the pools
#

if not cliopts.silent:
    print("Getting list of pools from CDN.")

cdn_request = requests.get(
    'https://subscription.rhsm.redhat.com/subscription/owners/{}/pools?include=id&include=productName&include=quantity&include=consumed&include=exported'.format( cliopts.ownerid ),
    auth=(cliopts.user, cliopts.password), 
    verify=False,
    )

#print ( cdn_request.text )

jsonobj = json.loads( cdn_request.text.lower() )

#print ( json.dumps(jsonobj, indent=4, sort_keys=True) )

for poolkey in jsonobj:
    pool[ poolkey["id"] ] = {
        'quantity': poolkey["quantity"],
        'consumed': poolkey["consumed"],
        'exported': poolkey["exported"],
        'name':     poolkey["productname"],
        'usage':    [],
        }

# Get consumer information
#
#jsonobj = json.loads( open('owners_consumers.json').read() )

if not cliopts.silent:
    print("Getting list of hosts from CDN.")

cdn_request = requests.get(
    'https://subscription.rhsm.redhat.com/subscription/owners/{}/consumers?include=id&include=uuid&include=name&include=lastCheckin&include=created'.format( cliopts.ownerid ),
    auth=(cliopts.user, cliopts.password), 
    verify=False,
    )

#print ( cdn_request.text )

jsonobj = json.loads( cdn_request.text.lower() )

#print ( json.dumps(jsonobj, indent=4, sort_keys=True) )


for ckey in jsonobj:
    if not ckey["created"]:
        secs_create = "0"
    else:
        secs_create = datetime.strptime(ckey["created"], "%Y-%m-%dT%H:%M:%S+0000").strftime("%s")

    if not ckey["lastcheckin"]:
        secs_checkin = 0
        days_checkin = 0
    else:
        secs_checkin = datetime.strptime(ckey["lastcheckin"], "%Y-%m-%dT%H:%M:%S+0000").strftime("%s")
        days_checkin = int( ( int( time.time() ) - int( secs_checkin ) ) / 86400 )

    if days_checkin < 0:
        days_checkin = "0"


    consumer[ ckey["id"] ] = {
        'name': ckey["name"],
        'uuid': ckey["uuid"],
        'create': secs_create,
        'checkin': days_checkin,
        'checkin_secs': secs_checkin,
        'entitlementcount': 0,
        }

    consumersortlist.append( "{} {}".format( days_checkin, ckey["id"] ) )


# Loop through pool entitlements to get usage
#
#jsonobj = json.loads( open('owners_entitlements.json').read() )

if not cliopts.silent:
    print("Getting list of entitlements from CDN.")
cdn_request = requests.get(
    'https://subscription.rhsm.redhat.com/subscription/owners/{}/entitlements?include=id&include=consumer.name&include=consumer.id&include=pool.productName&include=pool.id'.format( cliopts.ownerid ),
    auth=(cliopts.user, cliopts.password), 
    verify=False,
    )

#print ( cdn_request.text )

jsonobj = json.loads( cdn_request.text.lower() )

#print ( json.dumps(jsonobj, indent=4, sort_keys=True) )

for usagekey in jsonobj:
#    print ( "consumer id: {}".format(usagekey["consumer"]["id"]) )
    consumer[ usagekey["consumer"]["id"] ]["entitlementcount"] += 1

#    print ( "pool: {}".format(usagekey["pool"]) )
    pool[usagekey["pool"]["id"]]["usage"].append( usagekey["consumer"]["id"] )


# ----------------------------



if cliopts.checkin:
    print_checkin()

if cliopts.poolusage:
    print_pool_usage()


if cliopts.duplicates:
    print_consumer_duplicates()

# if __name__ == '__main__':
# 
#     main()








