#!/usr/bin/env python3
"""
Example script to run ThingsBoard dashboard.

This script demonstrates how to use the BiogasDashboard with ThingsBoard integration.
"""

from dashboard import run_thingsboard_dashboard

def main():
    """Main function to run ThingsBoard dashboard."""
    
    # Example configuration for ThingsBoard demo server
    # Replace these values with your actual ThingsBoard setup
    run_thingsboard_dashboard(
        host="demo.thingsboard.io",  # Your ThingsBoard server
        port=443,                    # Use 443 for HTTPS, 8080 for HTTP
        username="tenant@thingsboard.org",  # Your username
        password="tenant",           # Your password
        use_ssl=True,               # Use HTTPS
        device_name="DHT22 Demo Device",  # Your device name
        telemetry_keys=["temperature", "humidity", "pressure", "flow"]  # Your telemetry keys
    )

def run_local_thingsboard():
    """Example for local ThingsBoard installation."""
    run_thingsboard_dashboard(
        host="localhost",
        port=8080,
        username="tenant@thingsboard.org",
        password="tenant",
        use_ssl=False,
        device_name="My Device",
        telemetry_keys=["temp", "pressure", "flow", "comp"]
    )

if __name__ == "__main__":
    print("ThingsBoard Dashboard Example")
    print("=" * 40)
    print("1. Demo server (default)")
    print("2. Local installation")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "2":
        run_local_thingsboard()
    else:
        main()