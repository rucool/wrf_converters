#!/usr/bin/env python
# Script to extract entire RU-WRF Model Data layers from old GRIB files
# Written by Sage, 10/25/18

from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import xarray as xr
import argparse

#------------------------------
# Specify WRF Model directory 
directory = '/home/bowers/output/grib/3km/'

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


def clean_dataset(ds):
  '''Clean the GRIB dataset'''
  nds = xr.Dataset()
  nds['eastward_wind'] = ds.UGRD_P0_L103_GLC0
  nds['northward_wind'] = ds.VGRD_P0_L103_GLC0
  nds.rename({'lv_HTGL1':'z','xgrid_0':'x','ygrid_0':'y','gridlat_0':'lat','gridlon_0':'lon'},inplace=True)
  #nds['wind_speed'] = np.sqrt(nds.eastward_wind**2 + nds.northward_wind**2)
  nds.expand_dims('time')
  t1 = pd.to_datetime(nds['eastward_wind'].initial_time,format='%m/%d/%Y (%H:%M)')
  t2 = pd.to_timedelta(nds['eastward_wind'].forecast_time[0], unit='h')
  nds['time'] = t1+t2
  nds.set_coords('time',inplace=True)
  return nds.sel(z=[10,100,120,140]) #Save selected layers


def make_encoding(ds, time_start='days since 2010-01-01 00:00:00', comp_level=5, fillvalue=-999.00):
  '''Create variable encodings for saving to netcdf'''
  encoding = {}
  for k in ds.data_vars:
    encoding[k] = {'zlib': True, 'complevel': comp_level} #'_FillValue': np.float32(fillvalue)
  encoding['time'] = dict(units=time_start, calendar='gregorian', zlib=False, _FillValue=False, dtype=np.double)
  return encoding


#------------------------------
def main(adate,aprefix):
  """Main function for command line execution"""
  script_start_time = datetime.now() #Script Timer

  if len(adate)!=8:
    raise ValueError('Please enter a date in the format yyyymmdd') 

  # Specify Date to Process
  year  = int(adate[0:4])
  month = int(adate[4:6])
  day   = int(adate[6:8])
  start_date = datetime(year,month,day)

  # Loop through 24 hours
  dsout = False
  for jj in range(0,24):
    wrf_file = make_wrf_file(start_date + pd.to_timedelta(jj,unit='h'), forecast_offset)
    print('Processing: ' + wrf_file)
    ds = False
    try:
      ds = xr.open_dataset(directory + wrf_file, engine='pynio')
    except:
      print('Could not open ' + wrf_file)
    if(isinstance(ds,xr.Dataset)):
      ds = clean_dataset(ds)
      if(isinstance(dsout,xr.Dataset)):
        dsout = xr.concat([dsout, ds],dim='time')
      else:
        dsout = ds

  if(isinstance(dsout,xr.Dataset)):
    # Add attributes
    dsout['eastward_wind'].attrs['standard_name'] = 'eastward_wind'
    dsout['eastward_wind'].attrs['comment'] = 'The zonal wind speed (m/s) indicates the u (positive eastward) component of where the wind is going.'
    dsout['northward_wind'].attrs['standard_name'] = 'northward_wind'
    dsout['northward_wind'].attrs['comment'] = 'The meridional wind speed (m/s) indicates the v (positive northward) component of where the wind is going.'
  
    # Add Wind Speed
    wind_speed = np.sqrt(dsout['eastward_wind']**2 + dsout['northward_wind']**2)
    wind_speed.attrs['units'] = 'm s-1'
    wind_speed.attrs['comment'] = 'Wind Speed is calculated from the Zonal and Meridional wind speeds.'
    wind_speed.attrs['long_name'] = 'Wind Speed'
    wind_speed.attrs['standard_name'] = 'wind_speed'
    dsout['wind_speed'] = wind_speed
  
    # Add Wind Direction
    wind_dir = 270 - xr.ufuncs.arctan2(dsout['northward_wind'],dsout['eastward_wind'])*180/np.pi
    #wind_dir = (wind_dir.where(wind_dir<0)+360).combine_first(wind_dir) #Flip negative degrees - Doesn't seem to work
    wind_dir = wind_dir % 360  #Use modulo to keep degrees between 0-360
    wind_dir.attrs['units'] = 'degree'
    wind_dir.attrs['comment'] = 'The direction from which winds are coming from, in degrees clockwise from true N.'
    wind_dir.attrs['long_name'] = 'Wind Direction'
    wind_dir.attrs['standard_name'] = 'wind_from_direction'
    dsout['wind_from_direction'] = wind_dir

    # Add global metadata
    dsout.attrs['title'] = "Rutgers WRF 3km model output"
    dsout.attrs['forecast_offset'] = forecast_offset
    dsout.attrs['source_directory'] = directory
    dsout.attrs['date_created'] = str(datetime.today())
    dsout.attrs['elapsed_time'] = str(datetime.now() - script_start_time)
    dsout.attrs['creator_name'] = "Sage Lichtenwalner"
    dsout.attrs['creator_email'] = "sage@marine.rutgers.edu"
    dsout.attrs['creator_url'] = "https://rucool.marine.rutgers.edu"
    dsout.attrs['institution'] = "Rutgers University Center for Ocean Observing Leadership (RU COOL)"
    dsout.attrs['summary'] = "Wind data extracted from the RU-WRF model.  The model is run daily at 00Z with forecast files saved every hour.  Times in this file are UTC based on the forecast time.  The forecast_offset specifies how many hours of model spin up are allowed before the data is included in this virtual time-series archive for a given day.  For example, a value of 6 means the first 6 hours of data for a day are actually extracted from the previous day's model run."
    dsout.attrs['project'] = "RU COOL BPU Wind Energy Project"
    dsout.attrs['Conventions'] = 'CF-1.6'
  
    # Setup xarray output encoding
    encoding = make_encoding(dsout)
  
    # Output final datafile
    output_datafile = '%s_%d%02d%02d.nc' % (aprefix, start_date.year, start_date.month, start_date.day)
    dsout.to_netcdf(output_datafile, encoding=encoding)  
    print('Outputted ' + output_datafile)
  else:
    print('No data found, skipping.')


# Run main function when in comand line mode        
if __name__ == '__main__':
  # Command Line Arguments
  parser = argparse.ArgumentParser(description='RU-WRF Full Grid Extractor')
  parser.add_argument('date',
    help='Specify a date to process in yyyymmdd format')
  parser.add_argument('-p','--prefix', type=str,
    default='wrf_data',
    help='Prefix for the output filename')
  args = parser.parse_args()
  main(args.date,args.prefix)
