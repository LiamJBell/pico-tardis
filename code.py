import audiobusio
import board, os, pwmio, asyncio, digitalio
import wifi, socketpool
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.status import HTTPStatus
from adafruit_itertools import chain
from audiomp3 import MP3Decoder
import microcontroller

audio = audiobusio.I2SOut(board.GP10, board.GP11, board.GP9)
server = HTTPServer(socketpool.SocketPool(wifi.radio))
board_led = digitalio.DigitalInOut(board.LED)
board_led.direction = digitalio.Direction.OUTPUT

TARDIS_COMMANDS = ["demat", "mat", "flight", "cloister", "quickdemat", "quickmat", ]

async def selectSound(command):
    """Takes string command and checks if it is in `TARDIS_COMMANDS`, returning the path to the `.mp3` file if True
    """
    if command not in TARDIS_COMMANDS:
        return False
    return "sounds/%s.mp3" % command

async def playSound(sound):
    """Play the given sound and run the lamp 
    :param sound: the path to the audio file to be played
    """
    if audio.playing:
        return False
    else:
        audio.play(MP3Decoder(sound))
        asyncio.run(light())
        return True

async def light():
    """
    PWM pulse LED for duration of audio file currently playing
    """
    max = 255
    min = 0
    with pwmio.PWMOut(board.GP17) as pwm:
        while audio.playing:
            for i in chain(range(min, max, 1), range(max, min, -1)):
                pwm.duty_cycle = i*i
                await asyncio.sleep(0.004)

@server.route("/command")
def handleTardisCommand(request):
    """
    Ingests a parameter from the HTTP request, asks for the file path to the relevant sound and tells the 
    TARDIS to run the sound
    :param request: the HTTPRequest coming from the client. This should contain a paramater called `a` containing
    a command for the TARDIS to execute
    """
    command = request.query_params.get("a")
    response = HTTPResponse(request)
    sound = asyncio.run(selectSound(command))
    if sound:
        body = "OK"
        response.status=HTTPStatus(200, "OK")
        if not asyncio.run(playSound(sound)):
            body = "Sound already playing, please wait"
            response.status=HTTPStatus(503, "Busy")
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
    while True:
        server.poll()

async def main():
    wifi = asyncio.create_task(connectToWiFi())
    startServer = asyncio.create_task(startHTTPServer())
    asyncio.gather(wifi, startServer)

    asyncio.run(loop())

if __name__ == "__main__":
    asyncio.run(main())





