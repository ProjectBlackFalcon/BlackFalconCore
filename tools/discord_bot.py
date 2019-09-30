import os
from credentials import credentials
from subprocess import Popen, PIPE


def send_discord_message(message):
    sh_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'discord.sh'))
    Popen('''bash {} --webhook-url={} --text "{}"'''.format(sh_path, credentials['discord']['webhook'], message), shell=True, stdout=PIPE)


if __name__ == '__main__':
    send_discord_message('Python integration test')
