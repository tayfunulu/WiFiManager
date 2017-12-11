import network
import networkconfig
import time

wlan_sta = network.WLAN(network.STA_IF)


def do_connect(ntwrk_ssid, netwrk_pass):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if sta_if.isconnected():
        return None
    print('Trying to connect to %s...' % ntwrk_ssid)
    sta_if.connect(ntwrk_ssid, netwrk_pass)
    for retry in range(100):
        connected = sta_if.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', sta_if.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ntwrk_ssid)
    return connected


def check_connection():
    global wlan_sta
    # First check if there already is any connection:
    if wlan_sta.isconnected():
        return True
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if not wlan_sta.isconnected():
            # inside passwd file, there is a list of WiFi networks (CSV format)
            with open("passwd.dat") as f:
                data = f.readlines()
            # Search WiFis in range
            ssids_found = wlan_sta.scan()

            # matching...
            for ipass in data:
                ssid_list = ipass.strip("\n").split(";")

                for i in ssids_found:
                    if ssid_list[0] in i[0]:
                        print("OK. WiFi found.")
                        if do_connect(ssid_list[0], ssid_list[1]):
                            return True

            if not wlan_sta.isconnected():
                if networkconfig.start():
                    return True
        else:
            return True

    except OSError:
        # start web server for connection manager:
        if networkconfig.start():
            return True

    return False


if check_connection():

    # Main Code is here
    print("ESP OK")
    # to import your code;
    # import sample_mqtt.py

else:
    print("There is something wrong.")
