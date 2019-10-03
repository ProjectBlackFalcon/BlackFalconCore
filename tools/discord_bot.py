import os

import time

from credentials import credentials
from subprocess import Popen, PIPE


def send_discord_message(message):
    sh_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'discord.sh'))
    Popen('''bash {} --webhook-url={} --text "{}"'''.format(sh_path, credentials['discord']['webhook'], message.replace('`', "\`").replace('\n', ' ' * 300)), shell=True, stdout=PIPE)


if __name__ == '__main__':
    send_discord_message('''Traceback (most recent call last):
  File "swarm_node/swarm_node.py", line 111, in maintain_assets
    raise Exception
Exception
'''.replace('\n', ' '*500))
    time.sleep(10)
