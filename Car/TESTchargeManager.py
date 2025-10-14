import os
import requests
import math
import time
from io import StringIO


## Basis-URL SonnenBatterie API: #######################################################
BASE_URL_SB = 'http://192.168.1.200/api/v2'
cmd="sudo evcc -l debug vehicle" 
########################################################################################


## Basis-URL for PV API: ###############################################################
BASE_URL_PVforecast= 'http://www.solarprognose.de/web/solarprediction/api/v1?access-token=8aa7b41a5b40469ca96a43585874b160&project=Geheim.IX@gmx.de&type=daily'
########################################################################################


## Basis-URL Go-e charger ##############################################################
BASE_URL_GOe_status = 'https://244909.api.v3.go-e.io/api/status?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&filter=car,amp,nrg'
BASE_URL_GOe_stop = 'https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&frc=1'
BASE_URL_GOe_start = 'https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&frc=0'
BASE_URL_GOe_AMP = 'https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&amp='
BASE_URL_GOe_Phase='https://244909.api.v3.go-e.io/api/set?token=Pk2P0PjZOUAsUiL5fn0BB0OFVf2AGgai&psm=' #1=1phase. 2=3phase
########################################################################################

## global variables#####################################################################
PVpower=0
PVpowerDayMax=0
SOC_SB=0
SOC_car=0

chargeStatus=0
chargeAMP=0
actChargePower=0

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


## read actual SOC_SB and actual PV generation power (W) ###############################
def get_houseData(query):
    global SOC_SB
    global PVpower
    global Home_consumption_act_W
    url = '%s/%s' % (BASE_URL_SB, query)
    res = requests.get(url)
    #print(res.text)
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
    return
#######################################################################################


## read actual car SOC#################################################################
def get_carData():
    global SOC_car
    carData=os.popen(cmd)
    carString=carData.read()
    #print(carString)
    carData=carString.split('\n')
    carData=carData[3].replace(" ","")
    carData=carData.split(':')
    SOC_car=int(carData[1].replace("%",""))

    #SOC_car = 21 #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!debug
    return
#######################################################################################


## get PV forecast#####################################################################
def get_PVforecast():
    global PV_day0_Wh
    global PV_day1_Wh
    global PV_day2_Wh
    global PV_day3_Wh
    global PV_day4_Wh
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

    PV_day0_Wh=int(PV_day0_Wh[1].replace('.',''))
    PV_day1_Wh=int(PV_day1_Wh[1].replace('.',''))
    PV_day2_Wh=int(PV_day2_Wh[1].replace('.',''))
    PV_day3_Wh=int(PV_day3_Wh[1].replace('.',''))
    PV_day4_Wh=int(PV_day4_Wh[1].replace('.',''))

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


## calc charge advice################################################################
def calc_charge_advice():
    global charging_advice
    global charging_advice_reason
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
    res = requests.get(BASE_URL_GOe_status)
    if res.status_code == 200:
       res = res.text.replace('}','')
       print(res)
       GOe_data=res.split(',')
       chargeStatus=GOe_data[0].split(':')
       chargeStatus=int(chargeStatus[1])    #1=GOe ready no car ,2= vehicle is charging 3=car plugged in and not charging,4= charging finished car connected
       chargeAMP=GOe_data[1].split(':')
       chargeAMP=int(chargeAMP[1])
       actChargePower=int(float(GOe_data[13])) #int(float()) because "float-string" can not be converted to int
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

    timeNow=math.floor(time.time()) #get current time in seconds
    if timeNow-timePVforecast > 3600:  #1x per hour
       get_PVforecast()
       calc_PV_excess()
       print_status()

       #reset PVpowerDayMax at day change
       weekday=time.ctime()
       weekday=weekday.split(' ')
       weekday=weekday[0]
       if weekday != weekday_last:
          weekday_last = weekday
          PVpowerDayMax =0
       timePVforecast=timeNow

    if timeNow-timeCar > 300: #1x per 5min
       get_carData()
       timeCar=timeNow

    if timeNow-timeHouse > 5: #1x per 5sec
       get_houseData('status')
       get_GOe_data()
       if PVpower > PVpowerDayMax:
          PVpowerDayMax = PVpower
       timeHouse=timeNow
    return
#######################################################################################


