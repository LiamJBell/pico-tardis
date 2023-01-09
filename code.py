import audiobusio
import board, os, pwmio, asyncio, digitalio
import wifi, socketpool
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.status import HTTPStatus
from adafruit_itertools import chain
from audiomp3 import MP3Decoder
import microcontroller

server = HTTPServer(socketpool.SocketPool(wifi.radio))
# IO setup
board_led = digitalio.DigitalInOut(board.LED)
board_led.direction = digitalio.Direction.OUTPUT
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
    with audiobusio.I2SOut(board.GP10, board.GP11, board.GP9) as audio:#BCLK_PIN, WS_PIN, SDIN_PIN
        if audio.playing:
            return False
        else:
            decoder.file = open(sound, "rb")
            audio.play(decoder)
            while audio.playing:
                if playLight:
                    asyncio.run(light())
            return True

async def light():
    """
    PWM pulse LED for duration of audio file currently playing
    """
    global first_run
    max = 255
    min = 0
    if first_run:
        await asyncio.sleep(3)  
        for i in range(min, max, 1):
            lamp.duty_cycle=i*i
            await asyncio.sleep(0.003)
        first_run = False
    for i in chain(range(max, min, -1), range(min, max, 1)):
        lamp.duty_cycle = i*i
        await asyncio.sleep(0.003)

@server.route("/command")
def handleTardisCommand(request):
    """
    Ingests a parameter from the HTTP request, asks for the file path to the relevant sound and tells the 
    TARDIS to run the sound
    :param request: the HTTPRequest coming from the client. This should contain a paramater called `sound` and `light` containing
    a command for the TARDIS to execute
    """
    sound = request.query_params.get("sound")
    light = request.query_params.get("light")
    response = HTTPResponse(request)
    if light is not bool:
        light = False
    sound = selectSound(sound)
    if sound is not None:
        body = "OK"
        response.status=HTTPStatus(200, "Playing {}. Light flashing: {}".format(sound, light))
        response.send(body)
        playSound(sound, light)
        if light:
            pass
        # The below If statement is currently pointless because CircuitPython cannot properly work asynchronously on a Pico, so the check is irrelevant
        # if not playSound(sound):
        #     body = "Sound already playing, please wait"
        #     response.status=HTTPStatus(503, "Busy")
    else:
        body = "Invalid parameter"
        response.status=HTTPStatus(400, "Bad Request")
        response.send(body)

async def connectToWiFi():  
    wifi.radio.hostname="TARDIS"
    wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
    print("Connected to WiFi %s on IP:" % os.getenv("CIRCUITPY_WIFI_SSID"), wifi.radio.ipv4_address)

async def startHTTPServer():
    try:
        server.start(str(wifi.radio.ipv4_address))
        board_led.value = True
        print("listening on:%s" % wifi.radio.ipv4_address)
    except OSError as e:
        print("Error starting server, restarting...\n{}".format(e))
        asyncio.sleep(5)
        microcontroller.reset()
    
async def loop():
    global first_run
    first_run=True
    if first_run:
        pass
        # playSound(selectSound("startup"))
    while True:
        server.poll()

async def main():
    global decoder
    wifi = asyncio.create_task(connectToWiFi())
    startServer = asyncio.create_task(startHTTPServer())
    asyncio.gather(wifi, startServer)
    decoder = MP3Decoder(open("/sounds/startup.mp3", "rb")) #Opening a MP3Decoder takes up a lot of memory, so we do it here to save the precious KBs during runtime

    asyncio.run(loop()) #Run server.poll() on a permanent loop until we crash, switch off or are interrupted

if __name__ == "__main__":
    asyncio.run(main())





