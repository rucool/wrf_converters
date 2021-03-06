#!/usr/bin/env python
# Script to extract RU-WRF Model Data from old GRIB files
# Written by Sage, 8/17/17
# Updated to extract quarterly report points 9/12/17
# Turned into a functional script 9/29/17
# Code improvements 3/2/18

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
def make_wrf_file(dtime,fo=0,pd=0):
  '''Create a WRF GRIB filename'''
  t2 = dtime.replace() # Copy variable to mess with
  if (pd):
    t2 = t2-timedelta(1) # Previous Day
  if t2.hour < fo:
    t2 = t2-timedelta(1) # Previous Day
    hour = t2.hour + 24
  else: 
    hour = t2.hour
  if (pd):
    hour = hour+24 # Later in model run
  if t2.year == 2016 and t2 >= datetime(2016,6,7):
    dir_name = '2016_new' # Hack to handle split 2016
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

  # Load Selected Station Locations
  sites = pd.read_csv(args.coordinates, skipinitialspace=True)
  
  #------------------------------
  # Setup default arrays
  heights = np.array([10,100,120,140], dtype='int32')
  stations = sites.name.astype('S')
  times = pd.date_range(start_date, end_date, freq="H")
  data = np.empty( shape=(len(times),len(stations),len(heights)) ) * np.NAN
  uVel = xr.DataArray(data, coords=[times, stations, heights], dims=['time','station','height'], attrs={
    'units':'m s-1',
    'standard_name':'eastward_wind',
    'long_name':'Wind Speed, Zonal',
    'comment':'The zonal wind speed (m/s) indicates the u (positive eastward) component of where the wind is going.',
  })
  
  uVel['time'].attrs['standard_name'] = 'time'
  uVel['time'].attrs['long_name'] = 'Time'
  
  uVel['station'].attrs['standard_name'] = 'station_id'
  uVel['station'].attrs['long_name'] = 'Station ID'
  uVel['station'].attrs['comment'] = 'A string specifying a unique station ID, created to allow easy referencing of the selected grid points extracted from the WRF model files.'

  uVel['height'].attrs['units'] = 'm'
  uVel['height'].attrs['standard_name'] = 'height'
  uVel['height'].attrs['long_name'] = 'Height'

  vVel = uVel.copy()
  vVel.attrs['standard_name'] = 'northward_wind'
  vVel.attrs['long_name'] = 'Wind Speed, Meridional'
  vVel.attrs['comment'] = 'The meridional wind speed (m/s) indicates the v (positive northward) component of where the wind is going.'
  
  latitude = xr.DataArray(sites['latitude'], coords=[stations], dims=['station'], attrs={
    'units':'degrees_north',
    'comment':'The latitude of the station.',
    'long_name':'Latitude',
    'standard_name':'latitude'
  })
  longitude = xr.DataArray(sites['longitude'], coords=[stations], dims=['station'], attrs={
    'units':'degrees_east',
    'comment':'The longitude of the station.',
    'long_name':'Longitude',
    'standard_name':'longitude'
  })
  
  #------------------------------
  # Step 1 - Loop over each hour
  for t in times:

    # Step 2 - Open WRF file
    try:
      try: # Try ideal file
        wrf_file = make_wrf_file(t, forecast_offset)
        grbfile = pygrib.open(directory + wrf_file)
      except: 
        try: # Try previous day
          wrf_file = make_wrf_file(t,forecast_offset, 1)
          grbfile = pygrib.open(directory + wrf_file)
        except: # Try current day
          wrf_file = make_wrf_file(t, 0, 0)
          grbfile = pygrib.open(directory + wrf_file)
      
      print('Processing: ' + str(t) + ' File: ' + wrf_file)
      data_u10,lats,lons = grbfile.select(name="10 metre U wind component")[0].data()
      data_v10,lats,lons = grbfile.select(name="10 metre V wind component")[0].data()
      data_u100,lats,lons = grbfile.select(name="U component of wind")[8].data() # 100m
      data_v100,lats,lons = grbfile.select(name="V component of wind")[8].data()
      data_u120,lats,lons = grbfile.select(name="U component of wind")[10].data() # 120m
      data_v120,lats,lons = grbfile.select(name="V component of wind")[10].data()
      data_u140,lats,lons = grbfile.select(name="U component of wind")[12].data() # 140m
      data_v140,lats,lons = grbfile.select(name="V component of wind")[12].data()
      
      # Step 3 - Loop over each station
      for index, site in sites.iterrows():
        # Step 4 - Find the closest model point
        a = abs(lats-site.latitude)+abs(lons-site.longitude)
        i,j = np.unravel_index(a.argmin(),a.shape)
        # Step 5 - Extract data for each variable
        uVel.loc[{'time':t,'station':stations[index],'height':10}] = data_u10[i][j]
        vVel.loc[{'time':t,'station':stations[index],'height':10}] = data_v10[i][j]
        uVel.loc[{'time':t,'station':stations[index],'height':100}] = data_u100[i][j]
        vVel.loc[{'time':t,'station':stations[index],'height':100}] = data_v100[i][j]
        uVel.loc[{'time':t,'station':stations[index],'height':120}] = data_u120[i][j]
        vVel.loc[{'time':t,'station':stations[index],'height':120}] = data_v120[i][j]
        uVel.loc[{'time':t,'station':stations[index],'height':140}] = data_u140[i][j]
        vVel.loc[{'time':t,'station':stations[index],'height':140}] = data_v140[i][j]
        
      grbfile.close()
      
    except:
      print('Could not open ' + wrf_file)

  # Step 5.5 - Calculated additional variables
  
  # Wind Speed
  wind_speed = np.sqrt(uVel**2+vVel**2)
  wind_speed.attrs['units'] = 'm s-1'
  wind_speed.attrs['comment'] = 'Wind Speed is calculated from the Zonal and Meridional wind speeds.'
  wind_speed.attrs['long_name'] = 'Wind Speed'
  wind_speed.attrs['standard_name'] = 'wind_speed'
  
  # Wind Direction
  wind_dir = 270 - xr.ufuncs.arctan2(vVel,uVel)*180/np.pi
  #wind_dir = (wind_dir.where(wind_dir<0)+360).combine_first(wind_dir) #Flip negative degrees - Doesn't seem to work
  wind_dir = wind_dir % 360  #Use modulo to keep degrees between 0-360
  wind_dir.attrs['units'] = 'degree'
  wind_dir.attrs['comment'] = 'The direction from which winds are coming from, in degrees clockwise from true N.'
  wind_dir.attrs['long_name'] = 'Wind Direction'
  wind_dir.attrs['standard_name'] = 'wind_from_direction'

  # Estimated Power Output
  power_curve = pd.read_csv('wrf_lw8mw_power.csv')
  wind_power = np.interp(wind_speed,power_curve['Wind Speed'],power_curve['Power'])
  wind_power = xr.DataArray(wind_power,coords=[times, stations, heights], dims=['time','station','height'])
  wind_power.attrs['units'] = 'kW'
  wind_power.attrs['comment'] = 'Estimated Wind Power is interpolated from wind speed, using an 8 MW reference turbine power curve from Desmond (2016).'
  wind_power.attrs['long_name'] = 'Estimated 8MW Wind Power'
  wind_power.attrs['standard_name'] = 'wind_power'

  # Step 6 - Save the results
  final_dataset = xr.Dataset({
    'u_velocity':uVel, 'v_velocity':vVel,
    'wind_speed':wind_speed, 'wind_dir':wind_dir, 
    'wind_power':wind_power,
    'latitude':latitude, 'longitude':longitude
  })
  
  # Add global metadata
  final_dataset.attrs['forecast_offset'] = forecast_offset
  final_dataset.attrs['source_directory'] = directory
  final_dataset.attrs['date_created'] = str(datetime.today())
  final_dataset.attrs['elapsed_time'] = str(datetime.now() - script_start_time)

  final_dataset.attrs['acknowledgement'] = "Rutgers University Center for Ocean Observing Leadership (RU COOL)";
  final_dataset.attrs['creator_name'] = "Rutgers University Center for Ocean Observing Leadership (RU COOL)";
  final_dataset.attrs['creator_url'] = "https://rucool.marine.rutgers.edu";
  final_dataset.attrs['creator_email'] = "sage@marine.rutgers.edu";
  final_dataset.attrs['summary'] = "Wind data extracted from GRIB files produced by Rutgers University's 3km WRF model run.  The model is run daily at 00Z and forecast files are saved every hour.  Times in this file are UTC based on the forecast run times.  The forecast_offset specifies how many hours of model spin up are allowed before the data is used.  For example, a value of 6 means the first 6 hours of data for any day are actually extracted from the previous day's model run."
  final_dataset.attrs['project'] = "RU COOL BPU Wind Energy Project";
  final_dataset.attrs['title'] = "Rutgers WRF 3km Model output at selected stations";
  final_dataset.attrs['Conventions'] = 'CF-1.6'
  
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
  parser.add_argument('-c','--coordinates', type=argparse.FileType('r'),
    default='wrf_vmt_points.csv',
    help='A file with coordinate points to extract')
  parser.add_argument('-p','--prefix', type=str,
    default='wrf_data',
    help='Prefix for the output filename')
  args = parser.parse_args()
  main()
