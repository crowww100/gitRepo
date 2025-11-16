import os
import requests
import math
import time
from io import StringIO
import paho.mqtt.client as mqtt
import json

## Basis-URL SonnenBatterie API: #######################################################
BASE_URL_SB = 'http://192.168.1.200/api/v2'
########################################################################################


#command to get Car data################################################################
#cmd="sudo evcc -l debug vehicle" 
########################################################################################


## Basis-URL for PV API: ###############################################################
BASE_URL_PVforecast= 'http://www.solarprognose.de/web/solarprediction/api/v1?access-token=8aa7b41a5b40469ca96a43585874b160&project=Geheim.IX@gmx.de&type=daily'
########################################################################################


## Basis-URL Go-e charger ##############################################################
BASE_URL_GOe_status = 'https://244909.api.v3.go-e.io/api/status?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&filter=car,amp,nrg,frc'
BASE_URL_GOe_stop = 'https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&frc=1'
BASE_URL_GOe_start = 'https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&frc=0'
BASE_URL_GOe_AMP = 'https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&amp='
BASE_URL_GOe_Phase='https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&psm=' #1=1phase. 2=3phase
########################################################################################


# MQTT-parameter#######################################################################
hostname = os.getenv("MQTT_HOST", "mosquitto")
broker_port = int(os.getenv("MQTT_PORT", 1883))
topic = "ChargingManager"
topic2 ="ChargeData"
########################################################################################


## global variables#####################################################################
PVpower=0
PVpowerDayMax=0
SOC_SB=0
SOC_car=0
SOC_target = 80
chargeStatus=0 #1=GOe ready no car ,2= vehicle is charging 3=car plugged in and not charging,4= charging finished car connected
chargeStatus_old=99
chargeAMP=0

chargeMode=1 #0=automatic; 1=manuell
manualSpeed=1 #0=2kW; 1=4kW; 2=11kW

actChargePower=0
PV_excess_10min=0
PV_excess_10min_Array=[40] #10min
average_counter_10min=0

PV_excess_20min=0
PV_excess_20min_Array=[80] #20min
average_counter_20min=0

PV_excess =0
PV_4day_excess=0

PV_day0_Wh=0
PV_day1_Wh=0
PV_day2_Wh=0
PV_day3_Wh=0
PV_day4_Wh=0

PV_excess_day0_Wh=0
PV_excess_day1_Wh=0
PV_excess_day2_Wh=0
PV_excess_day3_Wh=0
PV_excess_day4_Wh=0

Home_consumption_act_W =0 #including GOe charger
Home_consumption_daily_Wh= 14000
charging_advice=0 #0=no charging needed, 1= charging recommended, 2=charging required
charging_advice_reason="everything ok"

timeNow=0
timePVforecast=0
timeCar=0
timeHouse=0


########################################################################################


# MQTT communication to frontend########################################################
def on_message(client, userdata, message):
    global chargeMode
    global manualSpeed
    data=str(message.payload.decode("utf-8"))
    print("message received " ,data)
    if data =="btnradio1":
       chargeMode=0
    if data =="btnradio2":
       chargeMode=1
    if data =="btnradio6":
       chargeMode=2
    if data =="btnradio3":
       manualSpeed=0
    if data =="btnradio4":
       manualSpeed=1
    if data =="btnradio5":
       manualSpeed=2

    #print("message topic=",message.topic)
    #print("message qos=",message.qos)
    #print("message retain flag=",message.retain)

    #objectData = data.split("/") # format = [nr,x_middle,y_middle, objLostCode]
    #client.disconnect()
    #move(objectData)
    return


# subscribe to MQTT-topic
ChargeManager_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,"ChargeManager_client")
ChargeManager_client.on_message=on_message #attach function to callback
ChargeManager_client.connect(hostname, broker_port, 60)
ChargeManager_client.subscribe(topic)

#start mqtt in the back
ChargeManager_client.loop_start()
########################################################################################


