import network
import socket
import ure
import time

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

# SSID/Password for setup
ssid_name = "WifiManager"
ssid_password = "tayfunulu"

server_socket = None


def do_connect(ssid, password):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if sta_if.isconnected():
        return None
    print('Trying to connect to %s...' % ssid)
    sta_if.connect(ssid, password)
    for retry in range(100):
        connected = sta_if.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', sta_if.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return connected


def send_response(client, payload, status_code=200):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    client.sendall("Content-Length: {}\r\n".format(len(payload)))
    client.sendall("\r\n")

    if len(payload) > 0:
        client.sendall(payload)


def handle_root(client):
    global wlan_sta
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())

    response = []
    response.append("""\
        <html>
            <h1 style="color: #5e9ca0; text-align: center;">
                <span style="color: #ff0000;">
                    Wi-Fi Client Setup
                </span>
            </h1>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)

    for ssid in ssids:
        response.append("""\
                        <tr>
                            <td colspan="2">
                                <input type="radio" name="ssid" value="{0}" />{0}
                            </td>
                        </tr>
        """.format(ssid))

    response.append("""\
                        <tr>
                            <td>Password:</td>
                            <td><input name="password" type="password" /></td>
                        </tr>
                    </tbody>
                </table>
                <p style="text-align: center;">
                    <input type="submit" value="Submit" />
                </p>
            </form>
            <p>&nbsp;</p>
            <hr />
            <h5>
                <span style="color: #ff0000;">
                    Your ssid and password information will be saved into the
                    "passwd.dat" file in your ESP module for future usage.
                    Be careful about security!
                </span>
            </h5>
            <hr />
            <h2 style="color: #2e6c80;">
                Some useful infos:
            </h2>
            <ul>
                <li>
                    Original code from <a href="https://github.com/cpopp/MicroPythonSamples"
                        target="_blank" rel="noopener">cpopp/MicroPythonSamples</a>.
                </li>
                <li>
                    This code available at <a href="https://github.com/tayfunulu/WiFiManager"
                        target="_blank" rel="noopener">tayfunulu/WiFiManager</a>.
                </li>
            </ul>
        </html>
    """)
    send_response(client, "\n".join(response))


def handle_configure(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False

    if do_connect(ssid, password):
        response = """\
            <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        try:
            with open("passwd.dat", "r") as f:
                ex_data = f.read()
        except:
            ex_data = ""
        ex_data = "%s;%s\n" % (ssid, password) + ex_data
        with open("passwd.dat", "w") as f:
            f.write(ex_data)
        return True
    else:
        response = """\
            <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket

    if server_socket:
        server_socket.close()


def start(port=80):
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    global server_socket
    global wlan_sta
    global wlan_ap
    global ssid_name
    global ssid_password
    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ssid_name, password=ssid_password)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)

    print('Connect to WiFi ssid ' + ssid_name + ', default password: ' + ssid_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)

    while True:

        if wlan_sta.isconnected():
            client.close
            return True

        client, addr = server_socket.accept()
        client.settimeout(5.0)

        print('client connected from', addr)

        request = b""
        try:
            while "\r\n\r\n" not in request:
                request += client.recv(512)
        except OSError:
            pass

        print("Request is: {}".format(request))
        if "HTTP" not in request:
            # skip invalid requests
            client.close()
            continue

        # version 1.9 compatibility
        try:
            url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
        except:
            url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
        print("URL is {}".format(url))

        if url == "":
            handle_root(client)
        elif url == "configure":
            handle_configure(client, request)
        else:
            handle_not_found(client, url)

        client.close()
