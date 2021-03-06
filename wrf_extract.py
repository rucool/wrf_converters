#!/usr/bin/env python
# Script to extract RU-WRF Wind Speed Grids from old GRIB files
# Written by Sage, 6/13/18

from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import xarray as xr
import pygrib
import argparse

#------------------------------
# Specify WRF Model directory 
# directory = 'test_data/'
# directory = '/Volumes/BayBreeze/output/grib/3km/' #Local
directory = '/home/bowers/output/grib/3km/' #Server

# Specify forecast offset to use
forecast_offset = 6 # Must be 0-23 to work

#------------------------------
def make_wrf_file(dtime,fo=0):
  '''Create a WRF GRIB filename'''
  t2 = dtime.replace() #Copy variable to mess with
  if t2.hour < fo:
    t2 = t2-timedelta(1) # Previous Day
    hour = t2.hour + 24
  else: 
    hour = t2.hour
  if t2.year == 2016 and t2 >= datetime(2016,6,7):
    dir_name = '2016_new' #Hack to handle split 2016
  else:
    dir_name = str(t2.year)
  return '%s/RUWRF_3km_%d%02d%02d00_%02d:00.grb2' % (dir_name,t2.year,t2.month,t2.day,hour)


#------------------------------
def main():
  """Main function for command line execution"""
  script_start_time = datetime.now() #Script Timer

  if len(args.date)!=8:
    raise ValueError('Please enter a date in the format yyyymmdd') 

  # Specify Date Range to Process
  year  = int(args.date[0:4])
  month = int(args.date[4:6])
  day   = int(args.date[6:8])
  start_date = datetime(year,month,day)
  end_date = start_date + timedelta(args.days) - timedelta(0,60*60)
  
  times = pd.date_range(start_date, end_date, freq="H")
  power_curve = pd.read_csv('wrf_lw8mw_power.csv')

  #------------------------------
  # Step 1 - Loop over each hour
  for t in times:

    # Step 2 - Open WRF file
    try:
      wrf_file = make_wrf_file(t, forecast_offset)
      grbfile = pygrib.open(directory + wrf_file)
      
      print('Processing: ' + str(t) + ' File: ' + wrf_file)

      data_u120,lats,lons = grbfile.select(name="U component of wind")[10].data() # 120m
      data_v120,lats,lons = grbfile.select(name="V component of wind")[10].data()
      grbfile.close()
      
      uVel = np.ma.expand_dims(data_u120,axis=2)
      vVel = np.ma.expand_dims(data_v120,axis=2)
      uVel.fill_value = np.nan
      vVel.fill_value = np.nan
      wind_speed = np.sqrt(uVel**2+vVel**2)
      wind_dir = 270 - xr.ufuncs.arctan2(vVel,uVel)*180/np.pi
      wind_dir = wind_dir % 360  #Use modulo to keep degrees between 0-360
      wind_power = np.interp(wind_speed,power_curve['Wind Speed'],power_curve['Power']) #right=np.nan

      ds = xr.Dataset({
#         'uVel': (['x', 'y', 'time'],  uVel),
#         'vVel': (['x', 'y', 'time'],  vVel),
        'wind_speed': (['x', 'y', 'time'],  wind_speed),
#         'wind_dir': (['x', 'y', 'time'], wind_dir),
        'wind_power': (['x', 'y', 'time'], wind_power)},
        coords={'lon': (['x', 'y'], lons), 'lat': (['x', 'y'], lats), 'time': [t] })
      
      try:
        final_dataset = xr.merge([final_dataset, ds]) 
        
      except:
        final_dataset = ds.copy()
    
    except:
      print('Could not open ' + wrf_file)


  # Step 6 - Save the results
  # Add global metadata
  final_dataset.attrs['forecast_offset'] = forecast_offset
  final_dataset.attrs['source_directory'] = directory
  final_dataset.attrs['date_created'] = str(datetime.today())
  final_dataset.attrs['elapsed_time'] = str(datetime.now() - script_start_time)
  
  # Setup xarray output encoding
  encoding={}
  encoding['time'] = dict(units='days since 2010-01-01 00:00:00', calendar='gregorian', dtype=np.double)

  # Output final datafile
  output_datafile = '%s_%d%02d%02d_%d%02d%02d.nc' % ( 
    args.prefix, 
    start_date.year, start_date.month, start_date.day, 
    end_date.year, end_date.month, end_date.day)
  
  final_dataset.to_netcdf(output_datafile, encoding=encoding)
  
  print('Outputted ' + output_datafile)


# Run main function when in comand line mode        
if __name__ == '__main__':
  # Command Line Arguments
  parser = argparse.ArgumentParser(description='RU-WRF Extractor - GRIB version')
  parser.add_argument('date',
    help='Specify a date to process in yyyymmdd format')
  parser.add_argument('-d','--days', type=int,
    default=1,
    help='Number of days to process')
  parser.add_argument('-p','--prefix', type=str,
    default='wrf_data',
    help='Prefix for the output filename')
  args = parser.parse_args()
  main()
