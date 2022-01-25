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


def ncf_metadata(ncf_files):
    """
    Generates a formatted meta data text file for input .ncf file(s)
    :param ncf_files: a path (str) or a list of paths (list) to .ncf files
    :return a text file in the directory of the first .ncf file w/ all input file info
    """
    import netCDF4 as nc

    print('Input files: %s' % ncf_files)

    # define output dir for text file
    if isinstance(ncf_files, list):
        main_dir = os.path.dirname(ncf_files[0])
        in_list = ncf_files
    elif isinstance(ncf_files, str):
        main_dir = os.path.dirname(ncf_files)
        in_list = [ncf_files]
    elif isinstance():
        return print('ncf_file parameter is not a valid .ncf path of a list of paths')

    # create a new text file
    txt_dir = main_dir + '\\ncf_files_info.txt'
    out_txt = open(txt_dir, 'w+')
    out_txt.write('INPUT FILES METADATA\n----------------\n')

    # format text file with ncf file metadata
    for ncf in in_list:
        out_txt.write('FILE: ' + ncf + '\n')
        ds = nc.Dataset(ncf)
        ds_dict = ds.__dict__
        dims = ds.dimensions
        for key in ds_dict.keys():
            val = ds_dict[key]
            out_txt.write('%s: %s\n' % (key, val))

        # write the number of dimensions, their names, and sizes
        out_txt.write('\n# of dimensions: %s\n' % len(dims))
        for dim in ds.dimensions.values():
            dim_txt = str(dim)
            if 'name' in dim_txt:
                split = dim_txt.split(':')[1]
                out = split.replace('name', 'dimension')[1:]
                out_txt.write(out + '\n')

        # write all variable descriptions
        variables = ds.variables.values()
        out_txt.write('\n# of variables: %s' % len(variables))
        for var in variables:
            var_txt = str(var)
            out = var_txt.split('>')[1]
            out_txt.write('%s\n' % out)
        out_txt.write('\n-------------\n')
    out_txt.close()

    return print('METADATA text file @ %s' % txt_dir)


def get_boundingbox(place, output_as='boundingbox', state_override=False):
    """
    Get the bounding box of a country or US state in EPSG4326 given it's name
    based on work by @mattijin (https://github.com/mattijn)

    :param place: a name (str) of a country, city, or state in english and lowercase (i.e., beunos aires)
    :param output_as: - either boundingbox' or 'center' (str)
         * 'boundingbox' for [latmin, latmax, lonmin, lonmax]
         * 'center' for [latcenter, loncenter]
    :param integer: - default is False (bool), if True the output list is converted to integers
    :param state_override: default is False (bool), only make True if mapping a state
    :return a list with coordinates as floats i.e., [[11.777, 53.7253321, -70.2695876, 7.2274985]]
    """
    import requests
    import iso3166
    # create url to pull openstreetmap data
    url_prefix = 'http://nominatim.openstreetmap.org/search?country='

    country_list = [j.lower() for j in iso3166.countries_by_name.keys()]

    if place not in country_list:
        if state_override:
            url_prefix = url_prefix.replace('country=', 'state=')
        else:
            url_prefix = url_prefix.replace('country=', 'city=')

    url = '{0}{1}{2}'.format(url_prefix, place, '&format=json&polygon=0')
    response = requests.get(url).json()[0]

    # parse response to list, convert to integer if desired
    if output_as == 'boundingbox':
        lst = response[output_as]
        coors = [float(i) for i in lst]
        output = [coors[-2], coors[-1], coors[0], coors[1]]

    elif output_as == 'center':
        lst = [response.get(key) for key in ['lat', 'lon']]
        coors = [float(i) for i in lst]
        output = [coors[-1], coors[0]]

    else:
        print('ERROR: output_as parameter must set to either boundingbox or center (str)')
        return

    return output


def bbox_poly(bbox, region, out_folder):
    """
    Creates a shapefile from a list with bounding box coordinates.
    :param bbox: a list with [latmin, latmax, lonmin, lonmax] (returned from get_boundingbox())
    :param region: a string with a region name (i.e., 'Chicago')
    :param out_folder: a folder path in which to save the created shapefile
    :return: the shapefile path
    """
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