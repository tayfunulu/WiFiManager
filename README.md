# WiFi Manager

Lang   : Micropython 
Tested : 1.8 and 1.9.2 (updated)

<b>Description</b> : WiFi manager for ESP8266 - ESP12 for micropython 

<b>Main Features:</b>

- Web based connection manager 
- Save wifi password in passwd.dat (csv format) 
- Easy to apply 

<b>Usage:</b>

Upload main.py and networkconfig.py to ESP. 
Write your code into main.py or import it from main.py. 

<b>Logic:</b>
1. step: Check passwd.dat file and try saved networks/passwords.
2. step: Publish web page to configure new wifi. 
3. step: Save network/password to passwd.dat file. 
4. step: Run user code.

![alt text](https://github.com/tayfunulu/WiFiManager/blob/master/WiFi_Manager.png)

**networkconfig.py based on code of CPOPP - https://github.com/cpopp/MicroPythonSamples