## read actual SOC_SB and actual PV generation power (W) ###############################
def get_houseData(query):
    global SOC_SB
    global PVpower
    global Home_consumption_act_W
    url = '%s/%s' % (BASE_URL_SB, query)
    try:
       res = requests.get(url, verify=False)
       if res.status_code == 200:
          #print(res.text)
          Data=res.text.split(",")
          Home_consumption_act_W=Data[4].split(":")
          Home_consumption_act_W=int(Home_consumption_act_W[1])
          PVpower=Data[17].split(":")
          PVpower=int(PVpower[1])
          SOC_SB=Data[25].split(":")
          SOC_SB=int(SOC_SB[1])
    except requests.exceptions.HTTPError as errh:
       print ("Http Error:",errh)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errh) + "\n\n")
       f.close()
    except requests.exceptions.Timeout as errt:
       print ("Timeout Error:",errt)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errt) + "\n\n")
       f.close()
    except requests.exceptions.ConnectionError as errc:
       print ("Connection Error", errc)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errc) + "\n\n")
       f.close()
    except requests.exceptions.RequestException as err:
       print ("Unknown Error:",err)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(err) + "\n\n")
       f.close()

    return
#######################################################################################


## read actual car SOC#################################################################
#def get_carData():
#    global SOC_car
#    carData=os.popen(cmd)
#    carString=carData.read()
#    print(carString)
#    carData=carString.split('\n')
#    carData=carData[3].replace(" ","")
#    carData=carData.split(':')
#    SOC_car=int(carData[1].replace("%",""))

#    return
#######################################################################################


## get PV forecast#####################################################################
def get_PVforecast():
    global PV_day0_Wh
    global PV_day1_Wh
    global PV_day2_Wh
    global PV_day3_Wh
    global PV_day4_Wh
    try:
       res = requests.get(BASE_URL_PVforecast)
       res = res.text.replace('}','')
       #print (res.text)
       PVforecastData=res.split('[')
       PVforecastData[2]=PVforecastData[2].replace(']','')
       PVforecastData[3]=PVforecastData[3].replace(']','')
       PVforecastData[4]=PVforecastData[4].replace(']','')
       PVforecastData[5]=PVforecastData[5].replace(']','')
       PVforecastData[6]=PVforecastData[6].replace(']','')


       PV_day0_Wh=PVforecastData[2].split(',')
       PV_day1_Wh=PVforecastData[3].split(',')
       PV_day2_Wh=PVforecastData[4].split(',')
       PV_day3_Wh=PVforecastData[5].split(',')
       PV_day4_Wh=PVforecastData[6].split(',')

       PV_day0_Wh=int(float(PV_day0_Wh[1])*1000)
       PV_day1_Wh=int(float(PV_day1_Wh[1])*1000)
       PV_day2_Wh=int(float(PV_day2_Wh[1])*1000)
       PV_day3_Wh=int(float(PV_day3_Wh[1])*1000)
       PV_day4_Wh=int(float(PV_day4_Wh[1])*1000)

    except requests.exceptions.HTTPError as errh:
       print ("Http Error:",errh)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errh) + "\n\n")
       f.close()
    except requests.exceptions.Timeout as errt:
       print ("Timeout Error:",errt)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errt) + "\n\n")
       f.close()
    except requests.exceptions.ConnectionError as errc:
       print ("Connection Error", errc)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errc) + "\n\n")
       f.close()
    except requests.exceptions.RequestException as err:
       print ("Unknown Error:",err)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(err) + "\n\n")
       f.close()

       return
#####################################################################################


## calc PV excess####################################################################
def calc_PV_excess():
    global PV_excess_day0_Wh
    global PV_excess_day1_Wh
    global PV_excess_day2_Wh
    global PV_excess_day3_Wh
    global PV_excess_day4_Wh

    PV_excess_day0_Wh = PV_day0_Wh - Home_consumption_daily_Wh
    PV_excess_day1_Wh = PV_day1_Wh - Home_consumption_daily_Wh
    PV_excess_day2_Wh = PV_day2_Wh - Home_consumption_daily_Wh
    PV_excess_day3_Wh = PV_day3_Wh - Home_consumption_daily_Wh
    PV_excess_day4_Wh = PV_day4_Wh - Home_consumption_daily_Wh
#####################################################################################


## calc SOC_target###################################################################
def calc_SOC_target():
    global SOC_target

    if PV_4day_excess <24000 and PV_excess_day1_Wh < 20000 and PV_excess_day2_Wh < 20000 and PV_excess_day3_Wh < 20000 and PV_excess_day4_Wh < 20000:
       SOC_target = 80
    elif PV_4day_excess >140000: #4 very sunny days ahead
       SOC_target = 60
    else:
       SOC_target = 70
    SOC_target=80 #debug######################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return
