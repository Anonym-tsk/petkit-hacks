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
