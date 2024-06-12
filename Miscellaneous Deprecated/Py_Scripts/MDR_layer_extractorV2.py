# Libraries used
import arcpy
import os
import pandas as pd
import re

# Allows the file to be written over
arcpy.env.overwriteOutput = True

# Set data product name and input directory
product = input("Enter the name of the data product: ")
input_dir = input("Enter the input directory: ")

# Set the output directory
output_dir = input("Enter the output directory: ")

# Set the layer name
layer_name = input("Enter the layer name to be extracted: ")

###### NOTE: The user must create a text file named "dates.txt". This file will store the dates that will be used for the application.

# Read list of dates
text_file = open("dates.txt","r")
while not os.path.exists("dates.txt"):
  print('The date list text was not found. It should be in the same directory as the .py script.')
  co = input("Press enter to try again.")
date = text_file.read().split(',')

offset = input('Enter the data offset. If there is none, enter 0: ')
try:
  offset = int(offset)
except:
  while offset.isnumeric():
    offset = input('Offset given was not an integer value, please try again: ')

# Monthly Lag
lag = input("Enter the number of monthly lag: ")
lag = int(lag)
# File type
ftype = input("Enter the file extension: ")
# Filename separator
sep = input("Enter the filename separator: ")
# Date position
d_pos = input('Enter the position of the date within the filenames, starting at index 0 (example ALB_2000123 position is 1): ')
d_pos = int(d_pos)
# Year batch
yer = input("Enter the year you wish to process (to process all, leave blank and press enter): ")

# Date Formatting
d_f = input('If the file uses %Y/%j, type A. If the file used %Y/%m/%d, type B: ')
while d_f != 'A' and d_f != 'B':
  d_f = input('Input ERROR. If the file uses %Y/%j, type A. If the file uses %Y/%m/%d, type B: ')
if d_f == 'A':
  d_format = %Y/%j
if d_f =='B':
  d_format == %Y/%m/%d

# Create a list of MD files in the input directory
md_files = []
# Sets date formatting
for d in date:
  g=0
  date_n = pd.to_datetime(d, format = "%m%d%Y")
  date_n = date_n + pd.DateOffset(months=lag)
  u_date_n = date_n + pd.DateOffset(days==offset)
  l_date_n = date_n - pd.DateOffset(days==offset)
  year = date_n.year
  if d_f == 'A':
    doy = date_n.timetuple().tm_yday
    u_date_c = str(u_date_n.year)+str(u_date_n.timetupel().tm_yday).zfill(3)
    l_date_c = str(l_date_n.year)+str(l_date_n.timetuple().tm_yday).zfill(3)
  if d_f =='B':
    u_date_c = str(u_date_n.year)+str(u_date_n.month).zfill(2)+str(u_date_n.day).zfill(2)
    l_date_c = str(l_date_n.year)+str(l_date_n.month).zfill(2)+str(l_date_n.day).zfill(2)
  for file in os.listdir(input_dir):
    if file.endswith(ftype):
      file_p = file.split(sep)
      file_p = file_p[d_pos]
      file_p = re.sub("D",file_p[0])
      date_p = pd.to_datetime(file_p, format=d_format)
      if date_p.year == year and (int(l_date_c) <= int(file_p) and int(file_p) <= int(u_date_c)):
        print(file)
        md_files.append(os.path.join(input_dir,file))
        g=1
        break;
      if g==1:
        g=0
        break;

i=0
# Iterate through the list of MD files
for md_file in md_files:
  # Converts the data format to mmddYYYY
  date_in = pd.to_datetime(date[i], format="%m%d%Y")
  doy_in = date_in.timetyple().tm_yday
  output_file = os.path.join(output_dir, product + '_'+ str(date_in.year) + str(doy_in).zfill(3) + '.tif')
  if str(yer) in md_file:
    print(output_file)
    print(md_file)
    # Creates a new subset multidimensional raster dataset
    arcpy.SubsetMultidimensionalRaster_md(md_file, output_file, layer_name)
  i=i+1
  print("Process complete")

i=0
# Iterate through the list of MD files
for md_file in md_files:
  # Converts the date format to mmddYYYY
  date_in = pd.to_datetime(date[i], format="%m%d%Y")
  # Adds Monthly lag
  date_in = date_in + pd.DateOffset(months=lag)
  doy_in = date_in.timetuple().tm_yday
  output_file = os.path.join(output_dir, product + '_' + str(date_in.year) + str(doy_in).zfill(3) + '.tif')
  if str(yer) in md_file:
    print(output_file)
    print(md_file)
    # Creates a new subset multidimensional raster dataset
    arcpy.SubsetMultidimensionalRaster_md(md_file, output_file, layername)
  i=i+1
  print("Process complete")

i=0
for md_file in md_files:
  # Converts the date format to mmddYYYY
  date_in = pd.to_datetime(date[i], format="%m%d%Y")
  doy_in = date_in.timetuple().tm_yday
  output_file = os.path.join(output_dir, product + '_' + str(date_in.year) + str(doy_in)+'.tif')
  if str(yer) in str(date[i]):
    print(date[i])
    print(output_file)
    print(md_file)
  i=i+1
