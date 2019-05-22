# RU-WRF Extraction Scripts
By Sage Lichtenwalner with help from Joe Brodie and Jaden Dicopoulos
These scripts were developed to support RU COOL's BPU Projects
Readme revised 4/4/19

|| Filename        || type || Model Files|| Levels || Import Lib  || Archive    ||
| wrf2nc            | point | old grib   | 4 levels | pygrib       | vmt_archive |
| wrf2nc_oyster     | point | old grib   | 5 levels | pygrib       |             |
| wrfnc2nc          | point | old netcdf | 4 levels | xarray       |             |
| wrf_extract       | grid  | old grib   | 10m      | pygrib       | fullgrid_archive |
| wrfgrid2nc        | grid  | old grib   | all      | pynio        | wrfgrid_archive |
| bvg_wrfgrid2nc    | grid  | old & new  | all      | pynio/xarray |             |
| wrfptextract_grib | point | old grib   | 4 levels | pygrib       |             |
| wrfptextract_nc   | point | new netcdf | 4 levels | xarray       |             |


## Notes
* wrfptextract_grib was adapted from wrf2nc
* wrfptextract_nc was adapted from wrfnc2nc


## Data Availabilty
NEED TO VERIFY THESE WITH EXACT DATES
8/1/13 and 9/1/13 have the dimensions (11, 376, 390) and heights: [10 60:10:150]
10/1/13 (or perhaps mid Sept) and on has the dimensions (11, 324, 324) and heights
12/1/14 (really 11/28) and on has the dimensions (15, 324, 324)     [10:10:150]
6/1/15 and on has the dimensions (20, 324, 324) and heights [10:10:200]