#!/usr/bin/env python3

# API reference (since nobody has all the endpoints in a single place ig)
# https://documenter.getpostman.com/view/13129365/TVeqbmeq
# https://github.com/D3vil0per/HackTheBox-API
# https://pyhackthebox.readthedocs.io/en/latest/index.html
# TODO
# cache active machine IP somewhere so each call to -a doesn't take a year?
# -X: submit review https://github.com/D3vil0p3r/HackTheBox-API#submit-a-machine-review
# -u user: user info, if no user is provided assume self
# some kind of machine display system to show machines sorted in an interactive interface
# colored output?

import requests
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dotenv import load_dotenv
import os
import sys
import json
import time
from datetime import datetime, timedelta

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
BASEURL = 'https://www.hackthebox.com/api/v4'

# parse command line arguments
parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description='simple commands to call the HackTheBox v4 API\nall commands are mutually exclusive')
group = parser.add_mutually_exclusive_group()
group.add_argument('-m', type=str, metavar='machine', help='print info about a machine (default: active)', nargs='?', const=True)
group.add_argument('-a', action='store_true', help='show currently active (spawned) machine')
group.add_argument('-w', type=str, metavar='machine', help='get official pdf writeup for a machine (default: active) and save it to a file', nargs='?', const=True)
group.add_argument('-t', action='store_true', help='print current to-do list')
group.add_argument('-T', type=str, metavar='machine', help='add or remove a machine from your to-do list')
group.add_argument('-S', type=str, metavar='machine', help='spawn an instance of a machine')
group.add_argument('-K', action='store_true', help='kill the currently active machine')
group.add_argument('-R', action='store_true', help='request a reset for the currently active machine')
group.add_argument('-F', type=str, metavar='flag', help='submit flag for the currently active machine - either flag text or a filename')
if ENABLE_DEBUGGING:
    group.add_argument('-d', action='store_true', help='debug mode')

args = parser.parse_args()

# putting difficulty strings in order to interpret responses later
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
# get_machine(): -m, get data about a machine and print it to console
# get_active(): -a, basically get_machine() but for currently active machine
# get_writeup(): -w, get official writeup for a machine
# get_todo(): -t, get current to-do list
# update_todo(): -T, add or remove a machine from your to-do list
# spawn_machine(): -S, spawn a machine
# kill_machine(): -K, kill currently spawned machine
# reset_machine(): -R, reset currently spawned machine
# submit_flag(): -F, submit flag for currently spawned machine
# get_difficulty(): get user difficulty rating for submit_flag()
# get_ip(): get IP of a machine
# get_reviews(): return review data about a machine
# print_json(): print a python dict prettily to console
# print_machine(): print a machine's data prettily to console

# sends a get request to an endpoint in HTB's API, passing proper headers for auth
# return json response as python dict
def get(endpoint):
    if not TOKEN:
        print('no API token found in .env, you need one to make API requests')
        print('instructions here: https://github.com/anton-3/htb-api')
        sys.exit(1)
    url = BASEURL + endpoint
    response = requests.get(url, headers=HEADERS)
    try:
        return json.loads(response.content.decode('utf-8'))
    # just return the regular response if it's not json
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        return response

# same but for post requests
def post(endpoint, data=None):
    if not TOKEN:
        print('no API token found in .env, you need one to make API requests')
        print('instructions here: https://github.com/anton-3/htb-api')
        sys.exit(1)
    url = BASEURL + endpoint
    if data:
        response = requests.post(url, headers=HEADERS, data=data)
    else:
        response = requests.post(url, headers=HEADERS)
    try:
        return json.loads(response.content.decode('utf-8'))
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        return response

# function for -m
# GET /machine/profile/name_or_id OR /sp/machines/name_or_id
# get data about a machine and print it to console
# name_or_id is either the name or id of the machine
# we can get the data directly if it's a lab machine (active or retired)
# if it's a starting point machine, we need to make a second request
def get_machine(name_or_id):
    # if -m is passed without args, it's set to True by argparser
    # we want it to retrieve the currently spawned machine in that case
    if name_or_id == True:
        active_response = get('/machine/active')
        info = active_response['info']
        if not info:
            print('no currently active machine')
            return
        m_id = info['id']
        # /machine/active doesn't return very much info
        # so we need to request /machine/profile with its newly acquired id
        response = get(f'/machine/profile/{m_id}')
    else:
        # otherwise just make the same request with the arg
        response = get('/machine/profile/' + name_or_id)
    # if the request found a matching machine (either in active or retired)
    if 'info' in response:
        machine = response['info']
        group = 'retired' if machine['retired'] == 1 else 'active'
        print_machine(machine, group)
    elif response['message'] == 'Starting Point Machine':
        sp_machines = get('/sp/machines')['info']
        # if this next() stuff throws a StopIteration then the API data is inaccurate (idc enough to handle that)
        machine = next(machine for machine in sp_machines if name_or_id.lower() == machine['name'].lower() or name_or_id == str(machine['id']))
        print_machine(machine, 'starting_point')
    else:
        print('error: no such machine')