#####################################################################################


## calc charge advice################################################################
def calc_charge_advice():
    global charging_advice
    global charging_advice_reason
    global PV_4day_excess

    if PV_excess_day1_Wh<0:
       PV_excess_day1_Wh_tmp=0
    else:
       PV_excess_day1_Wh_tmp=PV_excess_day1_Wh

    if PV_excess_day2_Wh<0:
       PV_excess_day2_Wh_tmp=0
    else:
       PV_excess_day2_Wh_tmp=PV_excess_day2_Wh

    if PV_excess_day3_Wh<0:
       PV_excess_day3_Wh_tmp=0
    else:
       PV_excess_day3_Wh_tmp=PV_excess_day3_Wh

    if PV_excess_day4_Wh<0:
       PV_excess_day4_Wh_tmp=0
    else:
       PV_excess_day4_Wh_tmp=PV_excess_day4_Wh

    PV_4day_excess= PV_excess_day1_Wh_tmp+PV_excess_day2_Wh_tmp+PV_excess_day3_Wh_tmp+PV_excess_day4_Wh_tmp

    #charge advice logic__________________________
    if SOC_car<20:
       charging_advice=2 #charging required
       charging_advice_reason="SOC below 20%"
    elif SOC_car<31 and PV_excess_day0_Wh>6000 and PVpowerDayMax > 2000:
       charging_advice=1 #charging recommended
       charging_advice_reason="SOC below31% and cheap energy available"
    elif SOC_car<42 and PV_excess_day0_Wh>6000 and PV_excess_day1_Wh < 9000 and PV_excess_day2_Wh<9000 and PVpowerDayMax > 2000:
       charging_advice=1 #charging recommended
       charging_advice_reason="cheap energy available and bad weather for next 2 days expected"
    elif SOC_car<53 and PV_excess_day0_Wh>6000 and PV_excess_day1_Wh < 9000 and PV_excess_day2_Wh<9000 and PV_excess_day3_Wh<9000 and PVpowerDayMax > 2000:
       charging_advice=1 #charging recommended
       charging_advice_reason="cheap energy available and bad weather for next 3 days expected"
    elif SOC_car<64 and PV_excess_day0_Wh>6000 and PV_excess_day1_Wh < 9000 and PV_excess_day2_Wh<9000 and PV_excess_day3_Wh<9000 and PV_excess_day4_Wh<9000 and PVpowerDayMax > 2000:
       charging_advice=1 #charging recommended
       charging_advice_reason="cheap energy available and bad weather for next 4 days expected"
    else:
       charging_advice=0 #no charging necessary
       charging_advice_reason="everything ok"
    #____________________________________________
    return
#######################################################################################


## get GOe charger data ###############################################################
def get_GOe_data():
    global chargeStatus
    global chargeAMP
    global actChargePower
    try:
       res = requests.get(BASE_URL_GOe_status)
       if res.status_code == 200:
          res = res.text.replace('}','')
          GOe_data=res.split(',')
          chargeStatus=GOe_data[0].split(':')
          chargeStatus=int(chargeStatus[1])    #1=GOe ready no car ,2= vehicle is charging 3=car plugged in and not charging,4= charging finished car connected
          chargeAMP=GOe_data[1].split(':')
          chargeAMP=int(chargeAMP[1])
          actChargePower=int(float(GOe_data[13]))
    except requests.exceptions.HTTPError as errh:
       print ("Http Error:",errh)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errh) + "\n\n")
       f.close()
    except requests.exceptions.Timeout as errt:
       print ("Timeout Error:",errt)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errt) + "\n\n")
       f.close()
    except requests.exceptions.ConnectionError as errc:
       print ("Connection Error", errc)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errc) + "\n\n")
       f.close()
    except requests.exceptions.RequestException as err:
       print ("Unknown Error:",err)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(err) + "\n\n")
       f.close()

    return
#######################################################################################


## cyclic data collection #############################################################
def cyclicDataCollection():
    global timePVforecast
    global timeCar
    global timeHouse
    global weekday
    global weekday_last
    global PVpowerDayMax
    global PV_excess_10min
    global PV_excess_20min
    global PV_excess_10min_Array
    global PV_excess_20min_Array
    global average_counter_10min
    global average_counter_20min
    global PV_excess


    timeNow=math.floor(time.time()) #get current time in seconds
    if timeNow-timePVforecast > 3600:  #1x per hour
       get_PVforecast()
       calc_PV_excess()
