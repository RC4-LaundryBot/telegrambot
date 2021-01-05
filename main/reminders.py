import datetime
import time

from emoji import emojize
from telegram import ParseMode

REMINDER_FILE_PATH = '../reminder.csv'

class ReminderList(list):

    """
    Format for each reminder is
    {
        'username': query['from_user']['username'],
        'chat_id': query.message.chat_id,
        'input_data': input_data,
        'machine_data': machine_data
    }
    """

    def poll(self, bot):
        while(True):
            for reminder in self:

                remaining_time = (
                    reminder['machine_data']['start-time'] +
                    datetime.timedelta(minutes=reminder['machine_data']['machine-duration'])
                ) - datetime.datetime.fromtimestamp(time.time() + 8*3600)

                print(
                    "Reminder remaining time for user {}: ".format(reminder['username'])
                    + str(remaining_time.seconds) + "\n"
                )

                if remaining_time < datetime.timedelta(minutes=5):
                    x = self.pop(0)

                    remaining_time_text = " ".join([
                        str(remaining_time.seconds // 60), "minutes",
                        str(remaining_time.seconds % 60), "seconds"
                    ])
                    
                    text = "The <b>{}</b> machine in level <b>{}</b> is done in <b>{}</b>. ".format(
                        x['machine_data']['type'],
                        x['machine_data']['level'],
                        remaining_time_text
                        ) + "Get your clothes ready!" + emojize(":basket:", use_aliases=True)

                    print(x)

                    bot.send_message(
                        text=text,
                        chat_id=x['chat_id'],
                        parse_mode=ParseMode.HTML
                    )
            time.sleep(60)