# function for -a
# GET /machine/active
# gets currently active machine and prints its information
def get_active():
    response = get('/machine/active')
    info = response['info']
    if not info:
        print('no currently active machine')
        return
    name = info['name']
    m_id = info['id']
    expire_date = info['expires_at']
    expire_date_obj = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    expires_in = expire_date_obj - now
    expires_in_rounded = timedelta(days=expires_in.days, seconds=expires_in.seconds)
    print(f'\n      Active machine: {name} ID {m_id}')
    print(f'      Expires in {expires_in_rounded}')
    print('      Getting IP: ')
    try:
        # this call takes literal years so consider removing it
        # putting it in a try except so you can ctrl C it without stack trace output
        print(f'      {get_ip(m_id)}')
    except:
        pass

# function for -w
# GET /machine/writeup/id
# get official writeup for a machine
# gets the currently active machine without an argument
def get_writeup(name_or_id):
    if name_or_id == True:
        # if no argument passed, get the ID of active machine
        active_response = get('/machine/active')
        info = active_response['info']
        if not info:
            print('no currently active machine')
            return
        m_id = info['id']
        name = info['name']
    else:
        # otherwise call /machine/profile to get both name and ID
        # since we only have one of the two right now
        profile_response = get('/machine/profile/' + name_or_id)
        if 'info' in profile_response:
            info = profile_response['info']
            m_id = info['id']
            name = info['name']
        else:
            print('error: no such machine')
            return
    # now we have the id for sure
    print(f'requesting pdf writeup for {name}')
    response = get(f'/machine/writeup/{m_id}')
    if not response.status_code == 200:
        print('error: no such machine')
        return
    filename = f'{name}-writeup.pdf'
    print(f'writing pdf data to {filename}')
    with open(filename, 'wb') as f:
        f.write(response.content)

# function for -t
# GET /machine/todo
# gets machines in your to-do list and prints them to the console
def get_todo():
    response = get('/machine/todo')
    info = response['info']
    print('https://app.hackthebox.com/machines/list/todo')
    if not info:
        print('no to-do machines found')
        return

    for machine in info:
        m_name = machine['name']
        m_difficulty = machine['difficultyText']
        m_difficulty_rating = machine['difficulty']
        m_os = machine['os']
        m_date_obj = datetime.strptime(machine['release'].split('T')[0], '%Y-%m-%d')
        m_days_ago = (datetime.now() - m_date_obj).days
        m_stars = machine['stars']
        print(f'{m_name} - {m_difficulty} {m_os} - Diff Rating {m_difficulty_rating}/100 - {m_stars}/5 Stars - {m_days_ago} Days Old')

# function for -T
# POST /machine/todo/update/id
# adds or removes a machine from your to-do list
def update_todo(name_or_id):
    # we need the id to spawn the machine
    if name_or_id.isnumeric():
        # if name_or_id is an id, we can just use it in the spawn request
        m_id = int(name_or_id)
    else:
        # if it's a name, we need to send a request and get the id
        name = name_or_id
        info_response = get('/machine/profile/' + name)
        if 'info' in info_response:
            m_id = info_response['info']['id']
        else:
            print('error: no such machine')
            return

    print(f'updating to-do for machine ID {m_id}...')
    # get the todo list before updating so we can check if the machine got added or removed
    before_todo = get('/machine/todo')
    todo_response = post(f'/machine/todo/update/{m_id}')

    # if it found the machine
    if 'info' in todo_response:
        # todo_response['info'] is the to-do list after the update
        old_todo_size = len(before_todo['info'])
        new_todo_size = len(todo_response['info'])

        # if new list is bigger than old list, it got added
        if new_todo_size > old_todo_size:
            print('added machine to to-do list')
        # if vice versa, it got removed
        elif new_todo_size < old_todo_size:
            print('removed machine from to-do list')
        # this should never happen but I'll handle it anyway
        else:
            print('something happened, idk what')

    # if it didn't find the machine
    else:
        print('error: no such machine')

# function for -S
# POST /vm/spawn {'machine_id': 123}
# spawns an instance of a machine given name or id
def spawn_machine(name_or_id):
    # we need the id to spawn the machine
    if name_or_id.isnumeric():
        # if name_or_id is an id, we can just use it in the spawn request
        m_id = int(name_or_id)
    else:
        # if it's a name, we need to send a request and get the id
        name = name_or_id
        info_response = get('/machine/profile/' + name)
        if 'info' in info_response:
            m_id = info_response['info']['id']
        else:
            print('error: no such machine')
            return

    # try to spawn the machine from the ID
    print(f'spawning machine ID {m_id}... (may take a while)')
    data = {'machine_id': m_id}
    spawn_response = post('/vm/spawn', data)
    message = spawn_response['message']

    # if it worked, tell the user the IP of the machine as well
    if message == 'Machine deployed to lab.':
        m_ip = get_ip(m_id)
        m_url = f'https://app.hackthebox.com/machines/{m_id}'
        message += f'\n{m_url}\n{m_ip}'

    print(message)

