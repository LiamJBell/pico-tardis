import time
import audiobusio
import board
import pwmio
import wifi, socketpool, ampule
from adafruit_itertools import chain
from audiomp3 import MP3Decoder
import asyncio

audio = audiobusio.I2SOut(board.GP10, board.GP11, board.GP9)
pwm = pwmio.PWMOut(board.GP17)


@ampule.route("/")
def handleTardisCommand(request, command):
    print("received request")
    playSound()

async def selectSound():
    # do sound selection stuff
    return


async def playSound():
    if audio.playing:
        return False
    else:
        mp3 = open("sounds/defaultFlightLaunch.mp3", "rb")
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

async def startAmpule():
    print("Starting Ampule...")
    pool = socketpool.SocketPool(wifi.radio)
    socket = pool.socket()
    socket.bind(['0.0.0.0', 80])
    print("Bound socket")
    socket.listen(10)
    print("Socket listening")

    while True:
        ampule.listen(socket)


async def connectToWiFi():    
    try:
        from secrets import secrets
    except ImportError:
        print("WiFi secrets are kept in secrets.py")
        raise
    wifi.radio.hostname="TARDIS"
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("Connected to WiFi %s on IP:" % secrets["ssid"], wifi.radio.ipv4_address)


async def main():
    wifi = asyncio.create_task(connectToWiFi())
    server = asyncio.create_task(startAmpule())
    
    await asyncio.gather(wifi, server)



if __name__ == "__main__":
    asyncio.run(main())
