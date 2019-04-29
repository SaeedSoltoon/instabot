"""
    instabot example

    Workflow:
        Follow users who liked the last media of input users.
""" 

import argparse
import os
import sys
import json

from tqdm import tqdm

sys.path.append(os.path.join(sys.path[0], '../'))
from instabot import Bot

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('-u', type=str, help="username")
parser.add_argument('-p', type=str, help="password")
parser.add_argument('-proxy', type=str, help="proxy")
parser.add_argument('users', type=str, nargs='+', help='users')
args = parser.parse_args()

bot = Bot(max_follows_per_day=25, follow_delay=30)
bot.login(username=args.u, password=args.p, proxy=args.proxy)

usernames = ["shoes.and.shoess", "just_shoess_", "virtual_shoe", "marlinasport", "tehran.running.shoes"]

for username in usernames:
    medias = bot.get_user_medias(username, filtration=False)    
    if medias:        
        for media in medias:
            likers = bot.get_media_likers(media)
            # for liker in tqdm(likers):
            #     bot.follow(liker)
            f = open(username + '.txt', 'a+')
            jsonstr = json.dumps(likers)
            f.write(jsonstr)
            f.close()

