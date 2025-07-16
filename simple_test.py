#!/usr/bin/env python3
"""
Simple test of dataviz functionality without external dependencies.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if we can import the modules."""
    print("Testing imports...")
    
    try:
        import numpy as np
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print("✓ matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ matplotlib import failed: {e}")
        return False
    
    try:
        from quick_plot import quick_plot
        print("✓ quick_plot imported successfully")
    except ImportError as e:
        print(f"✗ quick_plot import failed: {e}")
        return False
    
    try:
        from sensor_simulator import BiogasSensorSimulator
        print("✓ sensor_simulator imported successfully")
    except ImportError as e:
        print(f"✗ sensor_simulator import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without plotting."""
    print("\nTesting basic functionality...")
    
    try:
        import numpy as np
        import pandas as pd
        from sensor_simulator import BiogasSensorSimulator
        
        # Test simulator
        simulator = BiogasSensorSimulator()
        print("✓ BiogasSensorSimulator created")
        
        # Generate a single reading
        reading = simulator.generate_sensor_reading()
        print(f"✓ Generated sensor reading: {reading}")
        
        # Generate CSV row
        csv_row = simulator.generate_csv_row()
        print(f"✓ Generated CSV row with {len(csv_row)} fields")
        
        # Generate small DataFrame
        df = simulator.generate_dataframe(duration_minutes=1, interval_seconds=10)
        print(f"✓ Generated DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Test serial output
        serial_output = simulator.generate_serial_output()
        print(f"✓ Generated serial output: {serial_output[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Dataviz Simple Test")
    print("=" * 30)
    
    if not test_imports():
        print("\n❌ Import tests failed. Please install required packages:")
        print("pip install pandas numpy matplotlib seaborn")
        return False
    
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed.")
        return False
    
    print("\n✅ All tests passed!")
    print("\nTo run full examples, install all dependencies:")
    print("pip install -r requirements.txt")
    print("python examples.py")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)