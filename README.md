# WiFi Manager

Lang   : Micropython 
Tested : 1.15

<b>Description</b> : WiFi manager for ESP8266 - ESP12 - ESP32 for micropython 

<b>Main Features:</b>

- Web based connection manager 
- Save wifi password in "wifi.dat" (csv format) 
- Easy to apply 

<b>Added Features:</b>
 - Add Json response feature instead of html
 - Can Integrate to any native app with json response

<b>Usage:</b>

Upload main.py and wifimanager-html.py to ESP.(for configure with browser) 
Use wifimanager-json.py to ESP.(for configure with Native App) 
Write your code into main.py or import it from main.py. 

 - 192.168.1.4 will return available network ssid in json response.
 - 192.168.1.4/configure send ssid and password in json data and it will return success/failed message in  json response.

<b>Logic:</b>
1. step: Check "wifi.dat" file and try saved networks/passwords.
2. step: Publish web page to configure new wifi. 
3. step: Save network/password to "wifi.dat" file. 
4. step: Run user code.

![alt text](https://github.com/tayfunulu/WiFiManager/blob/master/WiFi_Manager.png)

**web server based on code of CPOPP - https://github.com/cpopp/MicroPythonSamples