# function for -K
# POST /vm/terminate {'machine_id': 123}
# kills the currently spawned machine instance
def kill_machine():
    # get the currently active machine first
    # since for some reason we need to pass the ID of the machine we're killing
    active_response = get('/machine/active')
    info = active_response['info']
    if not info:
        print('no currently active machine')
        return
    name = info['name']
    m_id = info['id']
    print(f'killing {name}...')
    data = {'machine_id': m_id}
    kill_response = post('/vm/terminate', data)
    message = kill_response['message']
    print(message)

# function for -R
# POST /vm/reset {'machine_id': 123}
# requests a reset for the current active machine instance
def reset_machine():
    active_response = get('/machine/active')
    info = active_response['info']
    if not info:
        print('no currently active machine')
        return
    name = info['name']
    m_id = info['id']
    print(f'requesting reset for {name}...')
    data = {'machine_id': m_id}
    reset_response = post('/vm/reset', data)
    message = reset_response['message']
    print(message)

# function for -F
# POST /machine/own {'flag': flag, 'id': 123, 'difficulty': 5}
# submits a flag for the currently active machine
# prompts for difficulty rating, user must input an integer between 1 and 10 inclusive
# flag_arg is either the flag text itself e.g. "e0d0a3d75aae2526566b0892d28de23c"
# or a path to a flag file like user.txt or root.txt
def submit_flag(flag_arg):
    # first, make sure a machine is spawned, if so get its ID
    # i'm violating DRY here I know
    active_response = get('/machine/active')
    info = active_response['info']
    if not info:
        print('no currently active machine')
        return
    name = info['name']
    m_id = info['id']
    flag_chars = '0123456789abcdef'
    if all(char in flag_chars for char in flag_arg):
        # if flag_args is exclusively in hex characters, treat it as the flag itself
        flag = flag_arg
    else:
        # otherwise read from that file
        try:
            with open(flag_arg, 'r') as f:
                flag = f.read().strip() # strip the newline at the end
        except FileNotFoundError:
            print('error: invalid flag format or couldn\'t read flag file')
            return
    # get the difficulty rating from the user
    difficulty = get_difficulty()
    print(f'submitting flag {flag} with difficulty {difficulty}/10 for machine {name}')
    data = {}
    data['flag'] = flag
    data['id'] = m_id
    data['difficulty'] = difficulty * 10 # the actual endpoint expects 10-100
    submit_response = post('/machine/own', data)
    message = submit_response['message']
    status = submit_response['status']
    print(f'{status} {message}')

# gets a difficulty rating from the user for submit_flag
# must be an integer between 1 and 10 inclusive
def get_difficulty():
    while True:
        difficulty = input('rate the difficulty 1-10: ')
        if difficulty.isnumeric() and int(difficulty) in range(1,11):
            return int(difficulty)
        print('error: invalid input, must be an integer between 1 to 10 inclusive')

# gets IP of machine given its name or ID
# in general should avoid this as it takes several seconds to run
# for some godforsaken reason the only way I know of to get a machine's IP
# is to query for literally every machine and select for the correct IP
# only works for lab machines (either active or retired)
def get_ip(name_or_id):
    # first make a request to /machine/profile/{name_or_id} to get the group that it's in
    info_response = get(f'/machine/profile/{name_or_id}')
    if not 'info' in info_response:
        print('get_ip() error, this shouldn\'t have happened')
        return
    info = info_response['info']
    m_id = info['id']
    endpoint = '/machine/list/retired' if info['retired'] == 1 else '/machine/list'
    list_response = get(endpoint)
    list_info = list_response['info']
    machine = next(machine for machine in list_info if m_id == machine['id'])
    return machine['ip']

# get and return review data for a machine given its id
# this is only used for one part of the output in print_machine()
def get_reviews(machine_id):
    review_data = get('/machine/reviews/' + str(machine_id))['message']
    return review_data

# print json data (python dict) to the console prettily
def print_json(data):
    print(json.dumps(data, indent=4))

# take json data about a machine and print it in a human readable way
# group is 'active', 'retired', or 'starting_point'
# need to know the group bc different groups return different data about their machines
def print_machine(machine, group):
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
    m_id = machine['id']
    m_url = f'https://app.hackthebox.com/machines/{m_id}'
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
    print(f'      {m_url}')
    print(f'      Released {m_date_str} ({m_days_ago} days ago)')
    print(f'      User Difficulty Rating {m_difficulty_rating}/100')
    print(f'      {m_user_owns} User Owns, {m_root_owns} Root Owns')
    print(f'\n      Rating - {m_stars}/5 Stars' + (f' - {m_review_count} Reviews' if show_reviews else ' - No Reviews'))
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
    if args.m:
        get_machine(args.m)
    elif args.a:
        get_active()
    elif args.w:
        get_writeup(args.w)
    elif args.t:
        get_todo()
    elif args.T:
        update_todo(args.T)
    elif args.S:
        spawn_machine(args.S)
    elif args.K:
        kill_machine()
    elif args.R:
        reset_machine()
    elif args.F:
        submit_flag(args.F)
    elif ENABLE_DEBUGGING and args.d:
        embed()
    else:
        parser.print_help()

main()
