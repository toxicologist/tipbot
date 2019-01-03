import json
import discord
import threading
from tipper.markets import *
from tipper.tipper import *

# reading from settings file
with open('settings.json', 'r') as f:
    config = json.load(f)

# setting everything up
ws = config['wallet']
cs = config['coin']
ms = config['markets']
token = config['token']

c = Connection(ws['user'], ws['password'], ws['ip'], ws['port'])
if ms['enabled'].lower() == "true":
    m = Market(ms['site'], ms['ticker'], ms['update-interval'])
else:
    m = Market(enabled=False)
client = discord.Client()

@client.event
async def on_message(message):
    # make sure bot doesnt reply to himself
    if message.author == client.user:
        return
    
    if message.content.startswith('!price'):
        price = m.get_price()
        msg = "The current price of %s is $%f or %.8f BTC." % (cs['name'], price[1], price[0])
        return await client.send_message(message.channel, msg)
    
    if message.content.startswith('!help'):
        helpmsg = "**!deposit** or **!addr** - shows your deposit address.\n" \
                  "**!balance [0conf=false]** - shows your balance\n**!tip [user] [amount]** - tips another user " \
                  "coins.\n **!withdraw [amount] [address]** - withdraws funds to an external address." \
                  "\n**!rain [amount]** - tips everyone on the server."
        if ms['enabled'].lower() == "true":
            helpmsg += '\n**!price** - shows the current price of %s.' % cs['name']
        return await client.send_message(message.channel, helpmsg)

    if message.content.startswith('!deposit') or message.content.startswith('!addr'):
        account = message.author.id
        address = c.get_address(account)
        msg = '{0.author.mention}, your address is %s.'.format(message) % address
        return await client.send_message(message.channel, msg)

    if message.content.startswith('!balance 0conf'):  # 0conf balance
        account = message.author.id
        balance = c.get_balance(account, 0)
        msg = '{0.author.mention}, you have %f %s, including 0-confs.'.format(message) % (balance, cs['ticker'])
        return await client.send_message(message.channel, msg)

    if message.content.startswith('!balance'):
        account = message.author.id
        balance = c.get_balance(account)
        price_usd = m.get_price(float(balance))[1]
        msg = '{0.author.mention}, you have %f %s ($%.2f).'.format(message) % (balance, cs['ticker'], price_usd)
        return await client.send_message(message.channel, msg)

    if message.content.startswith('!tip '):
        tipper = message.author.id
        content = message.content.split()[1:]
        to_tip_mention = content[0]
        to_tip = to_tip_mention.replace('<@','').replace('>','')  # remove <@> from ID
        amount = content[1]

        # catching errors
        if not to_tip_mention[:2] == '<@':
            return await client.send_message(message.channel, "{0.author.mention}, invalid account.".format(message))
        try:
            amount = float(amount)
        except ValueError:
            return await client.send_message(message.channel, "{0.author.mention}, invalid amount.".format(message))

        try:
            c.tip(tipper, to_tip, amount)
            price_usd = m.get_price(float(amount))[1]
            return await client.send_message(message.channel, "{0.author.mention} has tipped %s %f %s ($%.2f).".format(message) % (to_tip_mention, amount, cs['ticker'], price_usd))
        except ValueError:
            return await client.send_message(message.channel, "{0.author.mention}, insufficient balance.".format(message))

    if message.content.startswith('!withdraw '):
        account = message.author.id
        amount = message.content.split()[1]
        address = message.content.split()[2]
        
        # catching errors again
        if not c.validate_address(address):
            return await client.send_message(message.channel, "{0.author.mention}, invalid address.".format(message))
        
        try:
            amount = float(amount)
        except ValueError:
            return await client.send_message(message.channel, "{0.author.mention}, invalid amount.".format(message))

        try:
            txid = c.withdraw(account, address, amount)
            return await client.send_message(message.channel, "{0.author.mention}, withdrawal complete, TXID %s".format(message)%txid)
        except ValueError:
            return await client.send_message(message.channel, "{0.author.mention}, insufficient balance.".format(message))

    if message.content.startswith('!rain '):
        account = message.author.id
        amount = float(message.content.split()[1])

        if amount < 0.01:
            return await client.send_message(message.channel, "{0.author.mention}, the amount must be bigger than 0.01 %s.".format(message) % cs['ticker'])
        # catching errors again
        try:
            amount = float(amount)
        except ValueError:
            return await client.send_message(message.channel, "{0.author.mention}, invalid amount.".format(message))

        try:
            eachtip = c.rain(account, amount)  # the function returns each individual tip amount so this just makes it easier
            return await client.send_message(message.channel, "{0.author.mention} has tipped %f %s to everyone on this server!".format(message) % (eachtip, cs['ticker']))
        except ValueError:
            return await client.send_message(message.channel, "{0.author.mention}, insufficient balance.".format(message))
    
@client.event
async def on_ready():
    await update_status()
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

async def update_status():
    if ms['enabled'].lower() == "true":
        threading.Timer(int(ms['update-interval']), update_status).start()
        print("Updating status")
        price = m.get_price()[1]
        status = '%s: %.5f USD' % (m.ticker, price)
        await client.change_presence(game = discord.Game(name = status))

client.run(config['token'])


