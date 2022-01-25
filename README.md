# NO2_XGBoost_Prediction_Pipeline
A library facilitating the creation of XGBoost powered NO2 (monthly or daily) ground concentration prediction maps.

# Dependencies
Training, tuning, and testing the XGBoost model can be done without the use of ArcGIS's arcpy Python library. However, prediction maps are (currently) generated using arcpy funtionality.

```python
# import core dependencies
import os
import matplotlib.pyplot 
import seaborn 
import pandas 
import numpy 
import xgboost 
import sklearn
import joblib
import logging

# for predictions and data pulling
import arcpy
```

# Prediction pipeline overview
1. Create or obtain a csv with NO2 monitoring stations observations at a given timeframe (daily, monthly, etc.). NO2 concentrations must be stored in a 'mean_no2' column. Monitoring stations must be associated with lat/long values if the use of Kriging (coming in update) is desired. Other columns include spatially and temporally associated independent variable values. These values can be pulled using functions provided in the 'data_pulling_functions.py' file.

| station_id | lat  | long  | mean_no2 | indie_var1  | indie_var2  |
| ------------- |:-------------:| -----:| -----:| -----:| -----:|
| 1 | 33.553056 | -86.815 | 11.176 | 0.3678 | 2.667 | 

2. Train and tune a XGBoost regression model. Using the inputs section at the bottom of train_and_test.py and running the file will automate this process.
3. Assess your model's performance by looking the model test, feature importance, and hyper-parameter sensitivity plots stored in the generated ModelRun# folder. Use your assesment to update the input independent variables list and hyper-parameter ranges, and re-run until desirable performance is obtained. 
4. Use the make_prediction_map.py file to generate urban NO2 prediction maps at a chosen area of interest, spatial resolution, and temporal resolution. 


# Function descriptions 
Desripctions of useful standalone functions that are NOT attached to to automated pipelines.

## *arcpy_functions.py*

```python
def batch_resample_or_aggregate(in_folder, cell_size, out_folder='', str_in='.tif', agg=False):
    """
    This function resamples or aggregates every raster in a folder, and saves the new raster in a new folder
    :param in_folder: Folder containing raster datasets
    :param cell_size: The cell size (float or int) in the same units of the raster
    :param out_folder: Output folder, if not specified, a folder 'resampled_{DIST} will be made in in_folder'
    :param str_in: (.tif is default) A string within the raster file name to select for resampling
    :param agg: Bool. If true, a SUM aggregation is used (for data like population) instead of bilinear resampling
    :return: The new folder location containing resampled raster datasets
    """
    
def batch_raster_project(in_folder, spatial_ref, out_folder='', suffix='_p.tif'):
    """
    This function batch projects rasters and places them in a new flder
    :param in_folder: folder containing .tif rasters
    :param out_folder: folder to save output rasters
    :param spatial_ref: a spatial reference file or a raster/shapefile with the desired spatial reference
    :param suffix: suffix to add to output rasters (_p is default i.e., btw.tif -> btw_p.tif)
    :return: the out_folder
    """
```