#       print_status()

       #reset PVpowerDayMax at day change
       weekday=time.ctime()
       weekday=weekday.split(' ')
       weekday=weekday[0]
       if weekday != weekday_last:
          weekday_last = weekday
          PVpowerDayMax =0
       timePVforecast=timeNow

    #if timeNow-timeCar > 300: #1x per 5min
    #   try:
    #      get_carData()
    #   except:
    #      print("Exception occured while reading CAR SOC")
    #      f = open("Errorfile.txt", "a")
    #      f.write(time.ctime()+ "\n" + "ERR reading Car_SOC" + "\n\n")
    #      f.close()

    #   timeCar=timeNow

    if timeNow-timeHouse > 15: #1x per 5sec
       get_houseData('status')
       get_GOe_data()
       if PVpower > PVpowerDayMax:
          PVpowerDayMax = PVpower

       PV_excess=PVpower-Home_consumption_act_W+actChargePower
       PV_excess_10min_Array[average_counter_10min]=PV_excess
       average_counter_10min = average_counter_10min + 1
       if average_counter_10min==40: #120 bei 5s
          average_counter_10min=0
       PV_excess_10min=0
       for a in PV_excess_10min_Array:
          PV_excess_10min = PV_excess_10min + a
       PV_excess_10min= int(PV_excess_10min/40)

       PV_excess_20min_Array[average_counter_20min]=PV_excess
       average_counter_20min = average_counter_20min + 1
       if average_counter_20min==80:
          average_counter_20min=0
       PV_excess_20min=0
       for a in PV_excess_20min_Array:
          PV_excess_20min = PV_excess_20min + a
       PV_excess_20min= int(PV_excess_20min/80)


       timeHouse=timeNow
#       print_status()
    return
#######################################################################################


