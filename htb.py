#!/usr/bin/env python3

# TODO
# print_machine function actually prints human readable
# -r machine: gets machine, prints raw json output instead of human readable
# -s: show status of the account, if a machine is spawned
# -S machine: spawn a specific machine
# -K: kill the running machine

import requests
from argparse import ArgumentParser
from dotenv import load_dotenv
import os
import sys
import json
import time
from IPython import embed

# get API token from .env
load_dotenv()
TOKEN = os.getenv('API_TOKEN')
HEADERS = {
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'bruh' # request needs a user-agent to go through
        }

# path to the dir the script is in
# need this for reading/writing to machines.json later (-g option)
SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

# parse command line arguments
parser = ArgumentParser(description='simple commands to call the HackTheBox v4 API')
group = parser.add_mutually_exclusive_group()
group.add_argument('-m', type=str, metavar='machine', help='print info about a machine - pass its name, ip, or id')
group.add_argument('-g', action='store_true', help='generate a json with all machine data - this makes requests way faster')
group.add_argument('-d', action='store_true', help='debug mode')

args = parser.parse_args()

# URL endpoints for getting data about HTB machines
# pointing to the group of machines corresponding to that URL
urls = {
        'https://www.hackthebox.com/api/v4/machine/list': 'active',
        'https://www.hackthebox.com/api/v4/machine/list/retired': 'retired',
        'https://www.hackthebox.com/api/v4/sp/machines': 'starting_point'
        }

# functions (bc im too lazy to implement a class)

# sends a request to an endpoint in HTB's API, passing proper headers for auth
# return json response as python dict
def get(url):
    if not TOKEN:
        print('no API token found in .env, you need one to make API requests')
        print('instructions here: https://github.com/anton-3/htb-api')
        sys.exit(1)
    resp = requests.get(url, headers=HEADERS).content.decode('utf-8')
    return json.loads(resp)

# function for -m
# get data about a machine and print it to console
# name_ip_id is either the name, ip, or id of the machine
# api doesn't support requesting by name so instead we grab all of them and filter for it
# three groups of machines, can't request all at once
# to minimize number of requests, check active machines first, then retired, then starting point
def get_machine(name_ip_id):
    print('searching for ' + name_ip_id)
    machines_json_path = os.path.join(SCRIPT_DIR, 'machines.json')
    if os.path.exists(machines_json_path):
        print('machines.json found, reading from it')
        with open(machines_json_path, 'r') as f:
            data = json.load(f)
        if int(time.time()) - data['time_created'] > 300000:
            print('warning: machines.json is a few days old')
            print('consider updating it with -g')

        for group in urls.values():
            machine_list = data[group]
            machine = machine_from_list(name_ip_id, machine_list)
            if machine:
                print_machine(machine, group)
                return
        print('error: no such machine')
        return

    print('no machines.json found, calling API for machine data...')
    for url in urls:
        machine_list = get(url)['info']
        machine = machine_from_list(name_ip_id, machine_list)
        if machine:
            print_machine(machine, urls[url])
            return
    print('error: no such machine')

# select machine from list where name_ip_id is equal to a machine's name OR ip OR id
def machine_from_list(name_ip_id, machine_list):
    machine = [machine for machine in machine_list if ('ip' in machine and name_ip_id == machine['ip']) or name_ip_id == str(machine['id']) or name_ip_id.lower() == machine['name'].lower()]
    return machine[0] if machine else []

# function for -g
# generates a json with all machine data and saves it to machines.json in script's directory
# machines.json structure:
# 'active': {data about all active machines}
# 'retired': {data about all retired machines}
# 'starting_point': {data about all starting point machines}
def generate_json():
    print('making API requests for machine data...')
    data = {}
    # get json data for each group individually: active, retired, starting_point
    for url in urls:
        group = urls[url]
        groupdata = get(url)['info']
        data[group] = groupdata
    # also store the unix time the json is created e.g. 1659691580
    data['time_created'] = int(time.time())
    print('storing the data in machines.json...')
    filename = os.path.join(SCRIPT_DIR, 'machines.json')
    with open(filename, 'w') as f:
        json.dump(data, f)
    print('done!')

# print json data (python dict) to the console prettily
def print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

# take json data about a machine and print it in a human readable way
# group is 'active', 'retired', or 'starting_point'
# need to know the group bc different groups return different data about their machines
def print_machine(machine, group):
    # just a call to print_json for now
    print_json(machine)

def main():
    if args.m:
        get_machine(args.m)
    elif args.g:
        generate_json()
    elif args.d:
        embed()
    else:
        parser.print_help()

main()
