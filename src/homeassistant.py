import os
import logging
import time
import json
import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", None)
BROKER_PORT = os.getenv("MQTT_PORT", 1883)
BROKER_USER = os.getenv("MQTT_USER", None)
BROKER_PASS = os.getenv("MQTT_PASS", None)
CLIENT_ID = "petkit"

MESSAGE_ONLINE = "online"
MESSAGE_OFFLINE = "offline"


class HomeAssistant:
    def __init__(self):
        self.__device_name = None
        self.__firmware = 0
        self.__last_event_type = 0
        # {"litter":{"weight":9555,"usedTimes":1,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9585,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:75644,runt:65233,res:6,ow:7134078,cw:7132092,zw:7764741,Ls:66,Hs:66,cur:188_657_0,DC:12390,pet:1,PX:200-42,PXS:2147483647-1,ws:0,wcnt:2,md:510,k3c:0,IOT:3_-2319,dtp:12"}
        self.__last_state = {}
        # зависит от типа события, например такое
        # {"time_in":1749706114,"time_out":1749706228,"auto_clear":1,"is_shit":1,"interval":2,"pet_weight":4444,"shit_weight":0}
        self.__last_event_data = {}
        self.__mqttc = None

    def __publish_sensors_config(self):
        if self.__mqttc is not None:
            logging.debug("Publish info to MQTT")
            self.__mqttc.publish(f"homeassistant/sensor/{self.__device_name}/poop_count/config", payload=json.dumps({
                "name": "Poop count",
                "unique_id": f"{self.__device_name}_poop_count",
                "object_id": f"{self.__device_name}_poop_count",
                "icon": "mdi:emoticon-poop",
                "state_class": "total",
                "availability_topic": f"{self.__device_name}/available",
                "state_topic": f"{self.__device_name}/status/state",
                "value_template": "{{ value_json.poop_count }}",
                "device": {
                    "name": f"Petkit {self.__device_name}",
                    "manufacturer": "Petkit",
                    "model":"Pura Max",
                    "identifiers": [f"petkit_{self.__device_name}"],
                    "sw_version": self.__firmware
                }
             }), retain=True)

    def __publish_sensors_data(self):
        if self.__mqttc is not None:
            logging.debug("Publish sensors to MQTT")
            self.__mqttc.publish(f"{self.__device_name}/status/state", json.dumps({
                "poop_count": self.__last_state["litter"]["usedTimes"]
            }), retain=True)

    def __on_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT server")
        client.publish(f"{self.__device_name}/available", MESSAGE_ONLINE, retain=True)
        self.__publish_sensors_config()

    def __on_disconnect(self, client, userdata, rc):
        logging.debug(f"Disonnected with result code {rc}")

    def __start_mqtt(self):
        logging.debug("Creating new MQTT instance")
        self.__mqttc = mqtt.Client(client_id=CLIENT_ID, clean_session=False, protocol=mqtt.MQTTv311, transport="tcp")
        self.__mqttc.username_pw_set(BROKER_USER, BROKER_PASS)
        self.__mqttc.will_set(f"{self.__device_name}/available", payload=MESSAGE_OFFLINE, qos=0, retain=True)
        self.__mqttc.on_connect = self.__on_connect
        self.__mqttc.on_disconnect = self.__on_disconnect

        try:
            logging.debug("Connecting to broker")
            self.__mqttc.connect(BROKER_HOST, port=BROKER_PORT, keepalive=30)
        except:
            logging.warning("Connection failed. Reconnect after 3s")
            time.sleep(3)
            self.__start_mqtt()

        self.__mqttc.loop_start()

    def __start(self):
        if BROKER_HOST is not None:
            self.__start_mqtt()

    def disconnect(self):
        if self.__mqttc is not None:
            self.__mqttc.loop_stop()

    def set_device_name(self, device_name):
        self.__device_name = device_name
        self.__start()

    def set_firmware(self, firmware):
        self.__firmware = firmware

    def process_event(self, event_type, content, state = None):
        self.__last_event_type = event_type
        self.__last_event_data = content
        if state is not None:
            self.__last_state = state
            self.__publish_sensors_data()

    def process_state(self, state):
        self.__last_state = state
        self.__publish_sensors_data()
