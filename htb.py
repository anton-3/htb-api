#!/usr/bin/env python3

# TODO
# print_machine function actually prints human readable
# implement submitting flags (post to /machine/own with flag:flag, id: machine id, difficulty
# couldn't find any documentation for submitting flags so here's an example
# https://github.com/clubby789/htb-api/blob/1993431b2b458f8163127971c2b046cb0895cb40/hackthebox/machine.py#L97
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
from datetime import datetime
# for debugging
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
group.add_argument('-r', type=str, metavar='machine', help='same as -m but print as raw json')
group.add_argument('-d', action='store_true', help='debug mode')

args = parser.parse_args()

# URL endpoints for getting data about HTB machines
# pointing to the group of machines corresponding to that URL
urls = {
        'https://www.hackthebox.com/api/v4/machine/list': 'active',
        'https://www.hackthebox.com/api/v4/machine/list/retired': 'retired',
        'https://www.hackthebox.com/api/v4/sp/machines': 'starting_point'
        }

# translating difficulty strings to a number out of 10 for later
difficulty = [
        "counterCake",
        "counterVeryEasy",
        "counterEasy",
        "counterTooEasy",
        "counterMedium",
        "counterBitHard",
        "counterHard",
        "counterTooHard",
        "counterExHard",
        "counterBrainFuck"
        ]

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
#    print('searching for ' + name_ip_id)
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

# get and return review data for a machine given its id
# this is only used for one part of the output in print_machine()
# since for some reason the endpoint for listing all machine data doesn't include review count
def get_reviews(id):
    url = 'https://www.hackthebox.com/api/v4/machine/reviews/' + str(id)
    review_data = get(url)['message']
    return review_data

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
    print(json.dumps(data, indent=4))#, sort_keys=True))

# take json data about a machine and print it in a human readable way
# group is 'active', 'retired', or 'starting_point'
# need to know the group bc different groups return different data about their machines
def print_machine(machine, group):
    # if -r, print as raw json
    if args.r:
        print_json(machine)
        return
    # otherwise it's -m, so print it human readable
    # do starting point first bc it's different
    if group == 'starting_point':
        m_name = machine['name']
        m_difficulty = machine['difficultyText']
        m_os = machine['os']
        m_author = machine['maker']['name']
        m_date_obj = datetime.strptime(machine['release'].split('T')[0], '%Y-%m-%d')
        m_date_str = m_date_obj.strftime('%B %d, %Y')
        m_days_ago = (datetime.now() - m_date_obj).days
        m_user_owns = machine['user_owns_count']
        m_root_owns = machine['root_owns_count']
        print(f'\n      {m_name} - {m_difficulty} {m_os} - by {m_author}')
        print(f'      Released {m_date_str} ({m_days_ago} days ago)')
        print(f'      {m_user_owns} User Owns, {m_root_owns} Root Owns\n')
        return

    # active and retired have a lot more data to display
    # add in review data bc why not
    reviews = get_reviews(machine['id'])
    # get all the values from the machine dict
    m_name = machine['name']
    m_difficulty = machine['difficultyText']
    m_os = machine['os']
    m_author = machine['maker']['name']
    m_date_obj = datetime.strptime(machine['release'].split('T')[0], '%Y-%m-%d')
    m_date_str = m_date_obj.strftime('%B %d, %Y')
    m_days_ago = (datetime.now() - m_date_obj).days
    m_stars = machine['stars']
    if not group == 'starting_point':
        m_ip = machine['ip']
    m_user_owns = machine['user_owns_count']
    m_root_owns = machine['root_owns_count']
    m_difficulty_rating = machine['difficulty']
    feedback = machine['feedbackForChart']
    m_review_count = len(reviews)
    m_has_author_review = bool([review for review in reviews if review['user']['name'] == m_author])
    print(f'\n      {m_name} - {m_difficulty} {m_os} - by {m_author} - {m_ip}')
    print(f'      Released {m_date_str} ({m_days_ago} days ago)')
    print(f'      User Difficulty Rating {m_difficulty_rating}/100')
    print(f'      {m_user_owns} User Owns, {m_root_owns} Root Owns')
    print(f'\n      Rating - {m_stars}/5 Stars - {m_review_count} Reviews')
    print(f'         {int(float(m_stars) * 10) * "#"}{(50 - int(float(m_stars) * 10)) * "-"}')
    if m_has_author_review:
        print('      including a self review by the author (cringe)')
    print('\n      Difficulty Ratings:')
    max_count = max(feedback.values())
    counter = 1
    for d in difficulty:
        vote_count = feedback[d]
        num = int(vote_count / max_count * 50)
        print(f"      {counter}{'' if counter == 10 else ' '} {num * '#'}{(50 - num) * '-'} {vote_count}")
        counter += 1
    print()

def main():
    if args.m or args.r:
        get_machine(args.m if args.m else args.r)
    elif args.g:
        generate_json()
    elif args.d:
        embed()
    else:
        parser.print_help()

main()
