import discord
import asyncio
from credentials import credentials


class DiscordMessageSender(discord.Client):
    def __init__(self, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    async def on_ready(self):
        channel = self.get_channel(384760673629896714)
        await channel.send(self.message)
        await self.close()


if __name__ == '__main__':
    DiscordMessageSender('Test').run(credentials['discord']['token'])
