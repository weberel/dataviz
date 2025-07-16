import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Union, List, Optional, Any

# Optional seaborn import
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


def quick_plot(
    data: Union[pd.DataFrame, np.ndarray, List, dict],
    x: Optional[Union[str, np.ndarray, List]] = None,
    y: Optional[Union[str, List[str], np.ndarray, List[np.ndarray]]] = None,
    color: Optional[Union[str, np.ndarray, List]] = None,
    title: Optional[str] = None,
    figsize: Optional[tuple] = None,
    **kwargs
) -> plt.Figure:
    """
    Quick plotting function that automatically determines subplot layout.
    
    Parameters:
    -----------
    data : pandas DataFrame, numpy array, list, or dict
        Data to plot
    x : str, array, or list (optional)
        X-axis data or column name
    y : str, list of str, array, or list of arrays (optional)
        Y-axis data or column names
    color : str, array, or list (optional)
        Data for color mapping with colorbar
    title : str (optional)
        Figure title
    figsize : tuple (optional)
        Figure size (width, height)
    **kwargs : additional matplotlib plot arguments
    
    Returns:
    --------
    matplotlib.figure.Figure
    """
    
    # Convert data to DataFrame if needed
    if isinstance(data, dict):
        data = pd.DataFrame(data)
    elif isinstance(data, (list, np.ndarray)):
        if x is None and y is None:
            # Assume 1D or 2D array
            data = np.array(data)
            if data.ndim == 1:
                x = np.arange(len(data))
                y = data
            else:
                # Multiple series
                x = np.arange(data.shape[1])
                y = [data[i, :] for i in range(data.shape[0])]
    
    # Handle DataFrame input
    if isinstance(data, pd.DataFrame):
        if x is None and y is None:
            # Plot all numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) > 0:
                x = data.index
                y = numeric_cols
        elif x is not None and isinstance(x, str):
            x = data[x]
        
        if isinstance(y, str):
            y = [y]
        
        if isinstance(y, list) and all(isinstance(col, str) for col in y):
            y_data = [data[col].values for col in y]
            y_labels = y
        else:
            y_data = y
            y_labels = None
    else:
        y_data = y if isinstance(y, list) else [y]
        y_labels = None
    
    # Determine number of subplots
    n_plots = len(y_data) if isinstance(y_data, list) else 1
    
    # Calculate subplot layout
    if n_plots <= 1:
        rows, cols = 1, 1
    elif n_plots <= 2:
        rows, cols = 1, 2
    elif n_plots <= 4:
        rows, cols = 2, 2
    elif n_plots <= 6:
        rows, cols = 2, 3
    elif n_plots <= 9:
        rows, cols = 3, 3
    else:
        cols = 4
        rows = (n_plots + cols - 1) // cols
    
    # Set figure size if not provided
    if figsize is None:
        figsize = (5 * cols, 4 * rows)
    
    # Create figure and subplots
    fig, axes = plt.subplots(rows, cols, figsize=figsize, squeeze=False)
    axes = axes.flatten()
    
    # Hide extra subplots
    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)
    
    # Filter out figure-level kwargs
    plot_kwargs = {k: v for k, v in kwargs.items() if k not in ['title', 'figsize']}
    
    # Plot data
    for i in range(n_plots):
        ax = axes[i]
        y_curr = y_data[i] if isinstance(y_data, list) else y_data
        
        # Handle color mapping
        if color is not None:
            if isinstance(color, str) and isinstance(data, pd.DataFrame):
                color_data = data[color]
            else:
                color_data = color
            
            scatter = ax.scatter(x, y_curr, c=color_data, cmap='viridis', **plot_kwargs)
            if i == n_plots - 1:  # Add colorbar to last subplot
                cbar = plt.colorbar(scatter, ax=ax)
                if isinstance(color, str):
                    cbar.set_label(color)
        else:
            ax.plot(x, y_curr, **plot_kwargs)
        
        # Set labels
        if y_labels and i < len(y_labels):
            ax.set_ylabel(y_labels[i])
        ax.set_xlabel('Index' if x is None else (x.name if hasattr(x, 'name') else 'X'))
        
        if n_plots > 1 and y_labels:
            ax.set_title(y_labels[i])
    
    if title:
        fig.suptitle(title)
    
    plt.tight_layout()
    return fig


