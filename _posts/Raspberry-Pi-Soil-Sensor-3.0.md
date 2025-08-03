# 🌿 Introduction & Use Case:
If you’ve been following the evolution of the Raspberry Pi Soil Sensor project on DevSecOpsDad.com, you know it began as a fun side experiment to bring environmental telemetry into Microsoft Sentinel. From the original build to the more robust Sensor 2.0 upgrade and its multi-part series overcoming the bottleneck in Azure IoT Hub, we’ve integrated soil moisture and temperature readings into Azure Sentinel, Microsoft’s cloud-native SIEM.

But what if you want all the plant-monitoring goodness without the complexity of Sentinel, Log Analytics, or any cloud integration? 

This guide shows you how to deploy a completely self-contained Raspberry Pi Zero W soil sensor that logs data locally and hosts a mobile-friendly web dashboard over your Wi-Fi network. No Azure subscription, no SIEM plumbing—just real-time environmental telemetry accessible from your phone or browser.

Whether you're a home lab enthusiast, gardener, or someone just looking to build a clean local IoT project, this stripped-down deployment keeps all the insights and skips the cloud complexity, taking you from a blank SD card to a fully functional soil sensor web dashboard.




## 📋 Hardware Requirements

- Raspberry Pi Zero W
- MicroSD card (16GB+ recommended)
- I2C Soil Moisture & Temperature Sensor (Adafruit STEMMA)
- JST PH 2mm 4-Pin to Female Socket I2C STEMMA jumper cable
- GPIO Splitter (optional but recommended)
- MicroUSB power supply

## 🔧 Part 1: Initial Pi Setup (Headless)

