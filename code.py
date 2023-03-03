import ipaddress
import time
import audiobusio
import board, os, pwmio, asyncio, digitalio
import wifi, socketpool, ssl
from adafruit_itertools import chain
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from audiomp3 import MP3Decoder
from secrets import secrets

# IO setup
board_led = digitalio.DigitalInOut(board.LED)
board_led.direction = digitalio.Direction.OUTPUT
board_led.value=True
lamp = pwmio.PWMOut(board.GP17)


#Fetch list of sounds to be played
sounds = os.listdir("sounds")

def selectSound(command):
    """Takes string command and checks if it is in `sounds`, returning the path to the `.mp3` file if True
    """
    sound = "{}.mp3".format(command)
    if sound not in sounds:
        return None
    return "sounds/{}".format(sound)

def playSound(sound, playLight=True):
    global decoder
    """Play the given sound and run the lamp 
    :param sound: the path to the audio file to be played
    """
    with audiobusio.I2SOut(board.GP10, board.GP11, board.GP9) as audio:#BCLK_PIN, LRC_PIN, SDIN_PIN
        if audio.playing:
            return False
        else:
            decoder.file = open(sound, "rb")
            audio.play(decoder)
            while audio.playing:
                if playLight:
                    light()
            return True

def light():
    """
    PWM pulse LED for duration of audio file currently playing
    """
    global first_run
    max = 255
    min = 0
    if first_run:
        time.sleep(3)  
        for i in range(min, max, 1):
            lamp.duty_cycle=i*i
            time.sleep(0.003)
        first_run=False
    for i in chain(range(max, min, -1), range(min, max, 1)):
        lamp.duty_cycle = i*i
        time.sleep(0.003)
    
def initMqtt():    
    global mqtt_client
    broker = ipaddress.IPv4Address(secrets["mqtt_broker_hostname"])
    while wifi.radio.ping(broker) is None:
        print("Broker unavailable")
        time.sleep(1)
    pool = socketpool.SocketPool(wifi.radio)
    mqtt_client = MQTT.MQTT(
        client_id=secrets["hostname"],
        username = secrets["mqtt_username"],
        password = secrets['mqtt_password'],
        broker=secrets["mqtt_broker_hostname"],
        socket_pool=pool,
        port=secrets["mqtt_broker_port"],
        socket_timeout=5,
        connect_retries=10
    )
    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect
    mqtt_client.on_subscribe = subscribe
    mqtt_client.on_unsubscribe = unsubscribe
    mqtt_client.on_publish = publish
    mqtt_client.on_message = message
    mqtt_client.connect()
    mqtt_client.subscribe("tardis")

def connectToWiFi():  
    wifi.radio.enabled = False
    wifi.radio.enabled = True
    wifi.radio.hostname="TARDIS"
    wifi.radio.connect(secrets["wifi_ssid"], secrets["wifi_pw"])

def loop():
    global mqtt_client
    global first_run
    
    first_run=True
    if first_run:
        playSound(selectSound("startup"))
        first_run = False
    while True:
        mqtt_client.loop()
        
def connect(mqtt_client, userdata, flags, rc):
    print("Connected to MQTT Broker\n Flags: {0}\nRC:{1}".format(flags, rc))

def disconnect(mqtt_client, userdata, rc):
    print("Disconnected from MQTT Broker")

def subscribe(mqtt_client, userdata, topic, granted_qos):
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))
    
def unsubscribe(mqtt_client, userdata, topic, pid):
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))
    
def publish(mqtt_client, userdata, topic, pid):
    print("Published to {0} with PID {1}".format(topic, pid))
    
def message(client, topic, message):
    print("New message on topic {0}: {1}".format(topic, message))
    light = True
    sound = selectSound(message)
    if sound is None:
        return  #Throw some sort of error at the publisher?
    elif sound == "cloister.mp3":
        light = False
    playSound(selectSound(message))

def main():
    global decoder
    connectToWiFi()
    initMqtt()
    decoder = MP3Decoder(open("/sounds/startup.mp3", "rb")) #Opening a MP3Decoder takes up a lot of memory, so we do it here to save the precious KBs during runtime
    
    loop()

if __name__ == "__main__":
    main()





