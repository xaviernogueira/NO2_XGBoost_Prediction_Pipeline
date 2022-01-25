import logging
import os
import arcpy
import numpy as np
import pandas as pd
from useful_functions import init_logger


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
    # initialize logger, environment, and delete files list
    init_logger(__file__)
    arcpy.env.overwriteOutput = True
    del_files = []

    # create list of valid input files
    all_files = os.listdir(in_folder)
    in_files = [in_folder + '\\%s' % i for i in all_files if str_in in i]
    in_files = [i for i in in_files if i[-4:] == '.tif']
    if len(in_files) == 0:
        return print('ERROR. No valid input .tif files w/ %s in their name. Please run again.' % str_in)

    # find raster units, give user a chance to change cell_size input before processing
    in_spatial_ref = arcpy.Describe(in_files[0]).spatialReference
    in_cell_size = float(arcpy.GetRasterProperties_management(in_files[0], 'CELLSIZEX').getOutput(0))
    units = [in_spatial_ref.linearUnitName, in_spatial_ref.angularUnitName]
    unit = [i for i in units if i != ''][0]

    print('Units are in %s! Input cell size is %s' % (unit, in_cell_size))
    print('Output cell size will be %s %s' % (cell_size, unit))
    var = input('Is this correct? Y or N:')

    if var is not 'Y':
        return print('Adjust cell_size parameter and run again.')

    # if out_folder does not exist or is not specified, make new folder
    if out_folder == '':
        out_folder = in_folder + '\\resampled_%s%s' % (cell_size, unit)

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    # select raster files to process and resample or aggregate then resample
    for i, file in enumerate(in_files):
        name = os.path.split(file)[1]
        try:
            if not agg:
                # create output path then resample
                out_file = out_folder + '\\%s' % name

                arcpy.Resample_management(file, out_file, cell_size, 'BILINEAR')
                logging.info('Resampled %s' % name)

            # if agg == True, either aggregate to the output cell size (if divisible) or aggregate and then resample
            elif agg:
                # create text file to record which of the newly named rasters correspond to what
                txt_dir = out_folder + '\\aggregate_key.txt'
                out_txt = open(txt_dir, 'w+')
                out_file = out_folder + '\\agg%s.tif' % i

                factor = int(cell_size // in_cell_size)
                if cell_size % in_cell_size == 0:
                    in_ras = arcpy.sa.Raster(file)
                    out_ras = arcpy.sa.Aggregate(in_ras, factor, 'Sum')
                else:
                    temp = out_folder + '\\temp%s.tif' % i
                    in_ras = arcpy.sa.Raster(file)
                    out_agg = arcpy.sa.Aggregate(in_ras, factor, 'Sum')
                    out_agg.save(temp)
                    del_files.append(temp)
                    out_ras = arcpy.sa.Resample(out_agg, 'Average', output_cellsize=cell_size)

                # Save the output
                out_txt.write('\n %s -> %s\n' % (name, out_file))
                out_ras.save(out_file)
                logging.info('Aggregated %s' % name)
                out_txt.close()

        except arcpy.ExecuteError:
            logging.info(str(arcpy.GetMessages()))
            logging.info('ERROR, skipped %s' % name)

    # delete extra files
    for file in del_files:
        try:
            arcpy.Delete_management(file)
        except arcpy.ExecuteError:
            logging.info('Could not delete %s' % file)

    return out_folder


def batch_raster_project(in_folder, spatial_ref, out_folder='', suffix='_p.tif'):
    """
    This function batch projects rasters and places them in a new flder
    :param in_folder: folder containing .tif rasters
    :param out_folder: folder to save output rasters
    :param spatial_ref: a spatial reference file or a raster/shapefile with the desired spatial reference
    :param suffix: suffix to add to output rasters (_p is default i.e., btw.tif -> btw_p.tif)
    :return: the out_folder
    """
    # initialize logger, environment, and delete files list
    init_logger(__file__)
    arcpy.env.overwriteOutput = True
    del_files = []

    # create list of valid input files
    all_files = os.listdir(in_folder)
    in_names = [i for i in all_files if i[-4:] == '.tif']
    in_files = [in_folder + '\\%s' % i for i in in_names]
    if len(in_files) == 0:
        return print('ERROR. No valid input .tif files in %s. Please run again.' % in_folder)

    # create output spatial reference object
    if isinstance(spatial_ref, str):
        ext = spatial_ref[-4:]
        if ext == '.tif' or ext == '.shp':
            out_sr = arcpy.Describe(spatial_ref).spatialReference
        else:
            out_sr = spatial_ref

    else:
        return print('spatial_ref must be a .tif, .shp, or a arcpy spatial reference object')

    # if out_folder does not exist or is not specified, make new folder
    if out_folder == '':
        out_folder = in_folder + '\\projected'

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    # project and save rasters
    for i, file in enumerate(in_files):
        name = in_names[i]
        out_ras = out_folder + '\\%s' % name.replace('.tif', suffix)

        try:
            arcpy.ProjectRaster_management(file, out_ras, out_coor_system=out_sr, resampling_type='BILINEAR')
            logging.info('Projected %s -> %s' % (name, out_ras))

        except arcpy.ExecuteError:
            logging.info(str(arcpy.GetMessages()))
            logging.info('ERROR, skipped %s' % file)

    return out_folder


def simple_raster_sample(in_table, sample_points, var_dict):
    """
    Plain bagel raster sampling (w/o month or days)
    :param in_table: A table with daily NO2 observations
    :param sample_points: AQ station sample points with a station_id field
    :param var_dict: a dictionary with variable names as keys and associated rasters as items
    :return: a new csv
    """

    # initialize logger and format directories
    init_logger(__file__)
    logging.info('Running plain bagel (no months/days) raster sampling.')
    out_dir = os.path.dirname(sample_points)
    arcpy.env.overwriteOutput = True
    out_csv = in_table.replace('.csv', '_export.csv')
    temp_files = out_dir + '\\temp_files'
    if not os.path.exists(temp_files):
        os.makedirs(temp_files)

    # set variables names
    var_names = list(var_dict.keys())

    in_df = pd.read_csv(in_table)
    in_df.sort_values('station_id', inplace=True)
    out_df = in_df.copy()
    samp_dfs = []

    for var in var_names:
        ras = var_dict[var]
        ras_name = os.path.basename(ras)[:-4]
        logging.info('Pulling station point %s values...' % var)
        t_dbf = temp_files + '\\%s_sample.dbf' % var
        t_csv = t_dbf.replace('.dbf', '.csv')

        # make a sample dataframe with a _Band_# header suffixes where # is the month index
        sample_table = arcpy.sa.Sample(ras, sample_points, t_dbf, unique_id_field='station_id')

        if os.path.exists(t_csv):
            os.remove(t_csv)

        arcpy.TableToTable_conversion(sample_table, os.path.dirname(t_csv), os.path.basename(t_csv))

        samp_df = pd.read_csv(t_csv)
        samp_df.rename(columns={ras_name: var, 'no2_annual': 'station_id'}, inplace=True)
        samp_dfs.append(samp_df)

    # join to the daily observation csv
    for i, df in enumerate(samp_dfs):
        var = var_names[i]
        out_df = out_df.merge(df, on=['station_id'], how='left')
        out_df[var] = out_df[var].fillna(0)

    out_df.to_csv(out_csv)
    logging.info('Done\nOutput csv with variables %s @ %s' % (var_names, out_csv))

    return out_csv