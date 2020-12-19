# Laundry Bot for RC4, current telegram handle: @RC4LaundryBot

import os
import re
import logging
import requests
from datetime import datetime
import time
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from data import MockData
from string import Template

# This import is for communicating with google sheet######
from Google import Create_Service

##########################################################

# Only modify the sheet_ID when needed, else no need to change anything

CLIENT_SECRET_FILE = "credentials.json"
API_NAME = "sheets"
API_VERSION = "v4"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

SHEET_ID = '1Wu2fL9DMmroz4PM7iNE-wf7IfqEAho4ArJ9L-zzxrxo'

sheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()

################################################################################



# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global variables
RC_URL = "https://us-central1-rc4laundrybot.cloudfunctions.net/readData/RC4-"
LAUNDRY_LEVELS = [5, 8, 11, 14, 17]
MACHINES_INFO = {
    'washer-coin': 'Washer 1',
    'washer-ezlink': 'Washer 2',
    'dryer-ezlink': 'Dryer 1',
    'dryer-coin': 'Dryer 2'
}
DATA = MockData()


# Building menu for every occasion
def build_menu(buttons, n_cols, header_buttons=None, reminder_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if reminder_buttons:
        menu.append(reminder_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return InlineKeyboardMarkup(menu)


# Building emojis for every occasion
ebluediamond = emojize(":small_blue_diamond: ", use_aliases=True)
etick = emojize(":white_check_mark: ", use_aliases=True)
ecross = emojize(":x: ", use_aliases=True)
esoon = emojize(":soon: ", use_aliases=True)
ehourglass = emojize(":hourglass:", use_aliases=True)


# start command initializes:
def check_handler(bot, update, user_data):
    # user = update.message.from_user
    if 'pinned_level' in user_data:
        level_status(bot, update, user_data,
                     from_pinned_level=True, new_message=True)
    else:
        ask_level(bot, update)


def ask_level(bot, update):
    level_text = "Heyyo! I am RC4's Laundry Bot. <i>As I am currently in [BETA] mode, "\
        "I can only show details for Ursa floor.</i>\n\n<b>Which laundry level do you wish to check?</b>"
    level_buttons = []
    for level in LAUNDRY_LEVELS:
        label = 'Level {}'.format(level)
        data = 'set_L{}'.format(level)
        buttons = InlineKeyboardButton(text=label, callback_data=data)  # data callback to set_pinned_level
        level_buttons.append(buttons)
    update.message.reply_text(text=level_text,
                              reply_markup=build_menu(level_buttons, 1),
                              parse_mode=ParseMode.HTML)


def set_pinned_level(bot, update, user_data):
    query = update.callback_query
    level = int(re.match('^set_L(5|8|11|14|17)$', query.data).group(1))
    user_data['pinned_level'] = level

    level_status(bot, update, user_data, from_pinned_level=True)


# Generate a Hour Minute Second template
class DeltaTemplate(Template):
    ''' Set a template for input data '''
    delimiter = "%"

# Change from timedelta to H M S format without unecessary microsecond
def strfdelta(tdelta, fmt):
    ''' Format timedelta object to the format of string fmt

    Parameter
    ----------
        tdelta: datetime.timedelta
            The datetime.timedelta object that needs to be formatted
        fmt: str
            The format string (eg. %H:%M:%S)
    
    Returns
    -------
        str
            a formmated time string
    '''

    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


# Carves the status text for each level
def make_status_text(level_number):
    laundry_data = ''
    floor_url = RC_URL + str(level_number)
    # TODO: This should be the backend server time instead
    current_time = datetime.fromtimestamp(time.time() + 8*3600).strftime('%d %B %Y %H:%M:%S')

    # Get Request to the database backend
    # machine_status = requests.get(floor_url).json()

    # Use mock data
    machine_data = DATA.getStatuses(level_number)

    for machine in machine_data: 
        # Get data from back end - time since request/refresh
        remaining_time = datetime.today() - machine["start-time"]
        remaining_time = strfdelta(remaining_time, '%H:%M:%S')

        if machine["status"] == 0:
            status_emoji = etick
        else:
            status_emoji = f'{ehourglass} {remaining_time} |'

        machine_name = machine["type"]
        laundry_data += '{}  {}\n'.format(status_emoji, machine_name)

    return "<b>Showing statuses for Level {}</b>:\n\n" \
           "{}\n" \
           "Last updated: {}\n".format(level_number, laundry_data, current_time)


# Create the status menu which contains the help command, a pinned level number, and refresh button
def make_status_menu(level_number):
    level_buttons = []

    for level in LAUNDRY_LEVELS:
        label = 'L{}'.format(level)
        data = 'check_L{}'.format(level)
        if level == level_number:
            # label = u'\u2022 ' + label + u' \u2022'
            label = ebluediamond + label

        button = InlineKeyboardButton(text=label, callback_data=data)
        level_buttons.append(button)

    refresh_button = [InlineKeyboardButton(
        text='Refresh',
        callback_data='check_L{}'.format(level_number)
    )]

    help_button = [InlineKeyboardButton(
        text='Help',
        callback_data='Help'
    )]

    reminder_button = [InlineKeyboardButton(
        text="Set a reminder",
        callback_data="remind"
    )]
    

    return build_menu(level_buttons, 5, footer_buttons=refresh_button, header_buttons=help_button, reminder_buttons=reminder_button)


def level_status(bot, update, user_data, from_pinned_level=False, new_message=False):
    query = update.callback_query
    if from_pinned_level:
        level = user_data['pinned_level']
    else:
        level = int(re.match('^check_L(5|8|11|14|17)$', query.data).group(1))

    user_data['check_level'] = level

    if new_message:
        update.message.reply_text(text=make_status_text(level),
                                  reply_markup=make_status_menu(level),
                                  parse_mode=ParseMode.HTML)
    else:
        bot.edit_message_text(
            text=make_status_text(level),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=make_status_menu(level),
            parse_mode=ParseMode.HTML
            )


def help_menu(bot, update, user_data, from_pinned_level=False, new_message=False):
    query = update.callback_query
    help_text = "<b>Help</b>\n\n" + "Washer 1 and Dryer 2 accept coins\n" \
        + etick + "= Available / Job done\n" + esoon + "= Job finishing soon\n" + ecross + "= In use\n"

    help_text += "\nInformation not accurate or faced a problem? "\
        "Please message @PakornUe or @Cpf05, thank you!"
    help_text += "\n\nThis is a project by RC4Space's Laundry Bot Team. "\
        "We appreciate your feedback as we are currently still beta-testing "\
        "in Ursa before launching the college-wide implementation! :)"

    level = user_data['check_level']

    help_menu_button = [InlineKeyboardButton(
        text='Back',
        callback_data='check_L{}'.format(level)
    )]

    bot.edit_message_text(
        text=help_text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=build_menu(help_menu_button, 1),
        parse_mode=ParseMode.HTML
        )


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

def remind(bot, update, user_data):
    ''' Set up reminder function interface

        User will be bring to a prompt which show machines that are in used
        and can be set a reminder for (machines that are not in used cannot
        be set a reminder function).

        When machine buttons is clicked:
            data will be sent to add_reminder()
        When back button is clicked:
            user will be sent back to origianl prompt
    '''

    query = update.callback_query
    level = user_data['check_level']
    selection = []
    
    #Mock test
    machine_data = DATA.getStatuses(level)
    
    question = "Which machine on Level {} do you like to set a reminder for?\n".format(level)

    # Put in-use machines in selection list
    for machine in machine_data:
        if machine["status"] != 0:
            label = machine['type']
            data = machine['type']
            button = InlineKeyboardButton(text=label, callback_data=data)
            selection.append(button)

    back_button = [InlineKeyboardButton(
        text='Back',
        callback_data='check_L{}'.format(level)
    )]

    bot.edit_message_text(
        text=question,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=build_menu(selection, len(selection), footer_buttons=back_button),
        parse_mode=ParseMode.HTML
        )

def add_reminder(bot, update, user_data):
    ''' Append current time, username, level and machine to Google sheet

        Append current date, current time, username, level and machine data to Google sheet
        to save reminders. The data is saved in Laundrybot sheet under Reminder tab.
    '''
    query = update.callback_query
    level = user_data['check_level']
    username = query['from_user']['username']
    data = query['data']
    current_date = datetime.fromtimestamp(time.time() + 8*3600).strftime('%d %B %Y')
    current_time = datetime.fromtimestamp(time.time() + 8*3600).strftime('%H:%M:%S')
    
    #Mock test
    machine_data = DATA.getStatuses(level)

    notice = 'A reminder has been set for Level {} {}'.format(level,data)

    # Set up value to be append to google sheet
    WORKSHEET_NAME = 'Reminder!'
    cell_range_insert = 'A1'
    values = [
    [current_date,current_time,username,level,data]
    ]
    value_range_body = {
        'majorDimension': 'ROWS',
        'values': values
    }

    # Append to the google sheet
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        valueInputOption= 'USER_ENTERED',
        range= WORKSHEET_NAME+cell_range_insert,
        body= value_range_body
    ).execute()

    back_button = [InlineKeyboardButton(
        text='Back',
        callback_data='check_L{}'.format(level)
    )]

    bot.edit_message_text(
        text=notice,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=build_menu(back_button, 1),
        parse_mode=ParseMode.HTML,
        )


def main():
    TOKEN = os.environ['RC4LAUNDRYBOT_TOKEN']

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # dp.add_handler used to receive back querry
    # to call a function using a button, passed in pattern= callback_data
    dp.add_handler(CommandHandler('start', check_handler, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(set_pinned_level,
                                        pattern='^set_L(5|8|11|14|17)$',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(level_status,
                                        pattern='^check_L(5|8|11|14|17)$',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(help_menu,
                                        pattern='Help',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(remind, 
                                        pattern='remind',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(add_reminder, 
                                        pattern='^(washer-coin|washer-ezlink|dryer-ezlink|dryer-coin)$',
                                        pass_user_data=True))                                   
    
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
