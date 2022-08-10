#!/usr/bin/env python3

# TODO
# implement submitting flags (post to /machine/own with flag:flag, id: machine id, difficulty
# https://github.com/D3vil0per/HackTheBox-API
# -s: show status of the account, if a machine is spawned
# -S machine: spawn a specific machine
# -K: kill the running machine
# -R: reset the running machine
#    post('https://www.hackthebox.com/api/v4/vm/reset', {'machine_id':444})
# -u user: user info, if no user is provided assume self
# colored output?

import requests
from argparse import ArgumentParser
from dotenv import load_dotenv
import os
import sys
import json
import time
from datetime import datetime

ENABLE_DEBUGGING = False
if ENABLE_DEBUGGING:
    from IPython import embed

# get API token from .env
load_dotenv()
TOKEN = os.getenv('API_TOKEN')
HEADERS = {
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'bruh'
        }

# parse command line arguments
parser = ArgumentParser(description='simple commands to call the HackTheBox v4 API')
group = parser.add_mutually_exclusive_group()
group.add_argument('-m', type=str, metavar='machine', help='print info about a machine - pass its name, ip, or id')
group.add_argument('-r', type=str, metavar='machine', help='same as -m but print as raw json')
if ENABLE_DEBUGGING:
    group.add_argument('-d', action='store_true', help='debug mode')

args = parser.parse_args()

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

# listing all functions right here for sanity's sake
# get(): send GET request to the API, return json
# post(): send POST request to the API, return json
# get_machine(): get data about a machine and print it to console
# get_reviews(): return review data about a machine
# print_json(): print a python dict prettily to console
# print_machine(): print a machine's data prettily to console

# sends a request to an endpoint in HTB's API, passing proper headers for auth
# return json response as python dict
def get(url):
    if not TOKEN:
        print('no API token found in .env, you need one to make API requests')
        print('instructions here: https://github.com/anton-3/htb-api')
        sys.exit(1)
    response = requests.get(url, headers=HEADERS).content.decode('utf-8')
    return json.loads(response)

def post(url, data=None):
    if not TOKEN:
        print('no API token found in .env, you need one to make API requests')
        print('instructions here: https://github.com/anton-3/htb-api')
        sys.exit(1)
    if data:
        response = requests.post(url, headers=HEADERS, data=data)
    else:
        response = requests.post(url, headers=HEADERS)
    response = response.content.decode('utf-8')
    return json.loads(response)

# function for -m
# get data about a machine and print it to console
# name_or_id is either the name or id of the machine
# we can get the data directly if it's a lab machine (active or retired)
# if it's a starting point machine, we need to make a second request
def get_machine(name_or_id):
    response = get('https://www.hackthebox.com/api/v4/machine/profile/' + name_or_id)
    # if the request found a matching machine (either in active or retired)
    if 'info' in response:
        machine = response['info']
        group = 'retired' if machine['retired'] == 1 else 'active'
        print_machine(machine, group)
    elif response['message'] == 'Starting Point Machine':
        sp_machines = get('https://www.hackthebox.com/api/v4/sp/machines')['info']
        # if this next() stuff throws a StopIteration then the API data is inaccurate (idc enough to handle that)
        machine = next(machine for machine in sp_machines if name_or_id.lower() == machine['name'].lower() or name_or_id == str(machine['id']))
        print_machine(machine, 'starting_point')
    else:
        print('error: no such machine')

# get and return review data for a machine given its id
# this is only used for one part of the output in print_machine()
def get_reviews(id):
    url = 'https://www.hackthebox.com/api/v4/machine/reviews/' + str(id)
    review_data = get(url)['message']
    return review_data

# print json data (python dict) to the console prettily
def print_json(data):
    print(json.dumps(data, indent=4))

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
        print(f'\n      {m_name} - {m_difficulty} {m_os} - Starting Point - by {m_author}')
        print(f'      Released {m_date_str} ({m_days_ago} days ago)')
        print(f'      {m_user_owns} User Owns, {m_root_owns} Root Owns\n')
        return

    # active and retired have a lot more data to display
    # review data is only accessible sometimes
    reviews = get_reviews(machine['id'])
    # store whether or not we have access to review data that we should print later
    # if it's a str it'll be 'You do not have access to the reviews'
    show_reviews = type(reviews) != str

    # get all the values from the machine dict
    m_name = machine['name']
    m_difficulty = machine['difficultyText']
    m_os = machine['os']
    m_author = machine['maker']['name']
    m_date_obj = datetime.strptime(machine['release'].split('T')[0], '%Y-%m-%d')
    m_date_str = m_date_obj.strftime('%B %d, %Y')
    m_days_ago = (datetime.now() - m_date_obj).days
    m_stars = machine['stars']
    m_user_owns = machine['user_owns_count']
    m_root_owns = machine['root_owns_count']
    m_difficulty_rating = machine['difficulty']
    feedback = machine['feedbackForChart']
    # get review data only if it exists
    if show_reviews:
        m_review_count = len(reviews)
        m_has_author_review = bool([review for review in reviews if review['user']['name'] == m_author])

    # print everything
    print(f'\n      {m_name} - {m_difficulty} {m_os} - {group.capitalize()} - by {m_author}')
    print(f'      Released {m_date_str} ({m_days_ago} days ago)')
    print(f'      User Difficulty Rating {m_difficulty_rating}/100')
    print(f'      {m_user_owns} User Owns, {m_root_owns} Root Owns')
    print(f'\n      Rating - {m_stars}/5 Stars' + (f' - {m_review_count} Reviews' if show_reviews else ''))
    print(f'         {int(float(m_stars) * 10) * "#"}{(50 - int(float(m_stars) * 10)) * "-"}')
    if show_reviews and m_has_author_review:
        print('      including a self review by the author (cringe)')
    print('\n      Difficulty Ratings:')
    max_count = max(feedback.values())
    counter = 1
    for index, d in enumerate(difficulty):
        vote_count = feedback[d]
        num = int(vote_count / max_count * 50)
        print(f"      {index+1}{'' if len(str(index+1)) == 2 else ' '} {num * '#'}{(50 - num) * '-'} {vote_count}")
    print()

def main():
    if args.m or args.r:
        get_machine(args.m if args.m else args.r)
    elif ENABLE_DEBUGGING and args.d:
        embed()
    else:
        parser.print_help()

main()
