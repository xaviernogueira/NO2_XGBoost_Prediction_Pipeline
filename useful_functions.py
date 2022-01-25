"""
Quick and useful functions for supporting the NO2 prediction pipeline

author @xaviernogueira
"""
import pandas as pd
import logging
import matplotlib.pyplot as plt
import os


def init_logger(filename, log_name=None):
    """Initializes logger w/ same name as python file or a specified name if log_name is given a valid path (.log)"""

    if log_name is not None and log_name[-4:] == '.log':
        if os.path.exists(os.path.dirname(log_name)):
            name = log_name
        else:
            return print('ERROR: Logger cannot be initiated @ %s' % log_name)
    else:
        name = os.path.basename(filename).replace('.py', '.log')

    logging.basicConfig(filename=name, filemode='w', level=logging.INFO)
    stderr_logger = logging.StreamHandler()
    stderr_logger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logging.getLogger().addHandler(stderr_logger)

    return


def make_test_csv(csv, rows=500):
    """
    Takes a csv and randomly samples N number of rows to make a ML test csv (faster computation)
    :param csv: a csv
    :param rows: number of rows for test csv (int, default is 500)
    :return: new test csv
    """

    in_df = pd.read_csv(csv)
    shuffled = in_df.sample(frac=1).reset_index()

    if isinstance(rows, int):
        out_df = shuffled.sample(n=rows)

    else:
        return print('ERROR: Rows parameter must be an integer')

    out_dir = os.path.dirname(csv)
    out_csv = out_dir + '\\%s' % os.path.basename(csv).replace('.csv', '_test_%s_rows.csv' % rows)

    out_df.to_csv(out_csv)
    return out_csv


def bbox_poly(bbox, region, out_folder):
    import geopandas as gpd
    from shapely.geometry import Polygon

    # define output location
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    out_shp = out_folder + '\\%s_bbox.shp' % region

    # get bounding box coordinates and format
    long0, long1, lat0, lat1 = bbox
    logging.info('Prediction extent coordinates: %s' % bbox)

    poly = Polygon([[long0, lat0],
                    [long1, lat0],
                    [long1, lat1],
                    [long0, lat1]])

    # save as a shapefile and return it's path
    gpd.GeoDataFrame(pd.DataFrame(['p1'], columns=['geom']),
                     crs={'init': 'epsg:4326'},
                     geometry=[poly]).to_file(out_shp)
    return out_shp