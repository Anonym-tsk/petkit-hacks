# petkit-hacks

Итак, вы купили умный кошачий лоток Petkit Pura Max (или Pura Max 2), он же P9902,
а он оказался китайский и не подключается к приложению с ошибкой 711.

Не спешите сливать его на Авито. К приложению он, конечно, не подключится.
Но включить автоматическую очистку и добавить его в Home Assistant можно.

### Суть решения

Лоток получает настройки из API.
Мы подменим DNS запись китайского API и поднимем свою прокси.

### Прокси

Минимальный docker-compose.yaml

```yaml
version: '3.8'

services:
  petkit-hacks:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: petkit-hacks
    dns:
      - 8.8.8.8
    ports:
      - "80:8080"
    environment:
      SERVER_IP: 192.168.1.101
      SERVER_PORT: 80
    restart: unless-stopped

```

Другие параметры:

| Параметр       | Значение по-умолчанию | Описание                                                                                                        |
|----------------|-----------------------|-----------------------------------------------------------------------------------------------------------------|
| SERVER_IP      |                       | Внешний IP адрес вашего сервера                                                                                 |
| SERVER_PORT    | 80                    | Порт на котором работает прокси                                                                                 |
| TARGET_SN      |                       | Серийный номер вашего устройства, если не задан, прокси будет работать с любым устройством                      |
| PETKIT_HOST    | api.eu-pet.com        | API-хост на который ходит лоток, по-умолчанию для региона Россия                                                |
| LOG_LEVEL      | info                  | Log level: debug, info, warning                                                                                 |
| CONF_AUTOWORK  | 1                     | Включить автоматическую очистку                                                                                 |
| CONF_UNIT      | 0                     | Единицы измерения, отображаемые лотком (1 - lbs, 0 - kg)                                                        |
| CONF_SAND_TYPE | 1                     | Тип наполнителя. Достоверно неизвестно за что отвечает, но значение 1 убирает ошибку "недостаточно наполнителя" |
| MQTT_HOST      |                       | MQTT сервер, включает Home Assistant MQTT Discovery                                                             |
| MQTT_PORT      | 1883                  | MQTT порт                                                                                                       |
| MQTT_USER      |                       | MQTT логин                                                                                                      |
| MQTT_PASS      |                       | MQTT пароль                                                                                                     |

### Подмена DNS

На роутере Keenetic можно сделать без установки дополнительных пакетов в CLI:

```
ip host api.eu-pet.com 192.168.1.101
system configuration save
```

Теперь устройства в локальной сети при запросах на домен `api.eu-pet.com` будут попадать на адрес `192.168.1.101`

### Запуск

1. Поднимите прокси, подмените DNS
2. Переведите лоток в режим сопряжения через меню
3. В приложении Petkit выберите регион Россия и начните добавление лотка
4. После получения ошибки 711 закройте приложение, оно больше не понадобится
5. Через несколько минут лоток получит настройки, а вы увидите устройство и сенсоры в Home Assistant
6. Опционально - можно запретить лотку выход в интернет и оставить только локальную сеть

### Полезная информация

- [Как я воевал с китайским умным туалетом для котов](https://habr.com/ru/articles/908086/)
- [earlynerd/petkit-pura-max-serial-bus](https://github.com/earlynerd/petkit-pura-max-serial-bus)
- [Switch MQTT Broker](https://github.com/earlynerd/petkit-pura-max-serial-bus/issues/1)
- [dwyschka/localkit](https://github.com/dwyschka/localkit)
  и [dwyschka/localkit-broker](https://github.com/dwyschka/localkit-broker)

---

Нравится проект? Поддержи автора [здесь](https://yoomoney.ru/to/410019180291197) или [тут](https://pay.cloudtips.ru/p/054d0666). Купи ему немного :beers: или :coffee:!
