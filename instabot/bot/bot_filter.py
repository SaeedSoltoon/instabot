"""
    Filter functions for media and user lists.
"""

from . import delay


# Adding `users_id`s to `skipped.txt`, such that InstaBot will not
# try to follow them again or InstaBot will not like their media anymore.
def skippedlist_adder(self, user_id):
    skipped = self.read_list_from_file("skipped.txt")
    if user_id not in skipped:
        with open('skipped.txt', 'a') as file:
            msg = 'Adding `user_id` {} to `skipped.txt`.'.format(user_id)
            self.console_print(msg, 'green')
            file.write(str(user_id) + "\n")


# Filtering media

def filter_medias(self, media_items, filtration=True, quiet=False, is_comment=False):
    if filtration:
        if not quiet:
            self.logger.info("Received {} medias.".format(media_items))
        if not is_comment:
            media_items = _filter_medias_not_liked(media_items)
            if self.max_likes_to_like:
                media_items = _filter_medias_nlikes(
                    media_items, self.max_likes_to_like)
        else:
            media_items = _filter_medias_not_commented(self, media_items)
        if not quiet:
            msg = "After filtration {} medias left."
            self.logger.info(msg.format(len(media_items)))
    return _get_media_ids(media_items)


def _filter_medias_not_liked(media_items):
    not_liked_medias = []
    for media in media_items:
        if 'has_liked' in media and not media['has_liked']:
            not_liked_medias.append(media)
    return not_liked_medias


def _filter_medias_not_commented(self, media_items):
    not_commented_medias = []
    for media in media_items:
        if media.get('comment_count', 0) > 0 and media.get('comments'):
            my_comments = [comment for comment in media['comments']
                           if comment['user_id'] == self.user_id]
            if my_comments:
                continue
        not_commented_medias.append(media)
    return not_commented_medias


def _filter_medias_nlikes(media_items, max_likes_to_like):
    filtered_medias = []
    for media in media_items:
        if 'like_count' in media:
            if media['like_count'] < max_likes_to_like:
                filtered_medias.append(media)
    return filtered_medias


def _get_media_ids(media_items):
    result = []
    for media in media_items:
        if 'pk' in media:
            result.append(media['pk'])
    return result


def check_media(self, media_id):
    self.media_info(media_id)
    if self.filter_medias(self.last_json["items"]):
        return check_user(self, self.get_media_owner(media_id))
    return False


# Filter users

def search_stop_words_in_user(self, user_info):
    text = ''
    if 'biography' in user_info:
        text += user_info['biography'].lower()

    if 'username' in user_info:
        text += user_info['username'].lower()

    if 'full_name' in user_info:
        text += user_info['full_name'].lower()

    for stop_word in self.stop_words:
        if stop_word in text:
            return True

    return False


def filter_users(self, user_id_list):
    return [str(user["pk"]) for user in user_id_list]


def check_user(self, user_id, filter_closed_acc=False, unfollowing=False):
    if not self.filter_users and not unfollowing:
        return True

    delay.small_delay(self)
    user_id = self.convert_to_user_id(user_id)

    if not user_id:
        self.console_print('not user_id, skipping!', 'red')
        return False
    if self.whitelist and user_id in self.whitelist:
        self.console_print('`user_id` in `self.whitelist`.', 'green')
        return True
    if self.blacklist and user_id in self.blacklist:
        self.console_print('`user_id` in `self.blacklist`.', 'red')
        return False

    if user_id == str(self.user_id):
        self.console_print("`user_id` equals bot's `user_id`, skipping!", 'green')
        return False

    if not self.following:
        self.console_print('Own following list is empty, will download.', 'green')
        self.following = self.get_user_following(self.user_id)
    if user_id in self.following:
        if not unfollowing:
            # Log to Console
            self.console_print('Already following, skipping!', 'red')
        return False

    user_info = self.get_user_info(user_id)
    if not user_info:
        self.console_print('not `user_info`, skipping!', 'red')
        return False

    msg = 'USER_NAME: {username}, FOLLOWER: {followers}, FOLLOWING: {following}'
    follower_count = user_info["follower_count"]
    following_count = user_info["following_count"]
    self.console_print(msg.format(
        username=user_info["username"],
        followers=follower_count,
        following=following_count
    ))

    if filter_closed_acc and "is_private" in user_info:
        if user_info["is_private"]:
            self.console_print('info: account is PRIVATE, skipping! ', 'red')
            return False
    if "is_business" in user_info and self.filter_business_accounts:
        if user_info["is_business"]:
            self.console_print('info: is BUSINESS, skipping!', 'red')
            skippedlist_adder(self, user_id)
            return False
    if "is_verified" in user_info and self.filter_verified_accounts:
        if user_info["is_verified"]:
            self.console_print('info: is VERIFIED, skipping !', 'red')
            skippedlist_adder(self, user_id)
            return False

    if follower_count < self.min_followers_to_follow:
        msg = 'follower_count < bot.min_followers_to_follow, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False
    if follower_count > self.max_followers_to_follow:
        msg = 'follower_count > bot.max_followers_to_follow, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False
    if user_info["following_count"] < self.min_following_to_follow:
        msg = 'following_count < bot.min_following_to_follow, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False
    if user_info["following_count"] > self.max_following_to_follow:
        msg = 'following_count > bot.max_following_to_follow, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False
    try:
        if follower_count / following_count > self.max_followers_to_following_ratio:
            msg = 'follower_count / following_count > bot.max_followers_to_following_ratio, skipping!'
            self.console_print(msg, 'red')
            skippedlist_adder(self, user_id)
            return False
        if following_count / follower_count > self.max_following_to_followers_ratio:
            msg = 'following_count / follower_count > bot.max_following_to_followers_ratio, skipping!'
            self.console_print(msg, 'red')
            skippedlist_adder(self, user_id)
            return False
    except ZeroDivisionError:
        self.console_print('ZeroDivisionError: division by zero', 'red')
        return False

    if 'media_count' in user_info and user_info["media_count"] < self.min_media_count_to_follow:
        msg = 'media_count < bot.min_media_count_to_follow, BOT or INACTIVE, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False

    if search_stop_words_in_user(self, user_info):
        msg = '`bot.search_stop_words_in_user` found in user, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False

    return True


def check_not_bot(self, user_id):
    """ Filter bot from real users. """
    delay.small_delay(self)
    user_id = self.convert_to_user_id(user_id)
    if not user_id:
        return False
    if self.whitelist and user_id in self.whitelist:
        return True
    if self.blacklist and user_id in self.blacklist:
        return False

    user_info = self.get_user_info(user_id)
    if not user_info:
        return True  # closed acc

    if "following_count" in user_info and user_info["following_count"] > self.max_following_to_block:
        msg = 'following_count > bot.max_following_to_block, skipping!'
        self.console_print(msg, 'red')
        skippedlist_adder(self, user_id)
        return False  # massfollower

    if search_stop_words_in_user(self, user_info):
        msg = '`bot.search_stop_words_in_user` found in user, skipping!'
        skippedlist_adder(self, user_id)
        return False

    return True
