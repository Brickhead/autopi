import logging
import requests
import pickle
import os
from enum import Enum

log = logging.getLogger(__name__)

# Telegram tokens - see https://www.mariansauter.de/2018/01/send-telegram-notifications-to-your-mobile-from-python-opensesame/
#
BOT_TOKEN = ''
BOT_CHATID = ''



def checkChargeStatus():

    # load previous status
    #
    persistance = load()

    # check if we are driving or charging
    #
    charging = get_charging()
    if charging == 0 or charging == -1:
        if persistance['charging'] == True:
            bot_sendtext("Charging stopped. Last known State of charge "+format(persistance['SOC'],'.1f')+"%")
            persistance['charging'] = False
            save(persistance)
        return {"msg": "Not charging"} # Does nothing ?


    chargingPower = get_charging_power()
    soc = get_soc()

    # alert if just started to charge
    #
    if persistance['charging'] == False:
        bot_sendtext("Charging started at a rate of "+format(chargingPower,'.2f')+"kW. State of charge now "+format(soc,'.1f')+"%")

    # 80% alert
    #
    if soc >= 80 and persistance['SOC'] < 80:
        bot_sendtext("Charging now at a rate of "+format(chargingPower,'.2f')+"kW. State of charge now "+format(soc,'.1f')+"%")

    # 100% alert ... not sure if this can really happen
    #
    if soc >= 100 and persistance['SOC'] < 100:
        bot_sendtext("Charging now at a rate of "+format(chargingPower,'.2f')+"kW. State of charge now "+format(soc,'.1f')+"%")

    # store status for next time
    #
    persistance['charging'] = True
    persistance['SOC'] = soc
    save(persistance)

    return {"msg": "Charging at "+format(chargingPower,'.2f')+"kW, SOC now "+format(soc,'.1f')+"%"}

# send message to telegram
#
def bot_sendtext(message):
    send_text = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + BOT_CHATID + '&parse_mode=Markdown&text=' + message
    requests.get(send_text)

# load persistance
#
def load():
    try:
        persistance = pickle.load( open( 'charge_status.p', 'rb' ) )
    except:
        persistance = { 'charging': False, 'SOC': 0 }

    return persistance

# save persistance
#
def save(persistance):
    pickle.dump( persistance, open( "charge_status.p", "wb" ) )

# delete persistance
#
def delete():
    os.remove("charge_status.p")



# OBD Queries -----------------------------------------------------------------------------

def get_charging_power():
        args = ['charging_power']
        kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': '(twos_comp(bytes_to_int(message.data[13:14])*256+bytes_to_int(message.data[14:15]),16)/10.0)*((bytes_to_int(message.data[15:16])+bytes_to_int(message.data[16:17]))/10.0)/1000.0',
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        return __salt__['obd.query'](*args, **kwargs)['value']*-1.0

# get display state of charge
#
def get_soc():
    args = ['soc']
    kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': 'bytes_to_int(message.data[34:35])',
        'protocol': '6',
        'verify': False,
        'force': True,
        }
    return __salt__['obd.query'](*args, **kwargs)['value']/2.0

## LOCATION
#
def get_location():
    args = []
    kwargs = {}
    return __salt__['ec2x.gnss_nmea_gga'](*args, **kwargs)

# Retuns exception
def get_carState():
  #  try:
        args = ['driving']
        kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': 'bytes_to_int(message.data[53:54])',  # Ignition
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        return (int(__salt__['obd.query'](*args, **kwargs)['value'])&4)/4

def get_charging():
    try:
        args = ['driving']
        kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': 'bytes_to_int(message.data[12:13])',
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        return (int(__salt__['obd.query'](*args, **kwargs)['value'])&128)/128
    except:
        return -1

# Weird response, always seem to be true
def get_charging_chademo():
#  try:
        args = ['CCS Plug']
        kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': 'bytes_to_int(message.data[12:13])',
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        return (int(__salt__['obd.query'](*args, **kwargs)['value'])&64)/64

# Weird response, always seem to be true
def get_charging_normal():
#  try:
        args = ['J1772 Plug']
        kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': 'bytes_to_int(message.data[12:13])',
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        return (int(__salt__['obd.query'](*args, **kwargs)['value'])&32)/32
