import audiobusio
import board, os, pwmio, asyncio
import wifi, socketpool
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.response import HTTPResponse
from adafruit_itertools import chain
from audiomp3 import MP3Decoder

audio = audiobusio.I2SOut(board.GP10, board.GP11, board.GP9)
pwm = pwmio.PWMOut(board.GP17)

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
    
    await asyncio.gather(wifi)



if __name__ == "__main__":
    asyncio.run(main())