## charge ctrl#########################################################################
def charge_ctrl():

    # set start parameters for charging___________________________
    global chargeStatus_old
    chargingActive=0
    chargingActive_old=0
    phaseMode=1 #1= charge with 1 phase, 2=charge with 3 phases
    lockPhaseMode2=0
    chargeAmpReq=6
    chargeAmpReq_old=6
    charge_ctrl=1
    printTimer=0


    try:
       requests.get(BASE_URL_GOe_Phase+str(phaseMode))  #set to initial condition
    except requests.exceptions.HTTPError as errh:
       print ("Http Error:",errh)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errh) + "\n\n")
       f.close()
    except requests.exceptions.Timeout as errt:
       print ("Timeout Error:",errt)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errt) + "\n\n")
       f.close()
    except requests.exceptions.ConnectionError as errc:
       print ("Connection Error", errc)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errc) + "\n\n")
       f.close()
    except requests.exceptions.RequestException as err:
       print ("Unknown Error:",err)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(err) + "\n\n")
       f.close()

    try:
       requests.get(BASE_URL_GOe_AMP+str(chargeAmpReq)) #set to initial condition
    except requests.exceptions.HTTPError as errh:
       print ("Http Error:",errh)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errh) + "\n\n")
       f.close()
    except requests.exceptions.Timeout as errt:
       print ("Timeout Error:",errt)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errt) + "\n\n")
       f.close()
    except requests.exceptions.ConnectionError as errc:
       print ("Connection Error", errc)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(errc) + "\n\n")
       f.close()
    except requests.exceptions.RequestException as err:
       print ("Unknown Error:",err)
       f = open("Errorfile.txt", "a")
       f.write(time.ctime()+ "\n" + str(err) + "\n\n")
       f.close()

    #_____________________________________________________________


    print("_______________________________________________________________________________")
    print("_______________________________________________________________________________")
    print("________________________entering charge ctrl mode______________________________")
    print("")

    # main charge loop____________________________________________
    while charge_ctrl==1:
       cyclicDataCollection()
       calc_SOC_target()

       if chargeMode==0: #automatic mode

          #activate charging
          if (SOC_SB > 25 and PV_excess_10min > 2000) or (SOC_SB >70 and PV_excess_10min > 1500):
             chargingActive = 1

          #deactivate charging
          if PV_excess_20min < 0 or (SOC_SB < 25 and PV_excess_10min < 0) or (SOC_SB >25 and SOC_SB < 50 and PV_excess_10min < -1000) or (SOC_SB < 70 and SOC_SB > 50 and PV_excess_10min < -1500):
             chargingActive = 0

          if SOC_car >= SOC_target:
             chargingActive = 0


          #select number of phases
          if chargingActive == 1:
             if phaseMode==1 and PV_excess_10min > 5000 and PV_excess_20min > 5000 and lockPhaseMode2==0 and SOC_SB > 40:
                phaseMode=2
                requests.get(BASE_URL_GOe_Phase+str(phaseMode))
             #if phaseMode==1 and PV_excess_20min > 4500 and SOC_SB > 55:
             #   phaseMode=2
             #   requests.get(BASE_URL_GOe_Phase+str(phaseMode))


             if phaseMode==2 and PV_excess_10min < 3000 and SOC_SB < 50:
                phaseMode=1
                requests.get(BASE_URL_GOe_Phase+str(phaseMode))
                lockPhaseMode2=1 #prevent toggel between 1 and 3 phases
             if phaseMode==2 and PV_excess_20min < 3500:
                phaseMode=1
                requests.get(BASE_URL_GOe_Phase+str(phaseMode))
                lockPhaseMode2=1 #prevent toggel between 1 and 3 phases


          #calc and set charging current
          if chargingActive == 1:
             if phaseMode==1:
                chargeAmpReq=math.floor(PV_excess/223)
             else:
                chargeAmpReq=math.floor(PV_excess/669) #223V*3

          if chargeAmpReq>16:
             chargeAmpReq=16
          if chargeAmpReq<6:
             chargeAmpReq=6

          if chargeAmpReq != chargeAmpReq_old:
             chargeAmpReq_old=chargeAmpReq
             requests.get(BASE_URL_GOe_AMP+str(chargeAmpReq))
             time.sleep(10) #wait 10s for stabilization

          #send activate/deactivate message
          if chargingActive == 1 and chargingActive_old == 0:
             requests.get(BASE_URL_GOe_start)
             chargingActive_old = chargingActive

          if chargingActive == 0 and chargingActive_old == 1:
             requests.get(BASE_URL_GOe_stop)
             chargingActive_old = chargingActive

       if chargeMode==1: #manual mode
          if manualSpeed == 0: #2kW --> 1 phase
             chargeAmpReq=9
             requests.get(BASE_URL_GOe_AMP+str(chargeAmpReq))
          else: #4kW @ 1 phase or 11kW @ 2 phases
             chargeAmpReq=16
             requests.get(BASE_URL_GOe_AMP+str(chargeAmpReq))


          if manualSpeed == 2 and phaseMode !=2: #11kW --> 3 phases
             phaseMode=2
             requests.get(BASE_URL_GOe_Phase+str(phaseMode))
          if manualSpeed !=2 and phaseMode==2:
             phaseMode=1
             requests.get(BASE_URL_GOe_Phase+str(phaseMode))

          if chargingActive==0:
             requests.get(BASE_URL_GOe_start) #start charging
             chargingActive = 1
       else:
          requests.get(BASE_URL_GOe_stop)



       #print charging data every 10s
       printTimer = printTimer + 1
       if printTimer==10:
          printTimer=0

          print("ChargeMode                  ",chargeMode)
          print("ChargeSpeed in manual mode  ",manualSpeed)
          print("Time:                       ",time.ctime())
          print("SOC_target in %             ",SOC_target)
          print("SOC_SB in %                 ",SOC_SB)
          print("charging active:            ",chargingActive)
          print("SOC car in %:               ",SOC_car)
          print("Phase mode:                 ",phaseMode)
          print("Requested current in A:     ",chargeAmpReq)
          print("PV_excess act in W:         ",PV_excess)
          print("PV_excess 10min in W:       ",PV_excess_10min)
          print("PV_excess 20min in W:       ",PV_excess_20min)
          print("PV act:                     ",PVpower)
          print("act Power consumption in W: ",Home_consumption_act_W)
          print("")

       if chargeStatus == 1:  #1=GOe ready no car ,2= vehicle is charging 3=car plugged in and not charging,4= charging finished car connected
          charge_ctrl = 0

       #send current connection status to frontend
       url='http://192.168.1.100:5001/DataFromChargeManager'
       if chargeStatus != chargeStatus_old:
          chargeStatus_old = chargeStatus
          message={'chargeStatus': chargeStatus}
          resp=requests.post(url, json = message)

       time.sleep(1)
    #____________________________________________________________
    print("_______________________________________________________________________________")
    print("_______________________________________________________________________________")
    print("________________________leave charge ctrl mode______________________________")
    print("")

    return
