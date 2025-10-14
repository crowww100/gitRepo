from flask import Flask, jsonify, render_template, Response, request, redirect, url_for
import requests
import paho.mqtt.client as mqtt


#Variables needed for MQTT-interface##########################################################################################################
hostname = "localhost"
broker_port = 1883
topic1 = "ChargingManager"
topic2 = "ChargeData"
##############################################################################################################################################


#Variables####################################################################################################################################
Speed=1
Mode=1
##############################################################################################################################################


#start MQTT-client############################################################################################################################
HMI_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,"HMI_client")
HMI_client.connect(hostname, broker_port, 60)
##############################################################################################################################################


#setup Flask & SQL-Database
app = Flask(__name__,static_url_path='/static' )



@app.route('/', methods=['GET', 'POST'])
def index():
    global Speed
    global Mode
    if request.method == "POST":
       if 'button' in request.form:
          res=request.form['button']
          print(res)
          message=res
          HMI_client.connect(hostname, broker_port, 60)
          HMI_client.publish(topic1, message)
          #HMI_client.disconnect(hostname)

       if 'btnradio1' in request.form:
          res=request.form['btnradio1']
          print(res)
          if res=="btnradio1":
             Mode=1
             message=res
             HMI_client.connect(hostname, broker_port, 60)
             HMI_client.publish(topic1, message)
             #HMI_client.connect(hostname, broker_port, 60)
             #HMI_client.publish(topic1, message)
             #HMI_client.disconnect(hostname)

          else:
             Mode=2
             message=res
             HMI_client.connect(hostname, broker_port, 60)
             HMI_client.publish(topic1, message)
             #HMI_client.connect(hostname, broker_port, 60)
             #HMI_client.publish(topic1, message)
             #HMI_client.disconnect(hostname)

       if 'btnradio2' in request.form:
          res=request.form['btnradio2']
          print(res)
          if res=="btnradio3":
             Speed=1
             message=res
             HMI_client.connect(hostname, broker_port, 60)
             HMI_client.publish(topic1, message)
             #HMI_client.connect(hostname, broker_port, 60)
             #HMI_client.publish(topic1, message)
             #HMI_client.disconnect(hostname)

          elif res=="btnradio4":
             Speed=2
             message=res
             HMI_client.connect(hostname, broker_port, 60)
             HMI_client.publish(topic1, message)
             #HMI_client.connect(hostname, broker_port, 60)
             #HMI_client.publish(topic1, message)
             #HMI_client.disconnect(hostname)

          else:
             Speed=3
             message=res
             HMI_client.connect(hostname, broker_port, 60)
             HMI_client.publish(topic1, message)
             #HMI_client.connect(hostname, broker_port, 60)
             #HMI_client.publish(topic1, message)
             #HMI_client.disconnect(hostname)


    return render_template('index.html',Speed = Speed,Mode=Mode)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5001)

