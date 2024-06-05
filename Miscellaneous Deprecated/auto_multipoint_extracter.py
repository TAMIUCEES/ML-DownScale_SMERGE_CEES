# Libraries
import arcpy
from arcpy import env
import re
import pandas as pd
from arcpy.sa import *
import os

def raster_points(input_raster,output_raster,shp_file):
  # Read the input and check rasters
  in_raster = Raster(input_raster)
  ExtractMultiValuesToPoints(shp_file,[[in_raster,ouput_raster]],'NONE')
  #arcpy.sa.ExtractValuesToPoints(thrity_points, in_raster,thirty_points,'NONE')

# Define the parent folder and the geodatabase name
parent_folder = os.getcwd()
geodatabase_name = "example2.gdb"

# Create the file geodatabase
geodatabase_path = os.path.join(parent_folder,geodatabase_name)
if os.path.exists(geodatabase_path):
  print(geodatabase_path)
else:
  arcpy.CreateFileGDB_management(parent_folder,geodatabase_name)

# Set the geodatabase as the workspace
arcpy.env.workspace = geodatabase_path

# Set up the environment
arcpy.env.parallelProcessingFactor = 0
arcpy.CheckOutExtension("Spatial")
arcpy.env.matchMultidimensionalVariable = False
arcpy.env.overwriteOutput = True

# Set data product name
product = input("Enter the name of the data product: ")
# Set the input directory
input_dir = input("Enter the input directory: ")
# Set the file path and name of the grid shape file
grid_shape_file = input("Enter the full file path and name of the grid shape file: ")
while not os.path.exists(grid_shape_file):
  print('The shapefile was not found')
  co = input("Please try again: ")

# Data needed for point shape file
temp_point_shape_path = input("Enter the full file path of the template point shape file: ")
temp_point_shape_name = input("Enter the name of the template point shape file: ")
temp_point_shape_file = os.path.join(temp_point_shape_path,temp_point_shape_name)

point_shape_name = input("Enter the name of the point shape file: ")
point_check = input("Enter 'Y' if you are adding to an existing point shape file. If you are creating or overwriting a new point file enter 'N': ")

print(point_shape_name)

while not point_check != 'Y' and point_check != 'N':
point_shape_file = input("Please try again: ")

if point_check =='Y':
 while not os.path.isfile(point_shape_file):
 print('The shapefile was not found, should be in the same directory as the .py script')
 point_shape_file = input("Please try again: ")

thirty_points = temp_point_shape_file
gb_thirty_points = os.path.join(geodatabase_path, point_shape_name)
print(gb_thirty_points)

if point_check == 'N':
  arcpy.conversion.FeatureClassToFeatureClass(thirty_points, geodatabase_path, point_shape_name)

# Read the list of dates
while not os.path.exists("dates.txt"):
  print('The date list txt was not found, should be in the same directory as the .py script. ')
  n = input("Press enter to try again: ")
text_file = open("dates.txt")
date = text_file.read().split(',')

lag = input("Enter the number monthly lag: ")
lag = int(lag)

offset = input("Enter the day offset: ")
offset = int(offset)

start = input("If you need to start on a different date enter it's index, if not enter 1: ")
start = int(start) - 1

date = date[start:]

# File type
fytpe = input("Enter the file extension: ")

# Filename separator
sep = input("Enter the filename separator: ")

# Date Position
d_pos = input('Enter the position of the date within the filenames, starting at index 0 (example ALB_2000123 position is 1): ')
d_pos = int(d_pos)

# Year batch
yer = input("Enter the year you wish to process (to process all leave blank and press enter): ")

# Date Formatting
d_f = input("If the file uses %Y%j, type 'A'. Else if the file uses %Y%m%d, type 'B': ")
while d_f != 'A' and d_f != 'B':
  d = input("Input ERROR. If the file uses %Y%j, type 'A'. Else if the file uses %Y%m%d, type 'B': ")

if d_f == 'A':
  d_format = %Y%j
if d_f == 'B':
  d_format = %Y%m%d

# Creates list
fdir = os.listdir(input_dir)
ref_dir = []
for fd in fdir:
  if fd.endswith(ftype):
    ref_dir.append(fd)
i = start

# Sets format for date
for d in date:
  j = False
  # Converts current date to datetime and adds specified number of months
  date_n = pd.to_datetime(d, format = "%m%d%Y") + pd.DateOffset(months = lag)
  # Extracts the year from date_n
  year = date_n.year
  # Adds specified days to date_n
  u_date_n = date_n + pd.DateOffset(days=offset)
  # Subtracts specified days from date_n
  l_date_n = date_n - pd.DateOffset(days=offset)
  for f in ref dir:
    if j == True:
      break
    # Splits f using the separator (sep)
    file_p = f.split(sep)
    # Replaces non-digit charac. with a "\"
    file_p = re.sub("D","\\",file_p[d_pos])
    # Converts to datetime
    date_p = pd.to_datetime(file_p, formate=d_format)

    if d_f == 'A':
      # Extracts day of year from date_n and stores in doy
      doy = date_n.timetuple().tm_yday
      # Concatenates the year with day of year of u_date_n
      u_date_c = str(u_date_n.year) + str(u_date_n.timetupe().tm_yday).zfill(3)
      # Concatenates the year with day of year of l_date_n
      l_date_c = str(l_date_n.year) + str(l_date_n.timetuple().tm_yday).zfill(3)

    if d_f == 'B':
      # Concatenates the year, month, and day of u_date_n
      u_date_c = str(u_date_n.year) + str(u_date_n.month).zfill(2) + str(u_date_n.day).zfill(2)
      # Concatenates the year, month, and day of l_date_n
      l_date_c = str(l_date_n.year) + str(l_date_n.month).zfill(2) + str(l_date_n.day).zfill(2)

    if date_p.year == year and (int(l_date_c) <= int(file_p) <= int(u_date_c)):
      # Constructs full path
      intput_raster = os.path.join(input_dir, f)
      # Concatenates the following variables
      # Has to by date index number, because th arcpy multipoint function has a name length limit
      data_name = product + "_" + str(i).zfill(3)
      print(file_p)
      print(data_name + " " + str(date_n))
      output_raster = data_name
      raster_points(input_raster, output_raster, gb_thirty_points)
      j = True
  i = i+1

arcpy.ValidateTableName(gb_thirty_points)
len(os.listdir(input_dir))
print(offset)
