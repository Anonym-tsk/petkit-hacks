import os
import json
import logging
import requests
import urllib.parse
from flask import Flask, request, Response
import urllib3

from homeassistant import HomeAssistant

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PETKIT_HOST = os.getenv('PETKIT_HOST', 'api.eu-pet.com')
SERVER_IP = os.getenv('SERVER_IP', '127.0.0.1')
SERVER_PORT = os.getenv('SERVER_PORT', '80')
TARGET_SN = os.getenv('TARGET_SN', None)
LOG_LEVEL = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)

CONF_AUTOWORK = os.getenv('CONF_AUTOWORK', 1)
CONF_UNIT = os.getenv('CONF_UNIT', 0)
CONF_SAND_TYPE = os.getenv('CONF_SAND_TYPE', 1)

API_IP_URL = f"http://{SERVER_IP}:{SERVER_PORT}/6/"
TARGET_URL = f"http://{PETKIT_HOST}"
API_URL = f"{TARGET_URL}/6/"
PROXY_PORT = 8080

# http_client.HTTPConnection.debuglevel = 1 if LOG_LEVEL <= logging.DEBUG else 0
logging.basicConfig(level=LOG_LEVEL)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
ha = HomeAssistant()

device_info_paths = {'/6/t4/dev_device_info', '/6/t3/dev_device_info'}
iot_device_info_paths = {'/6/t4/dev_iot_device_info', '/6/t3/dev_iot_device_info'}
signup_paths = {'/6/t4/dev_signup', '/6/t3/dev_signup'}
heartbeat_paths = {'/6/poll/t4/heartbeat', '/6/poll/t3/heartbeat'}
serverinfo_paths = {'/6/t4/dev_serverinfo', '/6/t3/dev_serverinfo'}
state_report_paths = {'/6/t4/dev_state_report', '/6/t3/dev_state_report'}
event_report_paths = {'/6/t4/dev_event_report', '/6/t3/dev_event_report'}


def skip_logging(path):
    return path in heartbeat_paths


@app.before_request
def cache_body():
    request._request_body = request.get_data(cache=True)


@app.before_request
def log_request():
    if skip_logging(request.path):
        return

    logging.info(f">>> Request: {request.method} {request.url}")
    for k, v in request.headers.items():
        logging.debug(f">>> Header: {k}: {v}")

    data = getattr(request, '_request_body', b'')
    if data:
        logging.debug(f">>> Body: {data.decode('utf-8')}")


@app.after_request
def log_response(response):
    if skip_logging(request.path):
        return response

    logging.info(f"<<< Response: {response.status}")
    for k, v in response.headers.items():
        logging.debug(f"<<< Header: {k}: {v}")
    if response.data:
        logging.debug(f"<<< Body: {response.data.decode('utf-8')}")
    return response


def modify_device_info(resp_json):
    if 'result' in resp_json and isinstance(resp_json['result'], dict):
        result = resp_json['result']
        settings = result.get('settings', {})

        if ((TARGET_SN is None or TARGET_SN == result.get('sn'))
                and isinstance(settings, dict)):
            if 'autoWork' in settings:
                logging.info(f"Modifying autowork from {settings['autoWork']} to {CONF_AUTOWORK}")
                settings['autoWork'] = CONF_AUTOWORK
            if 'unit' in settings:
                logging.info(f"Modifying unit from {settings['unit']} to {CONF_UNIT}")
                settings['unit'] = CONF_UNIT
            if 'sandType' in settings:
                logging.info(f"Modifying sandType from {settings['sandType']} to {CONF_SAND_TYPE}")
                settings['sandType'] = CONF_SAND_TYPE

    return resp_json


