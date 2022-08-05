#!/usr/bin/env python3

# TODO
# -g option: generates a json file with the data for all machines
# get_machine automatically checks if machines.json exists and prefers it
# print_machine function actually prints human readable
# -r option: gets machine, prints raw json output instead of human readable
# when no args are passed actually do something

import requests
from argparse import ArgumentParser
from dotenv import load_dotenv
import os
import json
from IPython import embed

load_dotenv()
TOKEN = os.getenv('API_TOKEN')
HEADERS = {
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'bruh' # request needs a user-agent to go through
        }

parser = ArgumentParser(description='Simple commands to call the HackTheBox v4 API')
group = parser.add_mutually_exclusive_group()#required=True)
group.add_argument('-m', type=str, metavar='<machine>', help='get info about a machine')
group.add_argument('-d', action='store_true', help='debug mode')

args = parser.parse_args()

# URL endpoints for getting data about HTB machines
# pointing to the group of machines corresponding to that URL
urls = {
        'https://www.hackthebox.com/api/v4/machine/list/retired': 'retired',
        'https://www.hackthebox.com/api/v4/machine/list': 'active',
        'https://www.hackthebox.com/api/v4/sp/machines': 'starting_point'
        }

def get(url):
    resp = requests.get(url, headers=HEADERS).content.decode('utf-8')
    return json.loads(resp)

def print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

def get_machine(name_ip_id):
    # name_ip_id is either the name, ip, or id of the machine
    # api doesn't support requesting by name so instead we grab all of them and filter for it
    # three groups of machines, can't request all at once
    # to minimize number of requests, check retired ones first, then active, then starting point
    for url in urls:
        machine_list = get(url)['info']
        machine = machine_from_list(name_ip_id, machine_list)
        if machine:
            print_machine(machine, urls[url])
            return
    print('Error: no such machine')

def machine_from_list(name_ip_id, machine_list):
    # iterate through the list, if name_ip_id is equal to a machine's name OR ip OR id, that's the machine
    machine = [machine for machine in machine_list if ('ip' in machine and name_ip_id == machine['ip']) or name_ip_id == str(machine['id']) or name_ip_id.lower() == machine['name'].lower()]
    return machine[0] if machine else []

def print_machine(machine, group):
    # take json data about a machine and print it in a human readable way
    # group is 'retired', 'active', or 'starting_point'
    # need to know the group bc different groups return different data about their machines
    print_json(machine)

def main():
    if args.m:
        get_machine(args.m)
    elif args.d:
        embed()
    else:
        print('no args passed')

main()
