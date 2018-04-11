# 
# https://github.com/sindresorhus/weechat-notification-center
# Requires `pip install pync`

#
# Updated by effie mouzeli:
#

import os
import datetime
import weechat
import time
from dateutil.tz import tzutc
from pync import Notifier

SCRIPT_NAME = 'notification_center'
SCRIPT_AUTHOR = 'Sindre Sorhus <sindresorhus@gmail.com>'
SCRIPT_VERSION = '1.4.0'
SCRIPT_LICENSE = 'MIT'
SCRIPT_DESC = 'Pass highlights and private messages to the macOS X 10.10+ Notification Center'

weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, '', '')

# use com.googlecode.iterm2 in activate_bundle_id for iTerm 

DEFAULT_OPTIONS = {
	'show_highlights': 'on',
	'show_private_message': 'on',
	'show_message_text': 'on',
	'sound': 'off',
	'sound_name': 'Pong',
	'activate_bundle_id': 'com.apple.Terminal',
	'ignore_old_messages': 'off',
	'reduce_notifications': 'on',
	'notifications_interval': '300',
	'weechat_icon': '~/.weechat/weechat.png',
}


for key, val in DEFAULT_OPTIONS.items():
	if not weechat.config_is_set_plugin(key):
		weechat.config_set_plugin(key, val)

weechat.hook_print('', 'irc_privmsg', '', 1, 'notify', '')

# sample message from Notifier.list
#[{'subtitle': '(null)', 'message': 'In #blabla by @somenick', 'group': 'weechat', 'delivered_at': datetime.datetime(2018, 3, 11, 15, 30, 43, tzinfo=tzutc()), 'title': 'Highlighted Message'}]

def yes_notify(message_time, now_time, interval):
    try:
        # Find when we last had a notification
        # last_in_queue['delivered_at'] is a datetime object
        last_in_queue = Notifier.list(group='weechat')[-1]
        epoch = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=tzutc())
        last_message_time = int((last_in_queue['delivered_at'] - epoch).total_seconds())
        if (now_time - last_message_time) > int(interval):
            return True
        else:
            return False
    except IndexError:
        return True

def tell_notifier(message, title, **kwargs):
	# passing `None` or `''` still plays the default sound so we pass a lambda instead
	sound = weechat.config_get_plugin('sound_name') if weechat.config_get_plugin('sound') == 'on' else lambda:_
	weechat_icon = weechat.config_get_plugin('weechat_icon')
	activate_bundle_id = weechat.config_get_plugin('activate_bundle_id')
	Notifier.notify(message, title=title, sound=sound, appIcon=weechat_icon, activate=activate_bundle_id, group='weechat')

def notify(data, buffer, date, tags, displayed, highlight, prefix, message):
	# ignore if it's yourself
	own_nick = weechat.buffer_get_string(buffer, 'localvar_nick')
	message_time = int(date)
	now_time = int(time.time())
	# prefix is empty on slack :/
	if prefix in own_nick:
		return weechat.WEECHAT_RC_OK

	# ignore messages older than the configured theshold (such as ZNC logs) if enabled
	if weechat.config_get_plugin('ignore_old_messages') == 'on':
		# ignore if the message is greater than 5 minutes old
		if (now_time - message_time) > 300:
			return weechat.WEECHAT_RC_OK
	if weechat.config_get_plugin('reduce_notifications') == 'on':
		interval = weechat.config_get_plugin('notifications_interval')
		if yes_notify(message_time, now_time, interval) is False:
			return weechat.WEECHAT_RC_OK

	if weechat.config_get_plugin('show_highlights') == 'on' and int(highlight):
		channel = weechat.buffer_get_string(buffer, 'localvar_channel')
		if weechat.config_get_plugin('show_message_text') == 'on':
			tell_notifier(message, title='%s %s' % (prefix, channel))
		else:
			tell_notifier('In %s by %s' % (channel, prefix), title='Mention')
	elif weechat.config_get_plugin('show_private_message') == 'on' and 'notify_private' in tags:
		if weechat.config_get_plugin('show_message_text') == 'on':
			tell_notifier(message, title='%s [private]' % prefix)
		else:
			tell_notifier('From %s' % prefix, title='Direct Message')
	return weechat.WEECHAT_RC_OK
