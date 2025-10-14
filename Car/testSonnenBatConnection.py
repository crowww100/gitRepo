
import os
import requests
import math
import time
from io import StringIO

## Basis-URL SonnenBatterie API: #######################################################
BASE_URL_SB = 'http://192.168.1.200/api/v2'
cmd="sudo evcc -l debug vehicle"
########################################################################################



## global variables#####################################################################
SOC_SB=0
PVpower=0
Home_consumption_act_W =0 #including GOe charger

callNr=0


## read actual SOC_SB and actual PV generation power (W) ###############################
def get_houseData(query):
    global SOC_SB
    global PVpower
    global Home_consumption_act_W
    url = '%s/%s' % (BASE_URL_SB, query)
    res = requests.get(url, verify=False)
    #print(res.text)
    if res.status_code == 200:
       Data=res.text.split(",")
       #print(Data[17])
       #print(Data[25])
       Home_consumption_act_W=Data[4].split(":")
       Home_consumption_act_W=int(Home_consumption_act_W[1])
       PVpower=Data[17].split(":")
       PVpower=int(PVpower[1])
       SOC_SB=Data[25].split(":")
       SOC_SB=int(SOC_SB[1])
       #print(Home_consumption_act_W)
       #print(PVpower)
       #print(SOC_SB)
    else:
       print ("Fehler! Status code =: " + res.status_code)
       print (res.text)
    return
#######################################################################################


##### MAIN-loop########################################################################
start=time.ctime()

while(1):
   get_houseData('status')
   callNr += 1
   print ("CallNr = : "+ str(callNr) + "      Time = : "+ time.ctime()+ "        SOC = "+ str(SOC_SB)+ "      startTime = : "+start)

   time.sleep(1)
#######################################################################################