#######################################################################################


## print status #######################################################################
def print_status():
    print (time.ctime())

    print("")
    print("ChargeMode                    ",chargeMode)
    print("ChargeSpeed in manual mode    ",manualSpeed)

    print("SOC_target in %               ",SOC_target)
    print("SOC_SB in %:                  ",SOC_SB)
    print("SOC_car in %:                 ",SOC_car)
    print("PV_power in W:                ",PVpower)
    print("Maximum PV power this day     ",PVpowerDayMax)
    print("act Power consumption in W:   ",Home_consumption_act_W)

    print("")

    print("charge status:                ",chargeStatus)
    print("selected Phase current in A:  ",chargeAMP)
    print("PV_excess 10min in W:         ",PV_excess_10min)
    print("PV_excess 20min in W:         ",PV_excess_20min)


    print("")

    print("PV forecast for day 0 in Wh:  ",PV_day0_Wh)
    print("PV forecast for day 1 in Wh:  ",PV_day1_Wh)
    print("PV forecast for day 2 in Wh:  ",PV_day2_Wh)
    print("PV forecast for day 3 in Wh:  ",PV_day3_Wh)
    print("PV forecast for day 4 in Wh:  ",PV_day4_Wh)

    print("")

    print("PV excess for day 0 in Wh:    ",PV_excess_day0_Wh)
    print("PV excess for day 1 in Wh:    ",PV_excess_day1_Wh)
    print("PV excess for day 2 in Wh:    ",PV_excess_day2_Wh)
    print("PV excess for day 3 in Wh:    ",PV_excess_day3_Wh)
    print("PV excess for day 4 in Wh:    ",PV_excess_day4_Wh)

    print("")

    print("Charging advice:              ",charging_advice)
    print("advice reason:                ",charging_advice_reason)
    print("")
    print("_______________________________________________________________________________")
    print("")
    print("")
    return
#######################################################################################







##### MAIN-loop########################################################################

# client will loop forever --> can handle reconnections, can only be stopped via PanTilt_cli>
#ChargeManager_client.loop_forever()


#collect initial data
get_houseData('status')
#try:
#   get_carData()
#except:
#   print("Exception occured while reading CAR SOC")
#   f = open("Errorfile.txt", "a")
#   f.write(time.ctime()+ "\n" + "ERR reading Car_SOC" + "\n\n")
#   f.close()
get_PVforecast()
get_GOe_data()
calc_PV_excess()
calc_charge_advice()
print_counter=0

weekday=time.ctime()
weekday=weekday.split(' ')
weekday=weekday[0]
weekday_last=weekday

PVpowerDayMax = PVpower
PV_excess_10min=PVpower-Home_consumption_act_W+actChargePower
PV_excess_20min=PV_excess_10min
PV_excess_10min_Array=[PV_excess_10min for i in range(40)] #init whole array with act PowerReq
PV_excess_20min_Array=[PV_excess_20min for i in range(80)] #init whole array with act PowerReq


print_status()

requests.get(BASE_URL_GOe_stop) #no charging allowed when car is connected

#start timer for data collection
timeNow=math.floor(time.time()) #get current time in seconds
timePVforecast=timeNow
timeCar=timeNow
timeHouse=timeNow

while 1:
   cyclicDataCollection() #incl print every hour
   calc_charge_advice()

   #change to charge ctrl if car is connected to charger
   if chargeStatus == 3 or chargeStatus==4:
      charge_ctrl()
   print_counter= print_counter+1
   if print_counter>10:
      print_counter=0
      print_status()

   #send current connection status to frontend
   url='http://192.168.1.100:5001/DataFromChargeManager'
   if chargeStatus != chargeStatus_old:
      chargeStatus_old = chargeStatus
      message={'chargeStatus': chargeStatus}
      resp=requests.post(url, json = message)

   time.sleep(1)
#######################################################################################