### Step 1: Flash Raspberry Pi OS
1. Download [Raspberry Pi Imager](https://www.raspberrypi.org/software/)
2. Flash **Raspberry Pi OS Lite (Bullseye)** to your SD card
3. **Important**: Don't eject the SD card yet!

### Step 2: Enable SSH and WiFi (Headless Setup)
After flashing, the SD card will remount. Navigate to the boot partition and:

1. **Enable SSH**: Create an empty file named `ssh` (no extension)
   ```bash
   # On Windows: Create empty file called "ssh" in boot drive
   # On Mac/Linux:
   touch /Volumes/boot/ssh
   ```

2. **Configure WiFi**: Create `wpa_supplicant.conf` in the boot partition:
   ```bash
   # Create file: wpa_supplicant.conf
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1
   
   network={
       ssid="YOUR_WIFI_NAME"
       psk="YOUR_WIFI_PASSWORD"
   }
   ```
   **Replace `YOUR_WIFI_NAME` and `YOUR_WIFI_PASSWORD` with your actual WiFi credentials**

### Step 3: Boot and Connect
1. Insert SD card into Pi Zero W
2. Power on the Pi
3. Wait 2-3 minutes for boot
4. Find Pi's IP address:
   - Check your router's admin panel
   - Use network scanner app
   - Try: `ping raspberrypi.local`

### Step 4: SSH Into Your Pi
```bash
ssh pi@[PI_IP_ADDRESS]
# or
ssh pi@raspberrypi.local

# Default password: raspberry
```

## 🔄 Part 2: System Configuration

### Step 5: Basic System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Change default password (IMPORTANT!)
passwd

# Set timezone
sudo raspi-config
# Navigate: Localisation Options > Timezone > [Your Region] > [Your City]

# Expand filesystem
sudo raspi-config
# Navigate: Advanced Options > Expand Filesystem

# Enable I2C
sudo raspi-config
# Navigate: Interfacing Options > I2C > Enable

# Reboot to apply changes
sudo reboot
```

**Wait for reboot, then reconnect via SSH**

### Step 6: Install Required System Packages
```bash
# Install core packages
sudo apt install -y python3 python3-pip apache2 sqlite3 git i2c-tools

# Install Python I2C libraries
sudo apt install -y python3-smbus python3-dev

# Enable Apache CGI module
sudo a2enmod cgi

# Start and enable Apache
sudo systemctl enable apache2
sudo systemctl start apache2
```

## 🔌 Part 3: Hardware Connection

### Step 7: Connect Your Sensor
Connect the I2C soil sensor to your Pi Zero W:

```
Sensor Pin    →    Pi Zero W Pin
VCC (Red)     →    3.3V (Pin 1)
GND (Black)   →    Ground (Pin 6)  
SDA (White)    →    GPIO 2/SDA (Pin 3)
SCL (Green)  →    GPIO 3/SCL (Pin 5)
```

![](/assets/img/IoT%20Hub%202/Soil_PinOut.png)

### Step 8: Test Hardware Connection
```bash
# Test I2C connection
sudo i2cdetect -y 1

# You should see address 36 populated:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 30: -- -- -- -- -- -- 36 -- -- -- -- -- -- -- -- -- 
```

>&#x1F449; If you don't see address 36, check your wiring!
 
  
## 🐍 Part 4: Install Python Dependencies

### Step 9: Install Sensor Libraries
```bash
# Install Adafruit libraries
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-busdevice
sudo pip3 install adafruit-circuitpython-seesaw
```

## 📁 Part 5: Deploy the Soil Sensor Application

### Step 10: Create Application Structure
```bash
# Create directories
sudo mkdir -p /opt/soil_sensor
sudo mkdir -p /var/log

# Make sure Apache CGI directory is ready
sudo chmod 755 /usr/lib/cgi-bin
```

### Step 11: Install Main Sensor Script
```bash
# Create the sensor reader script
sudo nano /opt/soil_sensor/sensor_reader.py
```

**Copy and paste the entire `sensor_reader.py` content from ![here](/assets/Code/Sensor%203.0/sensor_reader.py)**, then:

```bash
# Make executable
sudo chmod +x /opt/soil_sensor/sensor_reader.py
```

>&#x1F449; This Python script is a soil sensor data logger designed for the Raspberry Pi Zero W. It interfaces with an Adafruit STEMMA I²C soil sensor to collect temperature and moisture data, storing each reading in a local SQLite database. The script also writes the latest reading to a JSON file, enabling easy integration with a self-hosted web interface for real-time monitoring. Key features include automatic database initialization, I²C sensor setup, data cleanup routines for managing storage, and a built-in logging mechanism for diagnostics.

> 💡 The program is structured as a class (SoilSensorLogger) with modular methods that handle sensor interaction, database management, and web data export. It’s optimized for periodic execution—ideal for use with cron or a systemd timer—making it a robust foundation for environmental monitoring projects in gardens, greenhouses, or smart home setups.



### Step 12: Install Web API Script
```bash
# Create the API script
sudo nano /usr/lib/cgi-bin/api.py
```

**Copy and paste the entire `api.py` content from the second artifact**, then:
```bash
# Make executable
sudo chmod +x /usr/lib/cgi-bin/api.py
```

### Step 13: Install Web Interface
```bash
# Remove default Apache page
sudo rm /var/www/html/index.html

# Create new dashboard
sudo nano /var/www/html/index.html
```

**Copy and paste the entire `index.html` content from the third artifact**, then:
```bash
# Set proper permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod 644 /var/www/html/index.html
sudo chmod 666 /var/www/html  # Allow database creation
```

## ⚡ Part 6: Test Your Installation

### Step 14: Take First Sensor Reading
```bash
# Test the sensor script
sudo python3 /opt/soil_sensor/sensor_reader.py

# You should see output like:
# INFO:root:Database initialized successfully
# INFO:root:Sensor initialized successfully  
# INFO:root:Sensor reading - Temperature: 23.4°C, Moisture: 485
# INFO:root:Data stored successfully - Temp: 23.4°C, Moisture: 485
# Sensor reading completed successfully
```

### Step 15: Test Web Interface
1. **Find your Pi's IP address**:
   ```bash
   ip addr show wlan0 | grep inet
   ```

2. **Open web browser** and navigate to:
   - `http://[YOUR_PI_IP]/`
   - `http://raspberrypi.local/`

3. **Test API directly**:
   ```bash
   curl http://localhost/cgi-bin/api.py?action=latest
   ```

You should see your sensor data displayed on the dashboard!

## 🕐 Part 7: Automate Data Collection

### Step 16: Set Up Hourly Data Collection
```bash
# Open crontab for editing
sudo crontab -e

# Add this line at the bottom:
0 * * * * /usr/bin/python3 /opt/soil_sensor/sensor_reader.py >> /var/log/soil_sensor_cron.log 2>&1

# Save and exit (Ctrl+X, Y, Enter in nano)
```

This will take a sensor reading every hour automatically.

### Step 17: Enable Log Rotation (Optional)
```bash
# Create log rotation config
sudo nano /etc/logrotate.d/soil-sensor

# Add this content:
/var/log/soil_sensor*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

## 🎯 Part 8: Final Configuration

### Step 18: Restart Apache
```bash
sudo systemctl restart apache2
```

### Step 19: Test Everything
```bash
# Check sensor logs
tail -f /var/log/soil_sensor.log

# Check cron logs  
tail -f /var/log/soil_sensor_cron.log

# Check Apache status
sudo systemctl status apache2
```

## 🌐 Part 9: Access Your Dashboard

Your soil sensor dashboard is now available at:
- **Local Network**: `http://[PI_IP_ADDRESS]/`
- **Hostname**: `http://raspberrypi.local/` (if unchanged)

The dashboard will show:
- ✅ Current temperature and moisture readings
- 📊 Historical charts (24 hours, 7 days, 30 days)
- 🔄 Auto-refresh every 5 minutes
- 📱 Mobile-responsive design

## 🛠️ Troubleshooting

### Common Issues:

**❌ Sensor not detected (`i2cdetect` shows no device at 36):**
- Check wiring connections
- Ensure I2C is enabled: `sudo raspi-config`
- Try different jumper wires

**❌ Permission errors:**
```bash
sudo chown -R www-data:www-data /var/www/html
sudo chmod 666 /var/www/html
sudo chmod +x /usr/lib/cgi-bin/api.py
```

**❌ Apache errors:**
```bash
# Check Apache logs
sudo tail -f /var/log/apache2/error.log

# Restart Apache
sudo systemctl restart apache2
```

**❌ Database issues:**
```bash
# Check database location and permissions
ls -la /var/www/html/sensor_data.db
sudo chown www-data:www-data /var/www/html/sensor_data.db
```

**❌ Cron job not running:**
```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail
```

## 📊 Usage Tips

- **Manual reading**: `sudo python3 /opt/soil_sensor/sensor_reader.py`
- **View live logs**: `tail -f /var/log/soil_sensor.log`
- **Check database**: `sqlite3 /var/www/html/sensor_data.db "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 5;"`
- **Change reading frequency**: Edit crontab with `sudo crontab -e`

## 🎉 You're Done!

Your Raspberry Pi Zero W is now running a complete soil sensor monitoring system with:
- Automated hourly data collection
- 30-day data retention
- Beautiful web dashboard
- Real-time and historical charts
- Mobile-friendly interface

Enjoy monitoring your plants! 🌱
