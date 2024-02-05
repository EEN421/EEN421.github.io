import board
import socket
import subprocess
import datetime
import time
import board
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from azure.iot.device import IoTHubDeviceClient, Message
from adafruit_seesaw.seesaw import Seesaw
from datetime import datetime, date

# Initialize I2C bus and Seesaw sensor
i2c_bus = board.I2C()  # uses board.SCL and board.SDA
ss = Seesaw(i2c_bus, addr=0x36)

# Create the I2C interface
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Clear display
disp.fill(0)
disp.show()

# Create blank image for drawing
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Default font. Commented out while slkscr.ttf is in use
#font = ImageFont.load_default()

# Load silkscreen font.
font = ImageFont.truetype('/home/ian/Adafruit_CircuitPython_seesaw/Font/slkscr.ttf', 8)

# Connection String to Azure IoT Hub
CONNECTION_STRING = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

def iothub_client_init():
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    return client

def iothub_client_telemetry_sample_run():
    try:
        client = iothub_client_init()
        print("Sending data to IoT Hub, press Ctrl-C to exit")
        while True:
            # Read moisture level through capacitive touch pad
            touch = ss.moisture_read()

            # Read temperature from the temperature sensor
            temp = (ss.get_temp() * (9 / 5) + 32)

                # Draw a black filled box to clear the image
            draw.rectangle((0, 0, width, height), outline=0, fill=0)

            # System monitoring variables defined
            cmd = "hostname -I | cut -d' ' -f1"
            IP = subprocess.check_output(cmd, shell=True).decode("utf-8")

            # read moisture level through capacitive touch pad
            touch = ss.moisture_read()

            # read temperature from the temperature sensor
            temp = (ss.get_temp() * (9 / 5) + 32)

            current_time = datetime.now()

            #'hostname' variable defined
            hostname = socket.gethostname()

            # Write four lines of text
            draw.text((x, top + 0), "Host: " + str(hostname), font=font, fill=255)
            draw.text((x, top + 8), "IP: " + IP, font=font, fill=255)
            draw.text((x, top + 16), "Temperature: " + str('%.2f'%temp), font=font, fill=255)
            draw.text((x, top + 25), "Moisture: " + str('%.2f'%touch), font=font, fill=255)

            # Display image
            disp.image(image)
            disp.show()

            msg_txt_formatted = '{{"Temperature": {:.2f}, "Humidity": {:.2f}}}'.format(temp, touch)
            message = Message(msg_txt_formatted)
            print("Sending message: {}".format(message))
            client.send_message(message)
            print("Message successfully sent")
            time.sleep(3)
    except KeyboardInterrupt:
        print("IoTHubClient stopped")

if __name__ == '__main__':
    print("Press Ctrl-C to exit")
    iothub_client_telemetry_sample_run()
