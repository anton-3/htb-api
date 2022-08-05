#!/usr/bin/env python3

import requests
from argparse import ArgumentParser
from dotenv import load_dotenv
import os
import json

load_dotenv()
TOKEN = os.getenv('API_TOKEN')
HEADERS = {
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'ayylmao' # request needs a user-agent to go through
}

parser = ArgumentParser(description='Simple commands to call the HackTheBox API')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-m', type=str, metavar='<machine>', help='get info about a machine')
group.add_argument('--hello', type=str, metavar='<name>', help='say hello (testing)')

args = parser.parse_args()


def get(url):
    resp = requests.get(url, headers=HEADERS).content.decode('utf-8')
#    print(resp)
    return json.loads(resp)

def get_machine_ids():
    active_machines = get('https://www.hackthebox.com/api/v4/machine/list')
    retired_machines = get('https://www.hackthebox.com/api/v4/machine/list/retired')

def print_json(data):
    print(json.dumps(data, indent=2, sort_keys=True))


if args.m:
    machine = args.m
    url = 'https://www.hackthebox.com/api/v4/machine/info/'
    response = get(url + machine)
    print_json(response)
elif args.hello:
    print(f'hello {args.hello}')
