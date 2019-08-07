# RU-WRF Extraction Scripts
This library contains a set of scripts to extract data from the RU-WRF model.

## Quickstart
The most useful functions are:
* wrfptextract_grib.py - Extracts timeseries for a set of specified data points from the older v3.6 model runs, prior to 12/1/2017.
* wrfptextract_nc.py - Extract timeseries for a set of specified data points from the newer v3.9 model runs, starting 12/1/2017.

Both of these functions can be run using the following syntax:

`./wrfptextract_grib.py 20141201 -d31 -c wrf_bpu_points.csv -f 1`

* yyyymmdd is the date to start the extraction
* -d is used to specify the number of days to extract.  The default is 1 day.
* -c specifies the filename that includes the lat/lon points to extract timeseries data points for
* -f specifies how many forecast hours to skip at the beginning of the run.  The default is 6 hours.
* -p specifies the prefix to prepend on the outputted file.


## Converter Script Summary

| Filename          | type  | Model Files| Levels   | Import Lib   | Archive     |
|-------------------|-------|------------|----------|--------------|-------------|
| wrf2nc            | point | old grib   | 4 levels | pygrib       | vmt_archive |
| wrf2nc_oyster     | point | old grib   | 5 levels | pygrib       |             |
| wrfnc2nc          | point | old netcdf | 4 levels | xarray       |             |
| wrf_extract       | grid  | old grib   | 10m      | pygrib       | fullgrid_archive |
| wrfgrid2nc        | grid  | old grib   | all      | pynio        | wrfgrid_archive |
| bvg_wrfgrid2nc    | grid  | old & new  | all      | pynio/xarray |             |
| wrfptextract_grib | point | old grib   | 4 levels | pygrib       |             |
| wrfptextract_nc   | point | new netcdf | 4 levels | xarray       |             |


### Notes
* wrfptextract_grib was adapted from wrf2nc
* wrfptextract_nc was adapted from wrfnc2nc


## Model Data Availabilty
* NEED TO VERIFY THESE WITH EXACT DATES AND LEVELS
* 8/1/13 and 9/1/13 have the dimensions (11, 376, 390) and heights: [10 60:10:150]
* 10/1/13 (or perhaps mid Sept) and on has the dimensions (11, 324, 324) and heights
* 12/1/14 (really 11/28) and on has the dimensions (15, 324, 324)     [10:10:150]
* 6/1/15 and on has the dimensions (20, 324, 324) and heights [10:10:200]


This library was developed by Sage Lichtenwalner, with help from Joe Brodie and Jaden Dicopoulos, Rutgers University Center for Ocean Observing Leadership ([RU COOL](https://rucool.marine.rutgers.edu)).


Revised 5/22/19