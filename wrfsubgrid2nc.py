#!/usr/bin/env python
# Script to extract RU-WRF Model Data layers from both old GRIB files and new NetCDF files
# Can also extract a specific lat/lon box
# Written by Sage, 11/13/19
# Example function call: ./wrfsubgrid2nc.py 20190101 -d 31 -f 1 

from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import xarray as xr
import argparse

#------------------------------
def clean_grib_dataset(ds):
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

def clean_nc_dataset(ds):
  '''Clean the NetCDF dataset'''
  nds1 = xr.Dataset()
  nds1['eastward_wind'] = ds.U
  nds1['northward_wind'] = ds.V
  nds1.rename({'height':'z','west_east':'x','south_north':'y','XLAT':'lat','XLONG':'lon','Time':'time'},inplace=True)
  nds1 = nds1.drop('XTIME')
  nds2 = xr.Dataset()
  nds2['eastward_wind'] = ds.U10
  nds2['northward_wind'] = ds.V10
  nds2.rename({'west_east':'x','south_north':'y','XLAT':'lat','XLONG':'lon','Time':'time'},inplace=True)
  nds2 = nds2.drop('XTIME')
  nds2['z'] = [10]
  nds = xr.concat([nds1,nds2],dim='z')
  return nds.sel(z=[10,100,120,140]) #Save selected layers    
  
  
#------------------------------
def make_encoding(ds, time_start='days since 2010-01-01 00:00:00', comp_level=5, fillvalue=-999.00):
  '''Create variable encodings for saving to netcdf'''
  encoding = {}
  for k in ds.data_vars:
    encoding[k] = {'zlib': True, 'complevel': comp_level} #'_FillValue': np.float32(fillvalue)
  encoding['time'] = dict(units=time_start, calendar='gregorian', zlib=False, _FillValue=False, dtype=np.double)
  return encoding


#------------------------------
def main(adate,adays,aprefix,forecast_offset):
  """Main function for command line execution"""
  script_start_time = datetime.now() #Script Timer

  if len(adate)!=8:
    raise ValueError('Please enter a date in the format yyyymmdd') 

  # Specify Date Range to Process
  year  = int(adate[0:4])
  month = int(adate[4:6])
  day   = int(adate[6:8])
  start_date = datetime(year,month,day)
  end_date = start_date + timedelta(adays) - timedelta(0,60*60)

  times = pd.date_range(start_date, end_date, freq="H")
  dsout = False #Default output

  # Loop over each hour
  for t in times:
    t2 = t.replace() # Copy variable to mess with
    if t2.hour < forecast_offset:
      t2 = t2-timedelta(1) # Previous model run
      hour = t2.hour + 24
    else: 
      hour = t2.hour
    
#     # Older Model Files
#     directory = '/home/bowers/output/grib/3km/'
#     if start_date.year == 2016 and start_date >= datetime(2016,6,7):
#       dir_name = '2016_new' # Hack to handle split 2016
#     else:
#       dir_name = str(start_date.year)
#     wrf_file = '%s/RUWRF_3km_%d%02d%02d00_%02d:00.grb2' % (dir_name,year,month,day,jj)

    # Newer Model Files
    directory = '/home/coolgroup/ru-wrf/real-time/processed/3km/'
    wrf_file = '%d%02d%02d/wrfproc_3km_%d%02d%02d_00Z_H0%02d.nc' % (t2.year,t2.month,t2.day,t2.year,t2.month,t2.day,hour)

    print('Processing: ' + directory + wrf_file)
    
    ds = False
    try:
      ds = xr.open_dataset(directory + wrf_file, engine='pynio')
    except:
      print('Could not open ' + wrf_file)
    if(isinstance(ds,xr.Dataset)):
#       if(amodel=='original'):
#         ds = clean_grib_dataset(ds)
#       elif(amodel=='new'):
      ds = clean_nc_dataset(ds)
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
    wind_speed.attrs['standard_name'] = 'wind_speed'
    wind_speed.attrs['long_name'] = 'Wind Speed'
    wind_speed.attrs['units'] = 'm s-1'
    wind_speed.attrs['comment'] = 'Wind Speed is calculated from the Zonal and Meridional wind speeds.'
    dsout['wind_speed'] = wind_speed
  
    # Add Wind Direction
    wind_dir = 270 - xr.ufuncs.arctan2(dsout['northward_wind'],dsout['eastward_wind'])*180/np.pi
    #wind_dir = (wind_dir.where(wind_dir<0)+360).combine_first(wind_dir) #Flip negative degrees - Doesn't seem to work
    wind_dir = wind_dir % 360  #Use modulo to keep degrees between 0-360
    wind_dir.attrs['standard_name'] = 'wind_from_direction'
    wind_dir.attrs['long_name'] = 'Wind Direction'
    wind_dir.attrs['units'] = 'degree'
    wind_dir.attrs['comment'] = 'The direction from which winds are coming from, in degrees clockwise from true N.'
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
    output_datafile = '%s_%d%02d%02d_%d%02d%02d.nc' % ( 
      aprefix, 
      start_date.year, start_date.month, start_date.day, 
      end_date.year, end_date.month, end_date.day)
    dsout.to_netcdf(output_datafile, encoding=encoding)  
    print('Outputted ' + output_datafile)
    
  else:
    print('No data found, skipping.')


# Run main function when in comand line mode        
if __name__ == '__main__':
  # Command Line Arguments
  parser = argparse.ArgumentParser(description='RU-WRF Subgrid Extractor')
  parser.add_argument('date',
    help='Specify a date to process in yyyymmdd format')
  parser.add_argument('-d','--days', type=int,
    default=1,
    help='Number of days to process')
  parser.add_argument('-p','--prefix', type=str,
    default='wrfsubgrid2',
    help='Prefix for the output filename')
  parser.add_argument('-f','--forecast_offset', type=int,
    default=6,
    help='Forecast hour to begin model run with (from 0 to 23)')
  args = parser.parse_args()
  main(args.date,args.days,args.prefix,args.forecast_offset)

