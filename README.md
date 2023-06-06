# CESM LENS2 Bokeh Dashboard

This Python repository includes a Bokeh dashboard to visualize data from the Community Earth System Model Large Ensemble (CESM LENS2) dataset, focusing on the Willamette Valley region.

The dashboard allows interactive exploration of the dataset, including options to select specific variables, ensembles, and frequencies. It includes two plots: a time series plot and a scatter plot.

## Requirements

To run this dashboard, you'll need Python 3.7 or higher, along with the following libraries:
****

You can install these libraries using `conda`:
***

## Getting Started

1. Clone the repository:
```
git clone https://github.com/negin513/climate-viewer.git
```
2. Navigate to the project directory:
```
cd climate-viewer
```
3. Run the Bokeh server:
```
bokeh serve --show climate-viewer/
```
This command will start the Bokeh server and open the dashboard in your default web browser.

## Using the Dashboard

Once the dashboard is running, you can use the dropdown menus at the top of the page to select the variable, ensemble, and frequency that you wish to visualize.

The left panel will display a time series plot of the selected variable, and the right panel will display a scatter plot of the selected variable.

You can select a range on the time series plot to highlight the corresponding data points on the scatter plot.
