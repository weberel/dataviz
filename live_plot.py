import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from collections import deque
from datetime import datetime
import threading
import time
from typing import List, Dict, Any, Optional, Callable, Union
from sensor_simulator import BiogasSensorSimulator, ThreadedSensorSimulator


class LivePlotter:
    """Create live updating plots for sensor data."""
    
    def __init__(self, 
                 data_source: Optional[Union[ThreadedSensorSimulator, Callable]] = None,
                 max_points: int = 100,
                 update_interval: int = 1000):
        """
        Initialize live plotter.
        
        Parameters:
        -----------
        data_source : ThreadedSensorSimulator or callable
            Source of data. If callable, should return dict with sensor values
        max_points : int
            Maximum number of points to display
        update_interval : int
            Update interval in milliseconds
        """
        self.data_source = data_source
        self.max_points = max_points
        self.update_interval = update_interval
        
        # Data storage
        self.time_data = deque(maxlen=max_points)
        self.data_streams = {}
        
        # Plot elements
        self.fig = None
        self.axes = None
        self.lines = {}
        
        # Animation
        self.animation = None
        
    def setup_plot(self, 
                   variables: List[str],
                   title: str = "Live Sensor Data",
                   figsize: Optional[tuple] = None):
        """
        Setup the plot layout.
        
        Parameters:
        -----------
        variables : list of str
            Variable names to plot
        title : str
            Figure title
        figsize : tuple
            Figure size (width, height)
        """
        # Calculate subplot layout
        n_plots = len(variables)
        if n_plots <= 1:
            rows, cols = 1, 1
        elif n_plots <= 2:
            rows, cols = 1, 2
        elif n_plots <= 4:
            rows, cols = 2, 2
        else:
            cols = 3
            rows = (n_plots + cols - 1) // cols
        
        if figsize is None:
            figsize = (5 * cols, 4 * rows)
        
        # Create figure and subplots
        self.fig, self.axes = plt.subplots(rows, cols, figsize=figsize, squeeze=False)
        self.fig.suptitle(title)
        self.axes = self.axes.flatten()
        
        # Hide extra subplots
        for i in range(n_plots, len(self.axes)):
            self.axes[i].set_visible(False)
        
        # Initialize data streams and plot lines
        for i, var in enumerate(variables):
            self.data_streams[var] = deque(maxlen=self.max_points)
            ax = self.axes[i]
            line, = ax.plot([], [], 'b-')
            self.lines[var] = line
            
            ax.set_ylabel(var)
            ax.set_xlabel('Time (s)')
            ax.set_title(var)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
    def update_data(self, frame):
        """Update data from source."""
        if self.data_source is None:
            return
        
        # Get new data
        if isinstance(self.data_source, ThreadedSensorSimulator):
            new_data = self.data_source.get_latest_data()
        elif callable(self.data_source):
            new_data = self.data_source()
        else:
            return
        
        if new_data is None:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in new_data:
            new_data['timestamp'] = datetime.now()
        
        # Calculate time offset from start
        if len(self.time_data) == 0:
            self.start_time = new_data['timestamp']
            time_offset = 0
        else:
            time_offset = (new_data['timestamp'] - self.start_time).total_seconds()
        
        self.time_data.append(time_offset)
        
        # Update data streams
        for var, values in self.data_streams.items():
            if var in new_data:
                values.append(new_data[var])
            elif var == 'ch4_concentration' and 'comp' in new_data:
                # Derive CH4 concentration from compensation ratio if needed
                values.append(new_data['comp'] * 50)  # Simplified conversion
            else:
                # Keep previous value or use 0
                values.append(values[-1] if len(values) > 0 else 0)
        
        # Update plots
        for var, line in self.lines.items():
            if len(self.data_streams[var]) > 0:
                line.set_data(list(self.time_data), list(self.data_streams[var]))
                
                # Update axis limits
                ax = line.axes
                ax.relim()
                ax.autoscale_view()
        
        return list(self.lines.values())
    
    def start(self):
        """Start the live plot animation."""
        self.animation = animation.FuncAnimation(
            self.fig, 
            self.update_data, 
            interval=self.update_interval,
            blit=True,
            cache_frame_data=False
        )
        plt.show()
    
    def stop(self):
        """Stop the animation."""
        if self.animation:
            self.animation.event_source.stop()


