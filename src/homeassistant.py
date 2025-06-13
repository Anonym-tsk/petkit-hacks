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
        self.__last_clean_type = 0
        self.__last_pet_weight = 0
        # {"litter":{"weight":9555,"usedTimes":1,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9585,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:75644,runt:65233,res:6,ow:7134078,cw:7132092,zw:7764741,Ls:66,Hs:66,cur:188_657_0,DC:12390,pet:1,PX:200-42,PXS:2147483647-1,ws:0,wcnt:2,md:510,k3c:0,IOT:3_-2319,dtp:12"}
        self.__last_state = {}
        # зависит от типа события, например такое
        # {"time_in":1749706114,"time_out":1749706228,"auto_clear":1,"is_shit":1,"interval":2,"pet_weight":4444,"shit_weight":0}
        self.__last_event_data = {}
        self.__mqttc = None

    def __availability_topic(self):
        return f"{self.__device_name}/available"

    def __state_topic(self):
        return f"{self.__device_name}/status/state"

    def __device_data(self):
        return {
            "device": {
                "name": f"Petkit {self.__device_name}",
                "manufacturer": "Petkit",
                "model": "Pura Max",
                "identifiers": [f"petkit_{self.__device_name}"],
                "sw_version": self.__firmware
            }
        }

    def __event_type_string(self, event_type):
        # eventType=9 - изменение веса
        # eventType=9&event_id=400079435_1749749633&timestamp=1749749633&content={"pet_weight":3499}&state={"litter":{"weight":9607,"usedTimes":3,"percent":96,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":1749749633,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":13473,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":57},"boxState":1,"other":"heap:78028,runt:372,res:1,ow:7130667,cw:6868595,zw:7764741,Ls:66,Hs:66,cur:226_398_0,DC:12390,pet:1,PX:200-40,PXS:2147483647-173,ws:0,wcnt:4,md:1233,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=10 - кот посрал
        # eventType=10&event_id=400079435_1749749633&timestamp=1749749651&content={"time_in":1749749634,"time_out":1749749651,"auto_clear":1,"is_shit":1,"interval":2,"pet_weight":3816,"shit_weight":0}&state={"litter":{"weight":9607,"usedTimes":4,"percent":95,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9612,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":54},"boxState":1,"other":"heap:75860,runt:390,res:1,ow:7130667,cw:7130317,zw:7764741,Ls:66,Hs:66,cur:226_398_0,DC:12390,pet:1,PX:200-40,PXS:2147483647-2,ws:0,wcnt:5,md:1234,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=3 - запущена очистка
        # авто -    eventType=3&event_id=400079435_1749747587&timestamp=1749747587&content={"reason":0,"pos":-30001,"action":0}&state={"litter":{"weight":9602,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"work_state":{"work_mode":0,"work_reason":0,"work_process":13,"stop_time":600,"safe_warn":-1},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9602,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":0,"close_hall":1,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":41},"boxState":1,"other":"heap:83104,runt:106592,res:6,ow:7130967,cw:7130960,zw:7764741,Ls:66,Hs:66,cur:234_501_0,DC:12402,pet:1,PX:200-40,PXS:2147483647-0,ws:1,wcnt:3,md:1199,k3c:0,IOT:3_-2319,dtp:12"}
        # вручную - eventType=3&event_id=400079435_1749750210&timestamp=1749750210&content={"reason":3,"pos":-30001,"action":0}&state={"litter":{"weight":9608,"usedTimes":4,"percent":95,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"work_state":{"work_mode":0,"work_reason":3,"work_process":11,"stop_time":600,"safe_warn":-1},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9612,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":0,"close_hall":1,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":40},"boxState":1,"other":"heap:84952,runt:949,res:1,ow:7130576,cw:7130321,zw:7764741,Ls:66,Hs:66,cur:188_775_0,DC:12390,pet:1,PX:200-40,PXS:2147483647-0,ws:1,wcnt:5,md:1243,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=5 - завершена очистка
        # авто -    eventType=5&event_id=400079435_1749747587&timestamp=1749747693&content={"start_time":1749747587,"start_reason":0,"pos":-30001,"current":219,"result":0,"components":0,"litter_weight":9602,"litter_percent":0,"box":0,"clean_weight":2,"err":null}&state={"litter":{"weight":9602,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9599,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:103296,runt:106699,res:6,ow:7130967,cw:7131159,zw:7764741,Ls:66,Hs:66,cur:383_671_0,DC:12360,pet:1,PX:200-40,PXS:2147483647-0,ws:0,wcnt:3,md:1201,k3c:0,IOT:3_-2319,dtp:12"}
        # вручную - eventType=5&event_id=400079435_1749750210&timestamp=1749750314&content={"start_time":1749750210,"start_reason":3,"pos":-30001,"current":217,"result":0,"components":0,"litter_weight":9608,"litter_percent":95,"box":0,"clean_weight":240,"err":null}&state={"litter":{"weight":9608,"usedTimes":4,"percent":95,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9610,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:105144,runt:1054,res:1,ow:7130576,cw:7130445,zw:7764741,Ls:66,Hs:66,cur:672_491_0,DC:12360,pet:1,PX:200-41,PXS:2147483647-1,ws:0,wcnt:5,md:1245,k3c:0,IOT:3_-2319,dtp:12"}

        if event_type == 9:
            return 'Weighing'
        if event_type == 10:
            return 'Visit'
        if event_type == 3:
            return 'Cleaning'
        return 'Ready'

    def __clean_type_string(self, clean_type):
        if clean_type == 3:
            return 'Manually'
        return 'Automatically'

    def __publish_sensors_config(self):
        if self.__mqttc is not None:
            logging.debug("Publish info to MQTT")

            self.__mqttc.publish(f"homeassistant/sensor/{self.__device_name}/poop_count/config", payload=json.dumps({
                "name": "Poop count",
                "unique_id": f"{self.__device_name}_poop_count",
                "object_id": f"{self.__device_name}_poop_count",
                "icon": "mdi:emoticon-poop",
                "state_class": "total",
                "availability_topic": self.__availability_topic(),
                "state_topic": self.__state_topic(),
                "value_template": "{{ value_json.poop_count }}"
            } | self.__device_data()), retain=True)

            self.__mqttc.publish(f"homeassistant/sensor/{self.__device_name}/event_type/config", payload=json.dumps({
                "name": "Status",
                "unique_id": f"{self.__device_name}_event_type",
                "object_id": f"{self.__device_name}_event_type",
                "icon": "mdi:check-circle-outline",
                "availability_topic": self.__availability_topic(),
                "state_topic": self.__state_topic(),
                "value_template": "{{ value_json.event_type }}"
            } | self.__device_data()), retain=True)

            self.__mqttc.publish(f"homeassistant/sensor/{self.__device_name}/clean_type/config", payload=json.dumps({
                "name": "Last cleaning",
                "unique_id": f"{self.__device_name}_clean_type",
                "object_id": f"{self.__device_name}_clean_type",
                "icon": "mdi:broom",
                "availability_topic": self.__availability_topic(),
                "state_topic": self.__state_topic(),
                "value_template": "{{ value_json.clean_type }}"
            } | self.__device_data()), retain=True)

            self.__mqttc.publish(f"homeassistant/sensor/{self.__device_name}/pet_weight/config", payload=json.dumps({
                "name": "Pet weight",
                "unique_id": f"{self.__device_name}_pet_weight",
                "object_id": f"{self.__device_name}_pet_weight",
                "icon": "mdi:cat",
                "state_class": "measurement",
                "device_class": "weight",
                "unit_of_measurement": "kg",
                "availability_topic": self.__availability_topic(),
                "state_topic": self.__state_topic(),
                "value_template": "{{ value_json.pet_weight }}",
            } | self.__device_data()), retain=True)

    def __publish_sensors_data(self):
        if self.__mqttc is not None:
            logging.debug("Publish sensors to MQTT")
            self.__mqttc.publish(self.__state_topic(), json.dumps({
                "poop_count": self.__last_state["litter"]["usedTimes"] + 1,
                "event_type": self.__event_type_string(self.__last_event_type),
                "clean_type": self.__clean_type_string(self.__last_clean_type),
                "pet_weight": self.__last_pet_weight / 1000
            }), retain=True)

    def __on_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT server")
        client.publish(self.__availability_topic(), MESSAGE_ONLINE, retain=True)
        self.__publish_sensors_config()

    def __on_disconnect(self, client, userdata, rc):
        logging.debug(f"Disonnected with result code {rc}")

    def __start_mqtt(self):
        logging.debug("Creating new MQTT instance")
        self.__mqttc = mqtt.Client(client_id=CLIENT_ID, clean_session=False, protocol=mqtt.MQTTv311, transport="tcp")
        self.__mqttc.username_pw_set(BROKER_USER, BROKER_PASS)
        self.__mqttc.will_set(self.__availability_topic(), payload=MESSAGE_OFFLINE, qos=0, retain=True)
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
        if self.__mqttc is None:
            self.__start()

    def set_firmware(self, firmware):
        self.__firmware = firmware

    def process_event(self, event_type, content, state = None):
        self.__last_event_type = int(event_type)
        self.__last_event_data = content

        if self.__last_event_type == 3:
            self.__last_clean_type = int(content["reason"])
        elif self.__last_event_type == 5:
            self.__last_clean_type = int(content["start_reason"])
        elif self.__last_event_type in [9, 10]:
            self.__last_pet_weight = int(content["pet_weight"])

        if state is not None:
            self.__last_state = state
            self.__publish_sensors_data()

    def process_state(self, state):
        self.__last_state = state
        self.__publish_sensors_data()