def modify_serverinfo():
    logging.info(f"Modifying ipServers and apiServers")
    return {
        'result': {
            'ipServers': [API_IP_URL],
            'apiServers': [API_URL],
            'nextTick': 3600,
            'linked': 0
        }
    }


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    fullpath = f"/{path}"
    url = urllib.parse.urljoin(TARGET_URL, fullpath)
    try:
        headers = {key: value for key, value in request.headers}
        headers['User-Agent'] = 'PETKIT DEV'
        headers['Host'] = PETKIT_HOST

        if fullpath in signup_paths:
            parsed = request.form.to_dict()
            if 'firmware' in parsed:
                ha.set_firmware(parsed['firmware'])
        elif fullpath in event_report_paths:
            parsed = request.form.to_dict()
            if 'eventType' in parsed:
                # eventType=10 - кот посрал
                # eventType=10&event_id=400079435_1749747433&timestamp=1749747466&content={"time_in":1749747433,"time_out":1749747466,"auto_clear":1,"is_shit":1,"interval":2,"pet_weight":2090,"shit_weight":0}&state={"litter":{"weight":9598,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9602,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":41},"boxState":1,"other":"heap:76144,runt:106471,res:6,ow:7131246,cw:7130990,zw:7764741,Ls:66,Hs:66,cur:234_501_0,DC:12408,pet:1,PX:200-40,PXS:2147483647-887,ws:0,wcnt:3,md:1197,k3c:0,IOT:3_-2319,dtp:12"}
                # eventType=3 - запущена очистка
                # eventType=3&event_id=400079435_1749747587&timestamp=1749747587&content={"reason":0,"pos":-30001,"action":0}&state={"litter":{"weight":9602,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"work_state":{"work_mode":0,"work_reason":0,"work_process":13,"stop_time":600,"safe_warn":-1},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9602,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":0,"close_hall":1,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":41},"boxState":1,"other":"heap:83104,runt:106592,res:6,ow:7130967,cw:7130960,zw:7764741,Ls:66,Hs:66,cur:234_501_0,DC:12402,pet:1,PX:200-40,PXS:2147483647-0,ws:1,wcnt:3,md:1199,k3c:0,IOT:3_-2319,dtp:12"}
                # eventType=5 - завершена очистка (?)
                # eventType=5&event_id=400079435_1749747587&timestamp=1749747693&content={"start_time":1749747587,"start_reason":0,"pos":-30001,"current":219,"result":0,"components":0,"litter_weight":9602,"litter_percent":0,"box":0,"clean_weight":2,"err":null}&state={"litter":{"weight":9602,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9599,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:103296,runt:106699,res:6,ow:7130967,cw:7131159,zw:7764741,Ls:66,Hs:66,cur:383_671_0,DC:12360,pet:1,PX:200-40,PXS:2147483647-0,ws:0,wcnt:3,md:1201,k3c:0,IOT:3_-2319,dtp:12"}
                event_type = parsed['eventType']
                content = json.loads(parsed['content'])
                state = json.loads(parsed['state']) if 'state' in parsed else None
                ha.process_event(event_type, content, state)
        elif fullpath in state_report_paths:
            parsed = request.form.to_dict()
            state = json.loads(parsed['state'])
            ha.process_state(state)

        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=getattr(request, '_request_body', b''),
            cookies=request.cookies,
            allow_redirects=False,
            verify=False,
            timeout=10
        )

        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            json_body = response.json()
            if fullpath in iot_device_info_paths:
                if 'result' in json_body and 'deviceName' in json_body['result']:
                    ha.set_device_name(json_body['result']['deviceName'])
            elif fullpath in serverinfo_paths:
                json_body = modify_serverinfo()
            elif fullpath in device_info_paths:
                json_body = modify_device_info(json_body)

            response_body = json.dumps(json_body)
            return Response(response_body, status=response.status_code, content_type='application/json')
        else:
            return Response(response.content, status=response.status_code, headers=dict(response.headers))
    except Exception as e:
        logging.error(f"Proxy error: {e}")
        return Response(f"Proxy error: {str(e)}", status=502)


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=PROXY_PORT)
    except KeyboardInterrupt:
        ha.disconnect()
        pass
