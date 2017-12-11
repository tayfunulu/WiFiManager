import network
import networkconfig
import time

wlan_sta = network.WLAN(network.STA_IF)


def check_connection():
    global wlan_sta
    # First check if there already is any connection:
    if wlan_sta.isconnected():
        return True

    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return True

        # Read known network profiles from file
        profiles = networkconfig.read_profiles()

        # Search WiFis in range
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = networkconfig.do_connect(ssid, password)
                else:
                    print("skipping unknown encrypted network")
            else:  # open
                connected = networkconfig.do_connect(ssid, None)
            if connected:
                break

    except OSError:
        pass

    # start web server for connection manager:
    if not connected:
        connected = networkconfig.start()

    return connected


if check_connection():

    # Main Code is here
    print("ESP OK")
    # to import your code;
    # import sample_mqtt.py

else:
    print("There is something wrong.")
