import audiobusio
import board, os, pwmio, asyncio
import wifi, socketpool
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.mime_type import MIMEType
from adafruit_itertools import chain
from audiomp3 import MP3Decoder
import microcontroller

audio = audiobusio.I2SOut(board.GP10, board.GP11, board.GP9)
pwm = pwmio.PWMOut(board.GP17)
pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)

async def selectSound(command):
    # do sound selection stuff
    if(command=="takeoff"):
        return "sounds/defaultFlightLaunch.mp3"
    return False

async def playSound(sound):
    if audio.playing:
        return False
    else:
        mp3 = open(sound, "rb")
        decoder = MP3Decoder(mp3)
        audio.play(decoder)
        asyncio.run(light())
        return True

# PWM light pulsing, only currently in the Police Box lamp. Future will also have breathing window lights
async def light():
    max = 255
    min = 0
    while audio.playing:
        for i in chain(range(min, max, 1), range(max, min, -1)):
            pwm.duty_cycle = i*i
            await asyncio.sleep(0.004)

@server.route("/command")
def handleTardisCommand(request):
    command = request.query_params.get("a")
    response = HTTPResponse(request, content_type=MIMEType.TYPE_TXT)
    sound = asyncio.run(selectSound(command))
    if sound:
        response.send("OK")
        asyncio.run(playSound(sound))
    else:
        response.send("Invalid parameter")



async def connectToWiFi():  
    # lock = asyncio.Lock()
    # with await lock.acquire():
        wifi.radio.hostname="TARDIS"
        wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
        print("Connected to WiFi %s on IP:" % os.getenv("CIRCUITPY_WIFI_SSID"), wifi.radio.ipv4_address)
    # lock.release()


async def startHTTPServer():
    global server    
    try:
        server.start(str(wifi.radio.ipv4_address))
        print("listening on:%s" % wifi.radio.ipv4_address)
        return True
    except OSError:
        asyncio.sleep(5)
        print("restarting. . .")
        microcontroller.reset()
    
async def loop():
    while True:
        server.poll()

async def main():
    global server
    wifi = asyncio.create_task(connectToWiFi())
    startServer = asyncio.create_task(startHTTPServer())
    asyncio.gather(wifi, startServer)

    asyncio.run(loop())


if __name__ == "__main__":
    asyncio.run(main())