## charge ctrl#########################################################################
def charge_ctrl():

    # set start parameters for charging___________________________
    chargingActive=0
    phaseMode=1 #1= charge with 1 phase, 2=charge with 3 phases
    lockPhaseMode2=0
    chargeAmpReq=0
    charge_ctrl=1
    chargePowerReqArray=[120] #10min
    chargePowerReq=PVpower-Home_consumption_act_W+actChargePower
    chargePowerReqArray=[chargePowerReq for i in range(120)] #init whole array with act PowerReq
    i=0
    printTimer=0

    if chargePowerReq >4600:
       phaseMode=2
       requests.get(BASE_URL_GOe_Phase+str(phaseMode))
    else:
       phaseMode=1
       requests.get(BASE_URL_GOe_Phase+str(phaseMode))
    #_____________________________________________________________


    print("_______________________________________________________________________________")
    print("_______________________________________________________________________________")
    print("________________________entering charge ctrl mode______________________________")
    print("")

    # main charge loop____________________________________________
    while charge_ctrl==1:
       cyclicDataCollection()

       chargePowerReq=PVpower-Home_consumption_act_W+actChargePower-300

       #calc chargePowerReq average (10min)
       chargePowerReqArray[i]=chargePowerReq
       i = i + 1
       if i==120:
          i=0
       chargePowerReqAverage=0
       for a in chargePowerReqArray:
          chargePowerReqAverage= chargePowerReqAverage + a
       chargePowerReqAverage=chargePowerReqAverage/120

       #select number of phases
       if phaseMode==2 and chargePowerReqAverage < 4100:
          phaseMode=1
          lockPhaseMode2=1 #prevent toggel between 1 and 3 phases
          requests.get(BASE_URL_GOe_Phase+str(phaseMode))

       if lockPhaseMode2==0 and chargePowerReqAverage >4600:
          phaseMode=2
          requests.get(BASE_URL_GOe_Phase+str(phaseMode))

       #calc and set charging current
       if phaseMode==1:
          chargeAmpReq=math.floor(chargePowerReq/223)
       else:
          chargeAmpReq=math.floor(chargePowerReq/669) #223V*3

       if chargeAmpReq>16:
          chargeAmpReq=16
       if chargeAmpReq<6:
          chargeAmpReq=6

       requests.get(BASE_URL_GOe_AMP+str(chargeAmpReq))

       #activate charging
       if chargingActive==0 and chargePowerReqAverage >100: #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!2000
          requests.get(BASE_URL_GOe_start)
          chargingActive=1

       #deactivate charging (no PV, target reached, external stop)
       if chargingActive == 1 and (chargePowerReqAverage <1000 or chargeStatus==4): #!!!!!!!!!!!!!!!!!!!!!!prüfen des Verhaltens von chargeState bei SOC erreicht und manueller Abbruch
          requests.get(BASE_URL_GOe_stop)
          chargingActive=0
          charge_ctrl=0

       #print charging data every 10s
       printTimer = printTimer + 1
       if printTimer==10:
          printTimer=0
          print("Time:                       ",time.ctime())
          print("SOC car in %:               ",SOC_car)
          print("Phase mode:                 ",phaseMode)
          print("Requested current in A:     ",chargeAmpReq)
          print("Charge power act in W:      ",actChargePower)
          print("PV act:                     ",PVpower)
          print("act Power consumption in W: ",Home_consumption_act_W)
          print("")

       time.sleep(1)
    #____________________________________________________________

    return
#######################################################################################


## print status #######################################################################
def print_status():
    print (time.ctime())

    print("")

    print("SOC_SB in %: ",SOC_SB)
    print("SOC_car in %: ",SOC_car)
    print("PV_power in W: ",PVpower)
    print("Maximum PV power this day",PVpowerDayMax)
    print("act Power consumption in W: ",Home_consumption_act_W)

    print("")

    print("charge status: ",chargeStatus)
    print("selected Phase current in A: ",chargeAMP)
    print("actual charging power in W: ",actChargePower)

    print("")

    print("PV forecast for day 0 in Wh: ",PV_day0_Wh)
    print("PV forecast for day 1 in Wh: ",PV_day1_Wh)
    print("PV forecast for day 2 in Wh: ",PV_day2_Wh)
    print("PV forecast for day 3 in Wh: ",PV_day3_Wh)
    print("PV forecast for day 4 in Wh: ",PV_day4_Wh)

    print("")

    print("PV excess for day 0 in Wh: ",PV_excess_day0_Wh)
    print("PV excess for day 1 in Wh: ",PV_excess_day1_Wh)
    print("PV excess for day 2 in Wh: ",PV_excess_day2_Wh)
    print("PV excess for day 3 in Wh: ",PV_excess_day3_Wh)
    print("PV excess for day 4 in Wh: ",PV_excess_day4_Wh)

    print("")

    print("Charging advice: ",charging_advice)
    print("advice reason: ",charging_advice_reason)
    print("")
    print("_______________________________________________________________________________")
    print("")
    print("")
    return
#######################################################################################







##### MAIN-loop########################################################################

#collect initial data
get_houseData('status')
get_carData()
#get_PVforecast()
get_GOe_data()
calc_PV_excess()
calc_charge_advice()

weekday=time.ctime()
weekday=weekday.split(' ')
weekday=weekday[0]
weekday_last=weekday

PVpowerDayMax = PVpower

#print_status()

#requests.get(BASE_URL_GOe_stop) #no charging allowed when car is connected



#start timer for data collection
#timeNow=math.floor(time.time()) #get current time in seconds
#timePVforecast=timeNow
#timeCar=timeNow
#timeHouse=timeNow

while 1:
#   cyclicDataCollection() #incl print every hour
#   calc_charge_advice()

   #change to charge ctrl if car is connected to charger
#   if chargeStatus == 3:
#      charge_ctrl()
   get_GOe_data()
   print(chargeStatus)
   get_carData()
   print(SOC_car)
   time.sleep(1)

#######################################################################################
