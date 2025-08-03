#!/usr/bin/env python3
"""
Raspberry Pi Zero W Soil Sensor Data Logger
Reads I2C soil moisture and temperature sensor data and stores in SQLite database
"""

import time
import sqlite3
import json
from datetime import datetime, timedelta
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.seesaw import Seesaw  # Redundant import, but harmless
import logging

# Configure logging to file and stdout for troubleshooting and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/soil_sensor.log'),  # Log file path
        logging.StreamHandler()  # Also log to console
    ]
)

class SoilSensorLogger:
    def __init__(self, db_path='/var/www/html/sensor_data.db'):
        # Path to the SQLite database (served from the web directory)
        self.db_path = db_path
        self.setup_database()  # Create DB schema if needed
        self.setup_sensor()    # Initialize I2C sensor

    def setup_database(self):
        """Initialize SQLite database with sensor data table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create the main table to store sensor readings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    temperature REAL,
                    moisture INTEGER
                )
            ''')

            # Index for faster queries by timestamp
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_readings(timestamp)
            ''')

            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")

        except Exception as e:
            logging.error(f"Database setup error: {e}")
            raise

    def setup_sensor(self):
        """Initialize I2C connection to soil sensor"""
        try:
            # Create I2C bus on default SCL/SDA pins
            i2c_bus = busio.I2C(board.SCL, board.SDA)

            # Initialize the Seesaw sensor at address 0x36
            self.ss = Seesaw(i2c_bus, addr=0x36)

            logging.info("Sensor initialized successfully")

        except Exception as e:
            logging.error(f"Sensor setup error: {e}")
            raise

    def read_sensor_data(self):
        """Read temperature and moisture from sensor"""
        try:
            # Get temperature in Celsius
            temp = self.ss.get_temp()

            # Get moisture reading (range: 0-1023)
            moisture = self.ss.moisture_read()

            logging.info(f"Sensor reading - Temperature: {temp:.1f}°C, Moisture: {moisture}")

            return temp, moisture

        except Exception as e:
            logging.error(f"Sensor reading error: {e}")
            return None, None

    def store_reading(self, temperature, moisture):
        """Store sensor reading in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Insert a new row of data into the table
            cursor.execute('''
                INSERT INTO sensor_readings (temperature, moisture)
                VALUES (?, ?)
            ''', (temperature, moisture))

            conn.commit()
            conn.close()

            logging.info(f"Data stored successfully - Temp: {temperature:.1f}°C, Moisture: {moisture}")

        except Exception as e:
            logging.error(f"Database storage error: {e}")

    def cleanup_old_data(self, days=30):
        """Remove data older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate timestamp cutoff for deletion
            cutoff_date = datetime.now() - timedelta(days=days)

            # Delete records older than cutoff
            cursor.execute('''
                DELETE FROM sensor_readings
                WHERE timestamp < ?
            ''', (cutoff_date,))

            deleted_rows = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_rows > 0:
                logging.info(f"Cleaned up {deleted_rows} old records")

        except Exception as e:
            logging.error(f"Database cleanup error: {e}")

    def get_latest_reading(self):
        """Get the most recent sensor reading"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Select the most recent row from the table
            cursor.execute('''
                SELECT timestamp, temperature, moisture
                FROM sensor_readings
                ORDER BY timestamp DESC
                LIMIT 1
            ''')

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'timestamp': result[0],
                    'temperature': result[1],
                    'moisture': result[2]
                }
            return None

        except Exception as e:
            logging.error(f"Database query error: {e}")
            return None

    def run_single_reading(self):
        """Take a single sensor reading and store it"""
        logging.info("Starting sensor reading...")

        # Read temperature and moisture
        temperature, moisture = self.read_sensor_data()

        if temperature is not None and moisture is not None:
            # Store the data
            self.store_reading(temperature, moisture)

            # Clean up older entries
            self.cleanup_old_data()

            # Update the JSON file for web access
            self.update_latest_json(temperature, moisture)

            logging.info("Sensor reading cycle completed successfully")
            return True
        else:
            logging.error("Failed to read sensor data")
            return False

    def update_latest_json(self, temperature, moisture):
        """Update JSON file with latest reading for web interface"""
        try:
            latest_data = {
                'timestamp': datetime.now().isoformat(),  # ISO format for compatibility
                'temperature': round(temperature, 1),
                'moisture': moisture,
                'temperature_f': round((temperature * 9/5) + 32, 1)  # Convert to Fahrenheit
            }

            # Save latest reading as JSON to be used by web dashboard
            with open('/var/www/html/latest_reading.json', 'w') as f:
                json.dump(latest_data, f, indent=2)

        except Exception as e:
            logging.error(f"JSON update error: {e}")

def main():
    """Main function to run sensor logger"""
    try:
        logger = SoilSensorLogger()  # Initialize logger
        success = logger.run_single_reading()  # Run full sensor + store cycle

        if success:
            print("Sensor reading completed successfully")
        else:
            print("Sensor reading failed")
            exit(1)

    except Exception as e:
        logging.error(f"Main execution error: {e}")
        print(f"Error: {e}")
        exit(1)

# Ensure script runs only when executed directly, not when imported
if __name__ == "__main__":
    main()