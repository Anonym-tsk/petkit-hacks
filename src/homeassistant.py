import os
import logging
import time
import json
import paho.mqtt.client as mqtt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from petkit_device import PetkitDevice

BROKER_HOST = os.getenv("MQTT_HOST", None)
BROKER_PORT = os.getenv("MQTT_PORT", 1883)
BROKER_USER = os.getenv("MQTT_USER", None)
BROKER_PASS = os.getenv("MQTT_PASS", None)
CLIENT_ID = "petkit"

TOPIC_AVAILABLE = "petkit/available"
MESSAGE_ONLINE = "online"
MESSAGE_OFFLINE = "offline"


def event_type_string(event_type):
    if event_type == 9:
        return 'Weighing'
    if event_type == 10:
        return 'Visit'
    if event_type == 3:
        return 'Cleaning'
    return 'Ready'


def clean_type_string(clean_type):
    if clean_type == 3:
        return 'Manually'
    return 'Automatically'


def state_topic(device_id: str):
    return f"petkit/{device_id}/status/state"


def mqtt_device_data(device: "PetkitDevice", sensor_id: str):
    return {
        "availability_topic": TOPIC_AVAILABLE,
        "unique_id": f"{device.device_id}_{sensor_id}",
        "object_id": f"{device.device_id}_{sensor_id}",
        "state_topic": state_topic(device.device_id),
        "value_template": "{{ value_json." + sensor_id + " }}",
        "device": {
            "name": f"Petkit {device.type}",
            "manufacturer": "Petkit",
            "model": "Pura Max",
            "identifiers": [f"petkit_{device.device_id}"],
            "sw_version": device.firmware
        }
    }


class HomeAssistant:
    def __init__(self):
        self.__mqttc = None

    def __publish_sensors_config(self, device: "PetkitDevice"):
        if self.__mqttc is not None:
            logging.debug("Publish info to MQTT")

            self.__mqttc.publish(f"homeassistant/sensor/{device.device_id}/poop_count/config", payload=json.dumps({
                "name": "Poop count",
                "icon": "mdi:emoticon-poop",
                "state_class": "total"
            } | mqtt_device_data(device, 'poop_count')), retain=True)

            self.__mqttc.publish(f"homeassistant/sensor/{device.device_id}/event_type/config", payload=json.dumps({
                "name": "Status",
                "icon": "mdi:check-circle-outline"
            } | mqtt_device_data(device, 'event_type')), retain=True)

            self.__mqttc.publish(f"homeassistant/sensor/{device.device_id}/clean_type/config", payload=json.dumps({
                "name": "Last cleaning",
                "icon": "mdi:broom"
            } | mqtt_device_data(device, 'clean_type')), retain=True)

            self.__mqttc.publish(f"homeassistant/sensor/{device.device_id}/pet_weight/config", payload=json.dumps({
                "name": "Pet weight",
                "icon": "mdi:cat",
                "state_class": "measurement",
                "device_class": "weight",
                "unit_of_measurement": "kg"
            } | mqtt_device_data(device, 'pet_weight')), retain=True)

    def __publish_sensors_data(self, device: "PetkitDevice"):
        if self.__mqttc is not None:
            logging.debug("Publish sensors to MQTT")

            self.__mqttc.publish(state_topic(device.device_id), json.dumps({
                "poop_count": device.used_times,
                "event_type": event_type_string(device.event_type),
                "clean_type": clean_type_string(device.clean_type),
                "pet_weight": device.pet_weight
            }), retain=True)

    @staticmethod
    def __on_connect(client, userdata, flags, rc):
        logging.info("Connected to MQTT server")
        client.publish(TOPIC_AVAILABLE, MESSAGE_ONLINE, retain=True)

    @staticmethod
    def __on_disconnect(client, userdata, rc):
        logging.debug(f"Disonnected with result code {rc}")

    def __start_mqtt(self):
        logging.debug("Creating new MQTT instance")
        self.__mqttc = mqtt.Client(client_id=CLIENT_ID, clean_session=False, protocol=mqtt.MQTTv311, transport="tcp")
        self.__mqttc.username_pw_set(BROKER_USER, BROKER_PASS)
        self.__mqttc.will_set(TOPIC_AVAILABLE, payload=MESSAGE_OFFLINE, qos=0, retain=True)
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

    def start(self):
        if BROKER_HOST is not None and self.__mqttc is None:
            self.__start_mqtt()

    def stop(self):
        if self.__mqttc is not None:
            self.__mqttc.loop_stop()

    def process_device_data(self, device: "PetkitDevice"):
        self.__publish_sensors_config(device)
        self.__publish_sensors_data(device)
