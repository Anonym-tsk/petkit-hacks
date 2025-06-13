from homeassistant import HomeAssistant


class PetkitDevice:
    def __init__(self, device_id):
        self.__device_id = device_id
        self.__type = None
        self.__firmware = 0
        self.__event_type = 0
        self.__clean_type = 0
        self.__pet_weight = 0
        self.__used_times = 0
        self.__error = None
        # {"litter":{"weight":9555,"usedTimes":1,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9585,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:75644,runt:65233,res:6,ow:7134078,cw:7132092,zw:7764741,Ls:66,Hs:66,cur:188_657_0,DC:12390,pet:1,PX:200-42,PXS:2147483647-1,ws:0,wcnt:2,md:510,k3c:0,IOT:3_-2319,dtp:12"}
        self.__state = {}
        # зависит от типа события, например такое
        # {"time_in":1749706114,"time_out":1749706228,"auto_clear":1,"is_shit":1,"interval":2,"pet_weight":4444,"shit_weight":0}
        self.__event_data = {}

    def set_type(self, event_type: str):
        self.__type = event_type

    def set_firmware(self, firmware: str):
        self.__firmware = firmware

    def set_state(self, state: {}):
        self.__state = state
        self.__used_times = state['litter']['usedTimes'] + 1

    def set_event(self, event_type: int, event_data: {}):
        # eventType=9 - изменение веса
        # eventType=9&event_id=400179435_1749749633&timestamp=1749749633&content={"pet_weight":3499}&state={"litter":{"weight":9607,"usedTimes":3,"percent":96,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":1749749633,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":13473,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":57},"boxState":1,"other":"heap:78028,runt:372,res:1,ow:7130667,cw:6868595,zw:7764741,Ls:66,Hs:66,cur:226_398_0,DC:12390,pet:1,PX:200-40,PXS:2147483647-173,ws:0,wcnt:4,md:1233,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=10 - кот посрал
        # eventType=10&event_id=400179435_1749749633&timestamp=1749749651&content={"time_in":1749749634,"time_out":1749749651,"auto_clear":1,"is_shit":1,"interval":2,"pet_weight":3816,"shit_weight":0}&state={"litter":{"weight":9607,"usedTimes":4,"percent":95,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9612,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":54},"boxState":1,"other":"heap:75860,runt:390,res:1,ow:7130667,cw:7130317,zw:7764741,Ls:66,Hs:66,cur:226_398_0,DC:12390,pet:1,PX:200-40,PXS:2147483647-2,ws:0,wcnt:5,md:1234,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=3 - запущена очистка
        # авто -    eventType=3&event_id=400179435_1749747587&timestamp=1749747587&content={"reason":0,"pos":-30001,"action":0}&state={"litter":{"weight":9602,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"work_state":{"work_mode":0,"work_reason":0,"work_process":13,"stop_time":600,"safe_warn":-1},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9602,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":0,"close_hall":1,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":41},"boxState":1,"other":"heap:83104,runt:106592,res:6,ow:7130967,cw:7130960,zw:7764741,Ls:66,Hs:66,cur:234_501_0,DC:12402,pet:1,PX:200-40,PXS:2147483647-0,ws:1,wcnt:3,md:1199,k3c:0,IOT:3_-2319,dtp:12"}
        # вручную - eventType=3&event_id=400179435_1749750210&timestamp=1749750210&content={"reason":3,"pos":-30001,"action":0}&state={"litter":{"weight":9608,"usedTimes":4,"percent":95,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"work_state":{"work_mode":0,"work_reason":3,"work_process":11,"stop_time":600,"safe_warn":-1},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9612,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":0,"close_hall":1,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":40},"boxState":1,"other":"heap:84952,runt:949,res:1,ow:7130576,cw:7130321,zw:7764741,Ls:66,Hs:66,cur:188_775_0,DC:12390,pet:1,PX:200-40,PXS:2147483647-0,ws:1,wcnt:5,md:1243,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=5 - завершена очистка
        # авто -    eventType=5&event_id=400179435_1749747587&timestamp=1749747693&content={"start_time":1749747587,"start_reason":0,"pos":-30001,"current":219,"result":0,"components":0,"litter_weight":9602,"litter_percent":0,"box":0,"clean_weight":2,"err":null}&state={"litter":{"weight":9602,"usedTimes":2,"percent":0,"sandType":0},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9599,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:103296,runt:106699,res:6,ow:7130967,cw:7131159,zw:7764741,Ls:66,Hs:66,cur:383_671_0,DC:12360,pet:1,PX:200-40,PXS:2147483647-0,ws:0,wcnt:3,md:1201,k3c:0,IOT:3_-2319,dtp:12"}
        # вручную - eventType=5&event_id=400179435_1749750210&timestamp=1749750314&content={"start_time":1749750210,"start_reason":3,"pos":-30001,"current":217,"result":0,"components":0,"litter_weight":9608,"litter_percent":95,"box":0,"clean_weight":240,"err":null}&state={"litter":{"weight":9608,"usedTimes":4,"percent":95,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9610,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":0,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:105144,runt:1054,res:1,ow:7130576,cw:7130445,zw:7764741,Ls:66,Hs:66,cur:672_491_0,DC:12360,pet:1,PX:200-41,PXS:2147483647-1,ws:0,wcnt:5,md:1245,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=1 и eventType=2 - кажется какие-то ошибки
        # eventType=1&event_id=400179435_1749820624&timestamp=1749820624&content={"err":"hallB"}&state={"litter":{"weight":9574,"usedTimes":9,"percent":89,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":1,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9243,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":1,"top_hall":0,"box_hall":1,"prox_L":0,"prox_R":41},"boxState":0,"other":"heap:108312,runt:4725,res:1,ow:7132827,cw:7154665,zw:7764741,Ls:66,Hs:66,cur:0_0_0,DC:12390,pet:1,PX:200-42,PXS:2147483647-529,ws:0,wcnt:1,md:977,k3c:0,IOT:3_-2319,dtp:12"}
        # eventType=2&event_id=400179435_1749820624&timestamp=1749820630&content={"start_time":1749820624,"err":"hallB"}&state={"litter":{"weight":9574,"usedTimes":9,"percent":89,"sandType":1},"k3Id":0,"device":{"sw":1,"pet_in_time":0,"k3LightSwitch":0},"err":{"DC":0,"mcu":0,"scale":0,"falldown":0,"moto_M":0,"moto_D":0,"hallT":0,"hallB":0,"hallH":0,"hallD":0,"hallS":0,"hallO":0,"hallC":0,"PROX":0,"rtc":0,"atmz":0,"full":0,"scaleD":0,"OLED":0},"sensor":{"weight":9524,"stdby_hall":0,"dump_hall":1,"smooth_hall":1,"open_hall":1,"close_hall":1,"top_hall":0,"box_hall":0,"prox_L":0,"prox_R":42},"boxState":1,"other":"heap:108088,runt:4731,res:1,ow:7132827,cw:7136107,zw:7764741,Ls:66,Hs:66,cur:0_0_0,DC:12384,pet:1,PX:200-42,PXS:2147483647-29,ws:0,wcnt:1,md:977,k3c:0,IOT:3_-2319,dtp:12"}

        self.__event_type = event_type
        self.__event_data = event_data
        self.__error = event_data['err'] if 'err' in event_data else None

        if event_type == 3:
            self.__clean_type = int(event_data['reason'])
        elif event_type == 5:
            self.__clean_type = int(event_data['start_reason'])
        elif event_type in [9, 10]:
            self.__pet_weight = int(event_data['pet_weight']) / 1000

    @property
    def device_id(self):
        return self.__device_id

    @property
    def type(self):
        return self.__type

    @property
    def firmware(self):
        return self.__firmware

    @property
    def event_type(self):
        return self.__event_type

    @property
    def clean_type(self):
        return self.__clean_type

    @property
    def pet_weight(self):
        return self.__pet_weight

    @property
    def used_times(self):
        return self.__used_times

    @property
    def error(self):
        return self.__error


class PetkitDeviceManager:
    def __init__(self):
        self.__devices: {str: PetkitDevice} = {}
        self.__ha = HomeAssistant()

    def __get_device(self, device_id: str) -> PetkitDevice:
        if device_id not in self.__devices:
            device = PetkitDevice(device_id)
            self.__devices[device_id] = device
            self.__ha.start()
        return self.__devices[device_id]

    def set_type(self, device_id: str, event_type: str):
        device = self.__get_device(device_id)
        device.set_type(event_type)

    def set_firmware(self, device_id: str, firmware: str):
        device = self.__get_device(device_id)
        device.set_firmware(firmware)

    def set_state(self, device_id: str, state: {}):
        device = self.__get_device(device_id)
        device.set_state(state)
        self.__ha.process_device_data(device)

    def set_event(self, device_id: str, event_type: int, event_data: {}, state=None):
        device = self.__get_device(device_id)
        device.set_event(event_type, event_data)
        if state is not None:
            self.set_state(device_id, state)
        else:
            self.__ha.process_device_data(device)

    def destroy(self):
        self.__devices = {}
        self.__ha.stop()