class MultiVariableLivePlot:
    """Live plot with multiple variables in single axes."""
    
    def __init__(self, 
                 data_source: Optional[Union[ThreadedSensorSimulator, Callable]] = None,
                 max_points: int = 100,
                 update_interval: int = 1000):
        """
        Initialize multi-variable live plotter.
        
        Parameters are same as LivePlotter.
        """
        self.data_source = data_source
        self.max_points = max_points
        self.update_interval = update_interval
        
        # Data storage
        self.time_data = deque(maxlen=max_points)
        self.data_streams = {}
        
        # Plot elements
        self.fig = None
        self.ax = None
        self.lines = {}
        
        # Animation
        self.animation = None
        self.start_time = None
        
    def setup_plot(self, 
                   variables: List[str],
                   title: str = "Live Sensor Data",
                   figsize: tuple = (10, 6),
                   normalize: bool = False):
        """
        Setup the plot.
        
        Parameters:
        -----------
        variables : list of str
            Variable names to plot
        title : str
            Figure title
        figsize : tuple
            Figure size
        normalize : bool
            Whether to normalize variables to 0-1 range
        """
        self.normalize = normalize
        self.variables = variables
        
        # Create figure
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.fig.suptitle(title)
        
        # Initialize data streams and plot lines
        colors = plt.cm.get_cmap('tab10')
        for i, var in enumerate(variables):
            self.data_streams[var] = deque(maxlen=self.max_points)
            line, = self.ax.plot([], [], label=var, color=colors(i))
            self.lines[var] = line
            
            # Store normalization parameters
            if self.normalize:
                self.data_streams[f"{var}_min"] = float('inf')
                self.data_streams[f"{var}_max"] = float('-inf')
        
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Value' + (' (normalized)' if normalize else ''))
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        
    def update_data(self, frame):
        """Update data from source."""
        if self.data_source is None:
            return
        
        # Get new data
        if isinstance(self.data_source, ThreadedSensorSimulator):
            new_data = self.data_source.get_latest_data()
        elif callable(self.data_source):
            new_data = self.data_source()
        else:
            return
        
        if new_data is None:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in new_data:
            new_data['timestamp'] = datetime.now()
        
        # Calculate time offset
        if self.start_time is None:
            self.start_time = new_data['timestamp']
            time_offset = 0
        else:
            time_offset = (new_data['timestamp'] - self.start_time).total_seconds()
        
        self.time_data.append(time_offset)
        
        # Update data streams
        for var in self.variables:
            if var in new_data:
                value = new_data[var]
                self.data_streams[var].append(value)
                
                # Update normalization bounds
                if self.normalize:
                    self.data_streams[f"{var}_min"] = min(self.data_streams[f"{var}_min"], value)
                    self.data_streams[f"{var}_max"] = max(self.data_streams[f"{var}_max"], value)
        
        # Update plots
        for var, line in self.lines.items():
            if len(self.data_streams[var]) > 0:
                y_data = list(self.data_streams[var])
                
                # Normalize if requested
                if self.normalize:
                    y_min = self.data_streams[f"{var}_min"]
                    y_max = self.data_streams[f"{var}_max"]
                    if y_max > y_min:
                        y_data = [(y - y_min) / (y_max - y_min) for y in y_data]
                
                line.set_data(list(self.time_data)[-len(y_data):], y_data)
        
        # Update axis limits
        self.ax.relim()
        self.ax.autoscale_view()
        
        return list(self.lines.values())
    
    def start(self):
        """Start the live plot animation."""
        self.animation = animation.FuncAnimation(
            self.fig, 
            self.update_data, 
            interval=self.update_interval,
            blit=True,
            cache_frame_data=False
        )
        plt.show()
    
    def stop(self):
        """Stop the animation."""
        if self.animation:
            self.animation.event_source.stop()


# Example usage functions
def example_live_plot_basic():
    """Example: Basic live plot with simulated data."""
    # Create simulator
    simulator = BiogasSensorSimulator()
    threaded_sim = ThreadedSensorSimulator(simulator)
    
    # Start data generation
    threaded_sim.start(interval=0.5)
    
    # Create live plotter
    plotter = LivePlotter(data_source=threaded_sim, max_points=100, update_interval=500)
    
    # Setup plot for key variables
    plotter.setup_plot(
        variables=['temp', 'flow', 'pressure', 'ch4_concentration'],
        title='Live Biogas Sensor Data'
    )
    
    try:
        # Start live plotting
        plotter.start()
    finally:
        # Clean up
        threaded_sim.stop()


def example_live_plot_normalized():
    """Example: Normalized multi-variable plot."""
    # Create simulator
    simulator = BiogasSensorSimulator()
    threaded_sim = ThreadedSensorSimulator(simulator)
    
    # Start data generation
    threaded_sim.start(interval=0.5)
    
    # Create multi-variable plotter
    plotter = MultiVariableLivePlot(data_source=threaded_sim, max_points=200, update_interval=500)
    
    # Setup normalized plot
    plotter.setup_plot(
        variables=['temp', 'flow', 'pressure', 'comp'],
        title='Normalized Sensor Values',
        normalize=True
    )
    
    try:
        # Start live plotting
        plotter.start()
    finally:
        # Clean up
        threaded_sim.stop()


def create_custom_live_plot(data_function: Callable, 
                           variables: List[str],
                           title: str = "Live Data",
                           update_interval: int = 1000) -> LivePlotter:
    """
    Create a live plot with custom data source.
    
    Parameters:
    -----------
    data_function : callable
        Function that returns dict with sensor values
    variables : list of str
        Variables to plot
    title : str
        Plot title
    update_interval : int
        Update interval in milliseconds
    
    Returns:
    --------
    LivePlotter instance
    """
    plotter = LivePlotter(
        data_source=data_function,
        max_points=100,
        update_interval=update_interval
    )
    
    plotter.setup_plot(variables=variables, title=title)
    
    return plotter