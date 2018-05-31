import network
import socket
import ure
import time

ap_ssid = "WifiManager"
ap_password = "tayfunulu"
ap_authmode = 3  # WPA2

NETWORK_PROFILES = 'wifi.dat'

html_head = """
    <head>
        <title>WiFi Manager</title>
        <style>
            body {
                margin: 0px 20px;
                font-family: "Roboto", "Helvetica", "Arial", sans-serif;
            }

            ul {
                list-style-type: none;
                padding: 0px;
            }

            li {
                margin: 0px -10px;
                padding: 10px 10px 10px 10px;
            }

            a, h1, h2, h3 {
                color: #333;
                text-decoration: none;
            }

            p > a {
                text-decoration: underline;
            }

            a > li,
            li[onclick] {
                background-color: #ffffff00;
                transition: background-color .5s;
            }

            a:hover li, a:active li,
            li:hover[onclick], li:active[onclick] {
                background-color: #ddd;
                cursor: pointer;
            }

            h1, form {
                position: relative;
                max-width: 750px;
                width: 100%;
                margin: auto;
            }

            h1 {
                margin: 10px auto;
            }

            h2 {
                margin: 10px 0px -10px 0px;
            }

            select:-moz-focusring {
                color: transparent;
                text-shadow: 0 0 0 #000;
            }

            button {
                position: relative;
                max-width: 750px;
                width: 100%;
                margin: auto;
                padding: 10px 10px 10px 10px;
                display: block;
                text-align: left;
                border: none;
                background: transparent;
                font-size: 1em;
                background-color: #ffffff00;
                transition: background-color .5s;
            }

            button:hover, button:active {
                background-color: #ddd;
                cursor: pointer;
            }

            #submit {
                border: none;
                background: transparent;
                padding: 0px;
                font-size: 1em;
            }

            .monospace {
                font-family: 'Roboto Mono', monospace;
            }

            .fixedWidth {
                width: 100px;
                display: inline-block;
            }

            .placeholder {
                padding-bottom: 20px;
            }
        </style>
    </head>
"""

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None


def get_connection():
    """return a working WLAN(STA_IF) instance or None"""

    # First check if there already is any connection:
    if wlan_sta.isconnected():
        return wlan_sta

    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta

        # Read known network profiles from file
        profiles = read_profiles()

        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print("skipping unknown encrypted network")
            else:  # open
                connected = do_connect(ssid, None)
            if connected:
                break

    except OSError as e:
        print("exception", str(e))

    # start web server for connection manager:
    if not connected:
        connected = start()

    return wlan_sta if connected else None


def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles


def write_profiles(profiles):
    lines = []
    for ssid, password in profiles.items():
        lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))


def do_connect(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(100):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', wlan_sta.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return connected


def send_header(client, status_code=200, content_length=None ):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
      client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


def handle_root(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())
    send_header(client)
    client.sendall("<html>")
    client.sendall(html_head)
    client.sendall("""\
            <body>
                <form action="configure" method="post">
                    <h1>
                        Wi-Fi Client Setup
                    </h1>
                    <h2>
                        SSIDs (click to select)
                    </h2>
                    <ul>
    """)
    while len(ssids):
        ssid = ssids.pop(0)
        client.sendall("""\
                        <a onclick="document.getElementById('ssid').value = '{ssid}';" href="javascript:void(0)">
                            <li>
                                {ssid}
                            </li>
                        </a>
        """.format(ssid=ssid))
    client.sendall("""\
                        <li onclick="document.getElementById('ssid').focus()">
                            <span class="fixedWidth">SSID</span>
                            <input id="ssid" name="ssid" type="text"/>
                        </li>
                        <li onclick="document.getElementById('password').focus()">
                            <span class="fixedWidth">Password</span>
                            <input id="password" name="password" type="password"/>
                        </li>
                        <li onclick="document.getElementById('submit').click()">
                            <input id=submit type="submit" value="Submit" />
                        </li>
                    </ul>
                    <div class="placeholder"></div>
                    <h2>
                        Infos:
                    </h2>
                    <p>
                        Your ssid and password information will be saved into the "{filename}" file in your ESP module for future usage. Be careful about security!
                    </p>
                    <p>
                        Original code from <a href="https://github.com/cpopp/MicroPythonSamples" target="_blank" rel="noopener">cpopp/MicroPythonSamples</a>.
                    </p>
                    <p>
                        This code available at <a href="https://github.com/tayfunulu/WiFiManager" target="_blank" rel="noopener">tayfunulu/WiFiManager</a>.
                    </p>
                </form>
            </body>
        </html>
    """.format(filename=NETWORK_PROFILES))
    client.close()


def handle_configure(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False

    if do_connect(ssid, password):
        response = """\
            <html>
                {html_head}
                <body>
                    <h1>
                        ESP successfully connected to WiFi network "<span class="monospace">{ssid}</span>"
                    </h1>
                </body>
            </html>
        """.format(html_head=html_head, ssid=ssid)
        send_response(client, response)
        try:
            profiles = read_profiles()
        except OSError:
            profiles = {}
        profiles[ssid] = password
        write_profiles(profiles)

        time.sleep(5)

        return True
    else:
        response = """\
            <html>
                {html_head}
                <body>
                    <h1>
                        ESP could not connect to WiFi network "<span class="monospace">{ssid}</span>"
                    </h1>
                    <button onclick="history.back()">Go back</button>
                </body>
            </html>
        """.format(html_head=html_head, ssid=ssid)
        send_response(client, response)
        return False


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)

    print('Connect to WiFi ssid ' + ap_ssid + ', default password: ' + ap_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)

    while True:
        if wlan_sta.isconnected():
            return True

        client, addr = server_socket.accept()
        print('client connected from', addr)
        try:
            client.settimeout(15.0)
            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass

            print("Request is: {}".format(request))
            if "HTTP" not in request:  # skip invalid requests
                continue

            # version 1.9 compatibility
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))

            if url == "":
                handle_root(client)
            elif url == "configure":
                handle_configure(client, request)
            else:
                handle_not_found(client, url)

        finally:
            client.close()
