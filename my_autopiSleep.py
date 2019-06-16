import requests
from datetime import datetime  
from datetime import timedelta  
import pickle

def poll():
    charging = get_charging()
    driving = get_driving()
    if charging == 1 or driving == 1:
        disable_sleep()
        return {"msg": "sleep disabled"}
    else:
        enable_sleep()
        return {"msg": "sleep enabled"}


# Check if we have been driving within the last 5 minutes
def get_driving():
    rpm = get_driveMotorSpeed()
    if rpm > 10: # if we have more than 10 rpm we should be moving.
        persistance['lastDrive'] = datetime.datetime.now()
        return 1
    if (persistance['lastDrive'] + timedelta(minutes=5) ) > datetime.datetime.now():
        return 1
    else:
        return 0

# enable autopi sleep
#
def enable_sleep():
    args = ['sleep']
    kwargs = {
        'enable': True,
    }
    __salt__['power.sleep_timer'](**kwargs)

# disable autopi sleep
#
def disable_sleep():
    args = ['sleep']
    kwargs = {
        'enable': False,
    }
    __salt__['power.sleep_timer'](**kwargs)


# --- OBD ----

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

def get_driveMotorSpeed():
    try:
        args = ['driving']
        kwargs = {
        'mode': '21',
        'pid': '01',
        'header': '7E4',
        'baudrate': 500000,
        'formula': '(twos_comp(bytes_to_int(message.data[56:57]),16))*256)+bytes_to_int(message.data[57:58])', # (Signed(BB)*256)+BC
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        return (int(__salt__['obd.query'](*args, **kwargs)['value']))
    except:
        return -1