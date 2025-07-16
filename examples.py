#!/usr/bin/env python3
"""
Example usage of the dataviz plotting functions.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from quick_plot import quick_plot, plot_dataframe, plot_sensor_data
from sensor_simulator import BiogasSensorSimulator, example_simulate_and_save
from live_plot import example_live_plot_basic, example_live_plot_normalized
from dashboard import run_dashboard


def example_basic_plotting():
    """Example of basic quick plotting with different data types."""
    print("=== Basic Quick Plot Examples ===")
    
    # Example 1: Simple array data
    print("1. Plotting simple array data...")
    data = np.random.randn(100)
    fig = quick_plot(data, title="Random Data")
    plt.show()
    
    # Example 2: Multiple series
    print("2. Plotting multiple series...")
    data = np.random.randn(3, 50)
    fig = quick_plot(data, title="Multiple Series")
    plt.show()
    
    # Example 3: Dictionary data
    print("3. Plotting dictionary data...")
    data = {
        'temperature': np.random.normal(25, 2, 100),
        'pressure': np.random.normal(101, 0.5, 100),
        'flow': np.random.exponential(2, 100)
    }
    fig = quick_plot(data, title="Dictionary Data")
    plt.show()


def example_dataframe_plotting():
    """Example of DataFrame plotting."""
    print("=== DataFrame Plotting Examples ===")
    
    # Create sample DataFrame
    dates = pd.date_range('2024-01-01', periods=200, freq='1min')
    df = pd.DataFrame({
        'datetime': dates,
        'temperature': 25 + 3 * np.sin(np.arange(200) * 0.1) + np.random.normal(0, 0.5, 200),
        'humidity': 60 + 10 * np.cos(np.arange(200) * 0.05) + np.random.normal(0, 2, 200),
        'pressure': 101.3 + 0.5 * np.sin(np.arange(200) * 0.02) + np.random.normal(0, 0.1, 200),
        'flow': 10 + 2 * np.sin(np.arange(200) * 0.03) + np.random.normal(0, 0.5, 200)
    })
    
    print("1. Plotting DataFrame columns...")
    fig = plot_dataframe(df, x_column='datetime', title="Time Series Data")
    plt.show()
    
    print("2. Plotting specific columns...")
    fig = plot_dataframe(df, columns=['temperature', 'humidity'], x_column='datetime')
    plt.show()
    
    print("3. Scatter plot with color mapping...")
    fig = plot_dataframe(df, columns=['flow'], x_column='temperature', 
                        color_column='pressure', plot_type='scatter')
    plt.show()


def example_sensor_data_simulation():
    """Example of sensor data simulation and plotting."""
    print("=== Sensor Data Simulation Examples ===")
    
    # Create simulator
    simulator = BiogasSensorSimulator()
    
    print("1. Generating and plotting simulated sensor data...")
    df = simulator.generate_dataframe(duration_minutes=30, interval_seconds=2)
    
    # Plot sensor data
    fig = plot_sensor_data(df=df, title="Simulated Biogas Sensor Data")
    plt.show()
    
    # Save to CSV for future use
    df.to_csv('/tmp/simulated_sensor_data.csv')
    print("   Saved data to /tmp/simulated_sensor_data.csv")
    
    print("2. Plotting from CSV file...")
    fig = plot_sensor_data(csv_file='/tmp/simulated_sensor_data.csv', 
                          title="Sensor Data from CSV")
    plt.show()


def example_custom_plotting():
    """Example of custom plotting scenarios."""
    print("=== Custom Plotting Examples ===")
    
    # Create complex data
    simulator = BiogasSensorSimulator()
    df = simulator.generate_dataframe(duration_minutes=60, interval_seconds=1)
    
    # Custom plotting with color mapping
    print("1. Custom plot with color mapping...")
    fig = quick_plot(df, 
                    x='temp_degC', 
                    y=['flow', 'concentration_ch4'], 
                    color='d0_pressure',
                    title="Flow vs Temperature with Pressure Coloring")
    plt.show()
    
    # Multiple variables over time
    print("2. Multiple variables over time...")
    time_col = df.index
    variables = ['temp_degC', 'flow', 'concentration_ch4', 'd0_power_flow']
    y_data = [df[var].values for var in variables]
    
    fig = quick_plot(df, x=time_col, y=y_data, title="Multiple Variables Over Time")
    plt.show()


def example_live_plotting():
    """Example of live plotting (requires manual interruption)."""
    print("=== Live Plotting Examples ===")
    print("Note: These examples will run until manually stopped (Ctrl+C)")
    
    response = input("Run live plotting examples? (y/n): ")
    if response.lower() == 'y':
        print("1. Starting basic live plot...")
        print("   Press Ctrl+C to stop and continue to next example")
        try:
            example_live_plot_basic()
        except KeyboardInterrupt:
            print("   Stopped basic live plot")
        
        print("2. Starting normalized multi-variable live plot...")
        print("   Press Ctrl+C to stop")
        try:
            example_live_plot_normalized()
        except KeyboardInterrupt:
            print("   Stopped normalized live plot")


def example_dashboard():
    """Example of running the dashboard."""
    print("=== Dashboard Example ===")
    
    response = input("Run dashboard example? (y/n): ")
    if response.lower() == 'y':
        print("Starting dashboard at http://localhost:8050")
        print("Press Ctrl+C to stop")
        try:
            run_dashboard()
        except KeyboardInterrupt:
            print("Dashboard stopped")


def run_all_examples():
    """Run all examples in sequence."""
    print("Dataviz Examples - Biogas Sensor Visualization")
    print("=" * 50)
    
    try:
        example_basic_plotting()
        example_dataframe_plotting()
        example_sensor_data_simulation()
        example_custom_plotting()
        example_live_plotting()
        example_dashboard()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")
    
    print("\nAll examples completed!")


if __name__ == '__main__':
    run_all_examples()