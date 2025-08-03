#!/usr/bin/env python3
"""
CGI API script to serve sensor data to web interface
Place in /usr/lib/cgi-bin/ directory
"""

import cgi                      # For parsing query parameters in CGI requests
import cgitb                    # For detailed error tracebacks in browser
import json                     # For encoding Python objects to JSON
import sqlite3                  # SQLite database access
from datetime import datetime, timedelta  # For time manipulation
import sys                      # Provides access to system-specific parameters
import os                       # Operating system interface (not used in code but imported)

# Enable detailed error reporting in browser for debugging CGI scripts
cgitb.enable()

# CGI scripts must start with content-type headers before output
print("Content-Type: application/json")
print()  # Blank line separates headers from response body

def get_db_connection():
    """Establish and return connection to SQLite database"""
    db_path = '/var/www/html/sensor_data.db'  # Path to SQLite database file
    return sqlite3.connect(db_path)

def get_latest_reading():
    """Fetch the most recent sensor reading from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get the most recent row by timestamp
        cursor.execute('''
            SELECT timestamp, temperature, moisture
            FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        result = cursor.fetchone()
        conn.close()

        # If a result is found, format and return it
        if result:
            return {
                'timestamp': result[0],
                'temperature': round(result[1], 1),
                'moisture': result[2],
                'temperature_f': round((result[1] * 9/5) + 32, 1)  # Convert °C to °F
            }
        return None  # No data in table

    except Exception as e:
        # Return any error message as part of the JSON response
        return {'error': str(e)}

def get_historical_data(hours=24):
    """Retrieve sensor readings from the past 'hours' period"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate cutoff time (now - specified hours)
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Fetch rows where the timestamp is within the period
        cursor.execute('''
            SELECT timestamp, temperature, moisture
            FROM sensor_readings
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        ''', (cutoff_time,))

        results = cursor.fetchall()
        conn.close()

        # Format each row into a dictionary for JSON output
        data = []
        for row in results:
            data.append({
                'timestamp': row[0],
                'temperature': round(row[1], 1),
                'moisture': row[2],
                'temperature_f': round((row[1] * 9/5) + 32, 1)
            })

        return data

    except Exception as e:
        # Return any error that occurred
        return {'error': str(e)}

def get_statistics(hours=24):
    """Compute basic statistics on temperature and moisture over past 'hours'"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate the cutoff time for the statistics window
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # SQL aggregates to compute count, average, min, and max values
        cursor.execute('''
            SELECT
                COUNT(*) as count,
                AVG(temperature) as avg_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(moisture) as avg_moisture,
                MIN(moisture) as min_moisture,
                MAX(moisture) as max_moisture
            FROM sensor_readings
            WHERE timestamp >= ?
        ''', (cutoff_time,))

        result = cursor.fetchone()
        conn.close()

        # Only return statistics if at least one row is found
        if result and result[0] > 0:
            return {
                'count': result[0],
                'temperature': {
                    'average': round(result[1], 1),
                    'minimum': round(result[2], 1),
                    'maximum': round(result[3], 1)
                },
                'moisture': {
                    'average': round(result[4], 0),
                    'minimum': result[5],
                    'maximum': result[6]
                }
            }
        return {'count': 0}  # No rows matched

    except Exception as e:
        return {'error': str(e)}

def main():
    """Main handler for CGI requests"""
    try:
        # Parse query string parameters (e.g., ?action=latest)
        form = cgi.FieldStorage()
        action = form.getvalue('action', 'latest')  # Default to 'latest'
        period = form.getvalue('period', '24')      # Default to 24 hours

        # Convert 'period' to integer, default to 24 on failure
        try:
            period_hours = int(period)
        except (ValueError, TypeError):
            period_hours = 24

        # Route to appropriate data handler based on 'action' parameter
        if action == 'latest':
            data = get_latest_reading()
        elif action == 'history':
            data = get_historical_data(period_hours)
        elif action == 'stats':
            data = get_statistics(period_hours)
        else:
            data = {'error': 'Invalid action parameter'}

        # Output data as formatted JSON
        print(json.dumps(data, indent=2))

    except Exception as e:
        # Handle any unexpected server-side exceptions
        error_response = {'error': f'Server error: {str(e)}'}
        print(json.dumps(error_response, indent=2))

# Entry point for CGI execution
if __name__ == '__main__':
    main()
