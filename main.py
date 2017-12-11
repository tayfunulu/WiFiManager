import network
import networkconfig
import time

wlan_sta = network.WLAN(network.STA_IF)


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
                lines = f.readlines()
            # Search WiFis in range
            ssids_found = wlan_sta.scan()

            # matching...
            for line in lines:
                ssid, password = line.strip("\n").split(";")
                for ssid_found in ssids_found:
                    if ssid in ssid_found[0]:
                        print("OK. WiFi found.")
                        if networkconfig.do_connect(ssid, password):
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
