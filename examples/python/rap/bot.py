# https://github.com/noemtdev

from discord.ext import commands, tasks
import aiohttp

from util.rap import Rap

class Bot(commands.Bot):
    def __init__(self):
        super().__init__()
        self.command_prefix = ">"
        self.token = "Enter bot token in here"

    async def on_ready(self):
        print(f"Logged in as {self.user}")

        self.session = aiohttp.ClientSession()
        self.rap = Rap(self.session)

        self.fetch_rap.start()

    @tasks.loop(hours=24)
    async def fetch_rap(self):
        await self.rap.fetch_rap()

    def run(self):
        super().run(self.token)


bot = Bot()
bot.run()

"""
RAP is accessable via bot.rap.rap, an example of the list can be found in rap-example.json
"""