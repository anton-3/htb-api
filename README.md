# HackTheBox API Script 1.2

Simple python script to interact with [HackTheBox](https://www.hackthebox.com)'s [API](https://documenter.getpostman.com/view/13129365/TVeqbmeq)

```
usage: htb.py [-h] [-m machine | -a | -S machine | -K | -R]

simple commands to call the HackTheBox v4 API
all commands are mutually exclusive

options:
  -h, --help  show this help message and exit
  -m machine  print info about a machine - pass its name or id
  -a          print info about currently active (spawned) machine
  -S machine  spawn an instance of a machine - pass its name or id
  -K          kill the currently active machine
  -R          request a reset for the currently active machine
```

## Usage

First, clone this repo:
```
git clone https://github.com/anton-3/htb-api
cd htb-api
```
Install dotenv if you haven't already:
```
python3 -m pip install python-dotenv
```
Copy the .env.example over to .env:
```
cp .env.example .env
```
You need an API token in order to use this script. In order to get one, head over to your Profile Settings in HackTheBox and click Create App Token. Copy that token and replace `your_api_token_here` in `.env` with your API token.

## Example

```
$ ./htb.py -m lame  

      Lame - Easy Linux - Retired - by ch4p
      https://app.hackthebox.com/machines/1
      Released March 14, 2017 (1975 days ago)
      User Difficulty Rating 26/100
      42127 User Owns, 44889 Root Owns

      Rating - 4.6/5 Stars - 137 Reviews
         ##############################################----

      Difficulty Ratings:
      1  ################################################## 23780
      2  ##################################---------------- 16372
      3  ########################-------------------------- 11465
      4  #######------------------------------------------- 3585
      5  ###########################----------------------- 12951
      6  #------------------------------------------------- 648
      7  -------------------------------------------------- 380
      8  -------------------------------------------------- 203
      9  -------------------------------------------------- 88
      10 -------------------------------------------------- 240
```

## Current Features

- Retrieving details about any active, retired, or starting point HackTheBox machine
- Print that data to the console in a human readable format
- Retrieve info about current spawned machine
- Spawn a machine
- Kill a spawned machine
- Reset a spawned machine

## Upcoming Features

- Submit a flag for a spawned machine

## I'm unoriginal

Here's a few other people who are doing the same thing but better:
- [thomaslaurenson](https://github.com/thomaslaurenson/htb-api)
- [qtc-de](https://github.com/qtc-de/htb-api)
- [clubby789](https://github.com/clubby789/htb-api)
- [apognu](https://github.com/apognu/htb)
