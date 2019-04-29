"""
    instabot filtering private users example

    Workflow:
        Try to follow a private user with the bot and see how it
        filters that user out.
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '../'))
from instabot import Bot


bot = Bot(filter_users=False,
          filter_private_users=False)
bot.login()
private_user_input = input("\n Enter a private user: ")
bot.follow(bot.get_user_id_from_username(private_user_input))
