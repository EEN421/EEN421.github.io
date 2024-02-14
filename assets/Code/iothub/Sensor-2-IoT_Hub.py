import time
import board
from azure.iot.device import IoTHubDeviceClient, Message
from adafruit_seesaw.seesaw import Seesaw

# Initialize I2C bus and Seesaw sensor
i2c_bus = board.I2C()  # uses board.SCL and board.SDA
ss = Seesaw(i2c_bus, addr=0x36)

# Connection String to Azure IoT Hub
CONNECTION_STRING = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

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

            # Format 'message' variables to 2 decimal places via .format
            msg_txt_formatted = '{{"Temperature": {:.2f}, "Humidity": {:.2f}}}'.format(temp, touch)
            message = Message(msg_txt_formatted)
            print("Sending message: {}".format(message))
            client.send_message(message)
            print("Message successfully sent")
            time.sleep(3) #<-- runs every 3 seconds. Change this value when done testing to 300 (5 minutes) or 600 (10 minutes) etc.
    except KeyboardInterrupt:
        print("IoTHubClient stopped")

if __name__ == '__main__':
    print("Press Ctrl-C to exit")
    iothub_client_telemetry_sample_run()
