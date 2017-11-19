import network
import socket
import ure
import time

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

# setup for ssid 
ssid_name= "WifiManager"
ssid_password = "tayfunulu"

server_socket = None

def do_connect(ntwrk_ssid, netwrk_pass):
	sta_if = network.WLAN(network.STA_IF)
	sta_if.active(True)
	if not sta_if.isconnected():
		print('try to connect : '+ntwrk_ssid+' network...')
		sta_if.active(True)
		sta_if.connect(ntwrk_ssid, netwrk_pass)
		a=0
		while not sta_if.isconnected() | (a > 99) :
			time.sleep(0.1)
			a+=1
			print('.', end='')
		if sta_if.isconnected():
			print('\nConnected. Network config:', sta_if.ifconfig())
			return (True)
		else : 
			print('\nProblem. Not Connected to :'+ntwrk_ssid)
			return (False)

def send_response(client, payload, status_code=200):
	client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
	client.sendall("Content-Type: text/html\r\n")
	client.sendall("Content-Length: {}\r\n".format(len(payload)))
	client.sendall("\r\n")
	
	if len(payload) > 0:
		client.sendall(payload)

def handle_root(client):
	global wlan_sta
	response_header = """
		<html><h1 style="color: #5e9ca0; text-align: center;"><span style="color: #ff0000;">Wi-Fi Client Setup</span></h1>
		<form action="configure" method="post">
		<table style="margin-left: auto; margin-right: auto;">
		<tbody><tr><td>Wifi Name</td>
		<td style="text-align: center;"><select id="ssid" name="ssid">
	"""
	wlan_sta.active(True)

	response_variable = ""
	for ssid, *_ in wlan_sta.scan():
		response_variable += '<option value="{0}">{0}</option>'.format(ssid.decode("utf-8"))
	
	response_footer = """
		</select></td></tr>
		<tr><td>Password</td>
		<td><input name="password" type="password" /></td>
		</tr></tbody>
		</table>
		<p style="text-align: center;"><input type="submit" value="Submit" /></p>
		</form>
		<p>&nbsp;</p>
		<hr />
		<h5><span style="color: #ff0000;">!!! your ssid and password information will save "passwd.dat" file inside of your esp module to use next time... be careful for security !!!</span></h5>
		<hr />
		<h2 style="color: #2e6c80;">Some useful infos:</h2>
		<ul>
		<li>Wi-Fi Client for Micropython GitHub from&nbsp;<a href="https://github.com/cpopp/MicroPythonSamples" target="_blank" rel="noopener">cpopp</a></li>
		<li>My github adress <a href="https://github.com/tayfunulu" target="_blank" rel="noopener">tayfunulu</a></li>
		</ul>
		</html>
	"""
	send_response(client, response_header + response_variable + response_footer)

def handle_configure(client, request):
	match = ure.search("ssid=([^&]*)&password=(.*)", request)

	if match is None:
		send_response(client, "Parameters not found", status_code=400)
		return (False)
	# version 1.9 compatibility
	try:
		ssid = match.group(1).decode("utf-8").replace("%3F","?").replace("%21","!")
		password = match.group(2).decode("utf-8").replace("%3F","?").replace("%21","!")
	except:
		ssid = match.group(1).replace("%3F","?").replace("%21","!")
		password = match.group(2).replace("%3F","?").replace("%21","!")
	
	
	if len(ssid) == 0:
		send_response(client, "SSID must be provided", status_code=400)
		return (False)

	if do_connect(ssid, password):
		response_footer = """
		<html>
		<center><br><br>
		<h1 style="color: #5e9ca0; text-align: center;"><span style="color: #ff0000;">:) YES, Wi-Fi Configured to """+ssid+"""</span></h1>
		<br><br>"""
		send_response(client, response_footer)
		try:
			fo = open("passwd.dat","r")
			ex_data = fo.read()
			fo.close()
			fo = open("passwd.dat","w")
			ex_data = ssid+";"+password+"\n"+ex_data
			fo.write(ex_data)
			fo.close()
		except:
			fo = open("passwd.dat","w")
			fo.write(ssid+";"+password+"\n")
			fo.close()
		
		return (True)
	else:
		response_footer = """
		<html>
		<center>
		<h1 style="color: #5e9ca0; text-align: center;"><span style="color: #ff0000;">Wi-Fi Not Configured to """+ssid+"""</span></h1>
		<br><br>
		<form>
			<input type="button" value="Go back!" onclick="history.back()"></input>
		</form></center></html>
		"""
		send_response(client, response_footer )
		return (False)

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
	
	wlan_ap.config(essid=ssid_name,password=ssid_password)
	
	
	server_socket = socket.socket()
	server_socket.bind(addr)
	server_socket.listen(1)
	
	print('Connect to Wifi ssid :'+ssid_name+' , Default pass: '+ssid_password)
	print('And connect to esp via your favorite web browser (like 192.168.4.1)')
	print('listening on', addr)
	
	while True:
		
		if wlan_sta.isconnected():
			client.close
			return (True)
		
		client, addr = server_socket.accept()
		client.settimeout(5.0)
		
		print('client connected from', addr)

		request = b""
		try:
			while not "\r\n\r\n" in request:
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