def plot_dataframe(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    x_column: Optional[str] = None,
    color_column: Optional[str] = None,
    plot_type: str = 'line',
    **kwargs
) -> plt.Figure:
    """
    Plot columns from a pandas DataFrame with automatic subplot layout.
    
    Parameters:
    -----------
    df : pandas DataFrame
        Input data
    columns : list of str (optional)
        Columns to plot. If None, plots all numeric columns
    x_column : str (optional)
        Column to use for x-axis. If None, uses index
    color_column : str (optional)
        Column to use for color mapping
    plot_type : str
        Type of plot ('line', 'scatter', 'bar', 'hist')
    **kwargs : additional plot arguments
    
    Returns:
    --------
    matplotlib.figure.Figure
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if x_column in columns:
            columns.remove(x_column)
        if color_column in columns:
            columns.remove(color_column)
    
    x_data = df[x_column] if x_column else df.index
    
    # Determine subplot layout
    n_plots = len(columns)
    if n_plots <= 1:
        rows, cols = 1, 1
    elif n_plots <= 2:
        rows, cols = 1, 2
    elif n_plots <= 4:
        rows, cols = 2, 2
    elif n_plots <= 6:
        rows, cols = 2, 3
    else:
        cols = 3
        rows = (n_plots + cols - 1) // cols
    
    figsize = kwargs.pop('figsize', (5 * cols, 4 * rows))
    fig, axes = plt.subplots(rows, cols, figsize=figsize, squeeze=False)
    axes = axes.flatten()
    
    # Hide extra subplots
    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)
    
    # Filter out figure-level kwargs
    plot_kwargs = {k: v for k, v in kwargs.items() if k not in ['title', 'figsize']}
    
    # Plot each column
    for i, col in enumerate(columns):
        ax = axes[i]
        
        if plot_type == 'line':
            if color_column:
                # Group by color column and plot each group
                for name, group in df.groupby(color_column):
                    ax.plot(x_data[group.index], group[col], label=f"{color_column}={name}", **plot_kwargs)
                ax.legend()
            else:
                ax.plot(x_data, df[col], **plot_kwargs)
        elif plot_type == 'scatter':
            if color_column:
                scatter = ax.scatter(x_data, df[col], c=df[color_column], cmap='viridis', **plot_kwargs)
                if i == n_plots - 1:
                    plt.colorbar(scatter, ax=ax, label=color_column)
            else:
                ax.scatter(x_data, df[col], **plot_kwargs)
        elif plot_type == 'bar':
            ax.bar(x_data, df[col], **plot_kwargs)
        elif plot_type == 'hist':
            ax.hist(df[col], **plot_kwargs)
        
        ax.set_xlabel(x_column if x_column else 'Index')
        ax.set_ylabel(col)
        ax.set_title(col)
    
    plt.tight_layout()
    return fig


def plot_sensor_data(
    csv_file: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
    sensor_columns: Optional[List[str]] = None,
    time_column: str = 'datetime',
    **kwargs
) -> plt.Figure:
    """
    Plot biogas sensor data with appropriate layout.
    
    Parameters:
    -----------
    csv_file : str (optional)
        Path to CSV file with sensor data
    df : pandas DataFrame (optional)
        Sensor data DataFrame (if csv_file not provided)
    sensor_columns : list of str (optional)
        Specific sensor columns to plot
    time_column : str
        Name of time/datetime column
    **kwargs : additional plot arguments
    
    Returns:
    --------
    matplotlib.figure.Figure
    """
    if csv_file:
        df = pd.read_csv(csv_file)
        if time_column in df.columns:
            df[time_column] = pd.to_datetime(df[time_column])
            df.set_index(time_column, inplace=True)
    
    if df is None:
        raise ValueError("Either csv_file or df must be provided")
    
    # Default sensor columns if not specified
    if sensor_columns is None:
        sensor_columns = ['temp_degC', 'humidity_perc_rH', 'flow', 'concentration_ch4', 
                         'd0_temp_flow', 'd0_power_flow', 'd1_temp_flow', 'd1_power_flow']
        # Filter to existing columns
        sensor_columns = [col for col in sensor_columns if col in df.columns]
    
    return plot_dataframe(df, columns=sensor_columns, **kwargs)