#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import requests
import random
from dotenv import load_dotenv
from loguru import logger
from slackclient import SlackClient

load_dotenv()

SLCKBTD = None
SLCKCLNT = SlackClient(os.getenv("SLACK_BOT_TOKEN"))

#[ Magic Declarations ]#
RTM_READ_DELAY = 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
#[ End magic declarations ]#

#------ Define bot functions here ------------------------------------------
def say_hello(command, event):
    return f"Hello {event['user']} :snake:"
    
def get_kitty(command, event):
    r = requests.get(f"https://community-placekitten.p.rapidapi.com/{random.randint(100, 600)}/{random.randint(100, 600)}", headers={"X-RapidAPI-Key": os.getenv("X-RapidAPI-Key")})
    open('kitty.png', 'wb').write(r.content)
    SLCKCLNT.api_call(
        'files.upload', 
        channels=event['channel'], 
        as_user=True, 
        filename='pic.jpg', 
        file=open('kitty.png', 'rb'),
    )
    return False

def get_norris(command, event):
    r = requests.get("https://matchilling-chuck-norris-jokes-v1.p.rapidapi.com/jokes/random", headers={"X-RapidAPI-Key": os.getenv("X-RapidAPI-Key")})
    j = json.loads(r.text)
    return j["value"] + " :tada:"

def get_insult(command, event):
    r = requests.get(f"https://insult.mattbas.org/api/insult.txt?who={event['user']}")
    return r.text
#------ Add definitions to CMDS dict ---------------------------------------

CMMDS = {
    # Key: func
    "hi": say_hello,
    "kitten": get_kitty,
    "norris": get_norris,
    "insult": get_insult
}

def humanizeChannel(channel):
    return "#{}".format(
        SLCKCLNT.api_call(
            "channels.info", 
            channel=channel
        ).get(
            'channel', 
            {}
        ).get('name'))


def humanizeUser(user):
    return SLCKCLNT.api_call(
        "users.info", 
        user=user).get(
            'user', 
            {}
        ).get('name')


def parse_incoming(sevent):
    for event in sevent:
        if 'user' in event:
                event['user'] = humanizeUser(event['user'])

        if 'channel' in event:
            event['channel'] = humanizeChannel(event['channel'])

        if event["type"] == "message" and not "subtype" in event:

            user_id, message = matchDirect(event["text"])
            if user_id == SLCKBTD:
                logger.info(f"Message Recieved in {event['channel']}: {message}")
                return message, event
        # if 'subtype' in event and event['subtype'] != "bot_message":
        logger.debug(event)
    return None, None

def matchDirect(msg):
    r = re.search(MENTION_REGEX, msg)
    return (r.group(1), r.group(2).strip()) if r else (None, None)

def handle_command(command, event):
    comm = command.split(" ")
    response = None

    if comm[0] in CMMDS:
        response = CMMDS[comm[0]](command, event)
    
    if response != False and response != None:
        logger_response = response.replace('\n', ' ')[:20]
        logger.info(f"Response: {logger_response}...")       
        SLCKCLNT.api_call(
            "chat.postMessage",
            channel=event['channel'],
            text=response or "What was that? :: Try: " + ", ".join([x for x in CMMDS.keys()])
        )

    if response == None:
        SLCKCLNT.api_call(
            "chat.postMessage",
            channel=event['channel'],
            text="What was that? :: Try: " + ", ".join([x for x in CMMDS.keys()])
        )

if __name__ == "__main__":
    if SLCKCLNT.rtm_connect(with_team_state=False):
        SLCKBTD = SLCKCLNT.api_call("auth.test")["user_id"]
        logger.info(f"Bot connected {SLCKBTD}")

        while True:
            command, channel = parse_incoming(SLCKCLNT.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        logger.exception("Connection Failed")
        
