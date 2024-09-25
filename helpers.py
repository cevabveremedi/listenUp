import os
import requests
import urllib.parse

# There libs are on the official documentation; I couldn't really use them but I'll read about them again in the future.
#import google_auth_oauthlib.flow
#import googleapiclient.discovery
#import googleapiclient.errors

import random
import re
import html

from flask import redirect, render_template, request, session, flash
from functools import wraps

from werkzeug.wrappers import Response

# from the distro code
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# function to retrieve a random video
def callYT(channel):
    try:
        api_key = os.environ.get("API_KEY")
        # for testing purposes;
        # api_key = [REDACTED]
        url = f"https://www.googleapis.com/youtube/v3/search?order=date&part=snippet&channelId={channel}&maxResults=50&key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        print("Something went wrong...")
        return None
    try:
        videos = response.json()
    except (KeyError, TypeError, ValueError) as e:
        print(e)
        return None

    # loop until get a proper subtitle list
    while True:
        rndm = random.randint(0, len(videos['items'])-1)
        video = videos['items'][rndm]
        subtitle = getCaption(video['id']['videoId'])
        if subtitle == None:
            continue
        if len(subtitle) == 3:
            break
        else:
            print("len not 3! how?")
            print(subtitle)

    mylist = [video['id']['videoId'], subtitle]
    return mylist
    #https://www.youtube.com/watch?v={id}&t={time}s

def getCaption(video):
    url = f"http://video.google.com/timedtext?lang=en&v={video}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        print("Something went wrong...")
        return None

    # It was originally return none, but I decided to try my chance with 
    # the en(united kingdom) caption too
    if len(response.text) < 50:
        url = f"http://video.google.com/timedtext?lang=en-GB&v={video}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            print("Something went wrong...")
            return None

        # IF still no caption, then return none.
        if len(response.text) < 50:
            return None

    try:
        substr = re.findall(r"<text(.*?)</text>", response.text)
    except Exception as e:
        print(e)
        return None

    # sometimes regex messes up and creates an empty list. So I add the following, just in case.
    if not substr:
        # source: https://stackoverflow.com/a/19772902
        rand = max(random.randint(0, response.text.count("<text")), 3)
        
        sentence = response.text.split('<text', rand)[rand-1]
        if sentence.endswith('</text>'):
            sentence = sentence[:-7]
    else:
        sentence = random.choice(substr)


    html.unescape(sentence)
    a,b = sentence.split('>', maxsplit=1)
    a = a.replace("\"", " ")

    mylist = []

    for i in a.split(' '):
        try:
            result = float(i)
            mylist.append(result)
        except:
            continue

    mylist.append(b)
    
    return mylist

#    with open('cc.txt', 'w') as file:
#        file.write(response.text.replace('><', '>\n<'))

#getCaption("dFCbJmgeHmA") #en-gb sub
#getCaption("0FRVx_c9T0c") #nosub
#getCaption("J0ldO87Pprc") #en

#getCaption("-inNrttB5tk") #regex bug: causes empty list.

#print(callYT("UCsooa4yRKGN_zEE8iknghZA"))
#print(callYT("UCsXVk37bltHxD1rDPwtNM8Q"))