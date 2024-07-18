import discord
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to load the bot token from the config file
def load_token():
    try:
        with open('config.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error('Config file not found.')
        raise

TOKEN = load_token()

# Configure the bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to track the last command times for users
user_last_command_time = {}
COMMAND_COOLDOWN = 10  # Cooldown period in seconds

def capture_tradingview_chart():
    chart_url = 'https://www.tradingview.com/chart/vSem31UH/?symbol=CME%3ABTC1!'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--log-level=3')

    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.get(chart_url)
        time.sleep(10)  # Wait for the page to load
        
        screenshot_path = 'chart.png'
        driver.save_screenshot(screenshot_path)
        driver.quit()

        return screenshot_path, chart_url
    except Exception as e:
        logging.error(f"Error while capturing the chart: {e}")
        raise

@bot.event
async def on_ready():
    logging.info(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    current_time = time.time()
    user_id = message.author.id

    if user_id in user_last_command_time:
        last_command_time = user_last_command_time[user_id]
        if current_time - last_command_time < COMMAND_COOLDOWN:
            embed = discord.Embed(
                title="Cooldown",
                description="Please wait a few seconds before trying again.",
                color=discord.Color.orange()
            )
            await message.channel.send(embed=embed)
            return

    user_last_command_time[user_id] = current_time

    if message.content.lower() in ['!cme', '!cme']:
        waiting_message = await message.channel.send(
            embed=discord.Embed(
                title="Processing",
                description="Processing your request... Please wait.",
                color=discord.Color.blue()
            )
        )

        try:
            chart_path, chart_url = capture_tradingview_chart()
            embed = discord.Embed(
                title="TradingView Chart",
                description="Here's the requested chart:",
                color=discord.Color.green()
            )
            embed.set_image(url="attachment://chart.png")
            embed.add_field(name="Chart Link", value=f"[View Chart]({chart_url})")

            await waiting_message.delete()
            await message.channel.send(file=discord.File(chart_path), embed=embed)

        except Exception as e:
            logging.error(f"Error while processing command: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while fetching the chart. Please try again later.",
                color=discord.Color.red()
            )
            await waiting_message.delete()
            await message.channel.send(embed=embed)

        finally:
            # Clean up temporary files
            if os.path.exists(chart_path):
                os.remove(chart_path)

    elif message.content.lower() in ['!help', '!help']:
        embed = discord.Embed(
            title="Help",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        embed.add_field(name="!cme", value="Fetches the CME Bitcoin chart.", inline=False)
        embed.add_field(name="!help", value="Shows this help message.", inline=False)
        await message.channel.send(embed=embed)

    elif message.content.lower() in ['!stop', '!stop']:
        embed = discord.Embed(
            title="Shutdown",
            description="Bot is shutting down...",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
        await bot.close()

# Run the bot
bot.run(TOKEN)
