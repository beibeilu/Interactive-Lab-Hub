import time
from datetime import datetime
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789
import webcolors

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
fontLarge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()

# Helpers
def to_time(value: str) -> int:
	dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
	return dt

def strfdelta(tdelta, fmt):
	d = {"days": tdelta.days}
	d["hours"], rem = divmod(tdelta.seconds, 3600)
	d["minutes"], d["seconds"] = divmod(rem, 60)
	return fmt.format(**d)

countdowns = {
	"Wellness Day": "2021-03-09 00:00:00",
	"Graduation Day": "2021-05-26 10:00:00",
        "Tax Day": "2021-04-15 00:00:00"
        }

def part_of_day():
	hour = datetime.now().hour
	return ("morning" if 5 <= hour <= 11
                else
                    "afternoon" if 12 <= hour <= 17
                else
    	            "evening" if 18 <= hour <= 22
	    	else
	            "night"
	)

index = 0

def screencolor(timeOfDay):
	return(color565(168, 235, 18) if timeOfDay == "morning"
    		else
			color565(184, 208, 253) if timeOfDay == "afternoon"
    		else
    			color565(132, 94, 194) if timeOfDay == "evening"
	    	else
        		color565(5, 25, 55)
	)

def show_countdown(index):
	delta = to_time(list(countdowns.values())[index]) - datetime.now()
	line1 = strfdelta(delta, "{days} days {hours} hours and {minutes} min")
	line2 = "until " + list(countdowns)[index]
	return (line1, line2)

def getWeather():
    cmd = "weather fips5114968"
    weather = subprocess.check_output(cmd, shell=True).decode("utf-8")
    text = weather.splitlines()
    
    temp = text[2].split(": ")[1]
    cond = text[-1].split(": ")[1]
    return temp + "\n" + cond

#show_countdown(index)
listcounter = 0
while True: 
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0,
            fill=screencolor(part_of_day()))
    
    # Show current time
    t = time.strftime("%m/%d/%Y %H:%M:%S")
    y = top
    draw.text((x, y), t, font=fontLarge, fill="#FFFFFF")
    
    greeting = "Good " + part_of_day() + "!"
    y += font.getsize(t)[1]*2
    draw.text((x, y), greeting, font=font, fill="#FFFF00")

    weather = getWeather()
    y += font.getsize(weather)[1]*2
    draw.text((x, y), weather, font=font, fill="#FFFFFF")


    if buttonA.value and not buttonB.value:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        listcounter += 1
        i = listcounter % len(countdowns)
        text = show_countdown(i)
        y = top
        draw.text((x, y), text[0], font=font, fill="#FFFFFF")
        y += font.getsize(text[0])[1]
        draw.text((x, y), text[1], font=font, fill="#FFFF00")

    if buttonB.value and not buttonA.value:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Display image
    disp.image(image, rotation)
    time.sleep(1)
