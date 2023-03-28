import adafruit_minimqtt.adafruit_minimqtt as MQTT
import wifi, socketpool


class mqttHandler:
    
    def __init__(self, secrets) -> None:
        self.secrets = secrets
        
    async def checkWifiConnection(self) -> bool:
        """ Checks if the WiFi connection is alive by pinging the gateway""" 
        return wifi.radio.ping("192.168.0.1") != None   
    
    async def connectToWiFi(self) -> bool:
        """ Connects to wifi with hostname, ssid and password from secrets"""
        wifi.radio.enabled = True
        wifi.radio.hostname=self.secrets["hostname"]
        wifi.radio.connect(self.secrets["wifi_ssid"], self.secrets["wifi_pw"])
        
        return self.checkWifiConnection()
    
    
    async def connectToMqttBroker(self) -> None:
        """ Connect to the MQTT Broker using the given parameters from the secrets"""
        self.mqtt_cient = MQTT.MQTT(
            client_id=self.secrets["hostname"],
            username = self.secrets["mqtt_username"],
            password = self.secrets['mqtt_password'],
            broker= self.secrets["mqtt_broker_hostname"],
            socket_pool= socketpool.SocketPool(wifi.radio),
            port= self.secrets["mqtt_broker_port"],
            socket_timeout=5,
            connect_retries=10
        )
        
