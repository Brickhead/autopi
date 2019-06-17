import pickle
import os
from datetime import datetime  
from datetime import timedelta
from dateutil.parser import parse


def poll():
    charging = get_charging()
    driving = get_driving()
    if charging == 1 or driving == 1:
        disable_sleep()
        return {"msg": "sleep disabled"}
    else:
        enable_sleep()
        delete()
        return {"msg": "sleep enabled"}


# Check if we have been driving within the last 5 minutes
def get_driving():
    persistance = load()
    rpm = get_driveMotorSpeed()
    if rpm > 10: # if we have more than 10 rpm we should be moving.
        persistance['lastDrive'] = datetime.now()
        save(persistance)
        return 1
    if (persistance['lastDrive'] + timedelta(minutes=10)) > datetime.now(): # Drove within the last 5 minutes
        return 1
    else:
        return 0

# enable autopi sleep
def enable_sleep():
    args = ['sleep']
    kwargs = {
        'enable': True,
    }
    __salt__['power.sleep_timer'](**kwargs)

# disable autopi sleep
def disable_sleep():
    args = ['sleep']
    kwargs = {
        'enable': False,
    }
    __salt__['power.sleep_timer'](**kwargs)


# --- Persistance ---

def load():
    try:
        persistance = pickle.load( open( 'sleepData.p', 'rb' ) )
    except:
        persistance = { 'lastDrive': parse("2010-01-01 00:00:00") }
    return persistance

def save(persistance):
    pickle.dump( persistance, open( "charge_status.p", "wb" ) )

def delete():
    os.remove("charge_status.p")

# --- OBD ---

def get_charging():
    try:
        args = ['charging']
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