import os
import re
import pandas as pd
import arcpy
from arcpy import env
from arcpy.sa import *

def raster_points(input_raster, output_table, shp_file):
  # Read the input and check rasters
  in_raster = Raster(input_raster)

  zoneField = input("Enter the index variable: ")
  outZSaT1 = ZonalStatisticsAsTable(shp_file, zoneField, input_raster, "output_tableG", "DATA", "ALL", "CURRENT_SLICE", 90, "AUTO_DETECT", "ARITHMETIC", 360)

  arcpy.conversion.ExportTable("output_tableG", output_table.replace('.dbf','.csv'))
  arcpy.management.Delete("output_tableG")
  arcpy.management.ClearWorkspaceCache()
  #arcpy.sa.ExtractValuesToPoints(thirty_points, in_raster, thirty_points, 'NONE')

def find_uncommon_elements(list1, list2):
  # Convert lists to sets for efficient operations
  set1 = set(list1)
  set2 = set(list2)

  #Find elements that are unique to each set
  unique_to_set1 = set1 - set2
  unique_to_set2 = set2 - set1

  # Combine the unique elements and convert back to a list
  result = list(unique_to_set1.union(unique_to_set2))
  return result

# Define the parent folder and the geodatabase name
parent_folder = os.getcwd()
geodatabase_name = "example2.gdb"

#Create the file geodatabase
geodatabase_path = os.path.join(parent_folder, geodatabase_name)
if os.path.exists(geodatabase_path):
  print(geodatabase_path)
else:
  arcpy.CreateFileGDB_management(parent_folder, geodatabase_name)

# Set the geodatabase as the workspace
arcpy.env.workspace = geodatabase_path

# Set up the environment
arcpy.SetLogHistory(True)
arcpy.env.parallelProcessingFactor = "\\"
arcpy.CheckOutExtension("ImageAnalyst")
arcpy.env.matchMultidimensionalVariable = False
arcpy.env.overwriteOutput = True
# asking for a raster that is at or below (cannot go too below, the runtime will be too long) target reso (it's forcing zonal stats to recognize the cellSize)
arcpy.env.cellSize = input("Enter the full directory of the raster that is at or below (but not too small, it can make runtime too long) the target resolution: ")

# Set the data product name
product = input("Enter the name of the data product: ")
# Set the input directory
input_dir = input("Enter the input directory: ")
# Set the output directory
output_dir = input("Enter the output directory: ")
# Set the layer name
layer_name = input("Enter the layer name: ")

# Uploads txt file
d_text = input("Enter the date list text file: ")
# Opens and reads list of dates
text_file = open(d_text, "r")
# Checks file's existence
while not os.path.exists(d_text):
  print("The date list text file was not found. It should be in the same directory as the '.py' script.")
  n = input("Press enter to try again.")
  text_file = open(d_text, "r")
# Reads file
date = text_file.read().split(',')

# Text file with adjusted data is uploaded
d_text1 = input("Enter the adjusted date list text file: ")
# Read list of dates
text_file1 = open(d_text1, "r")
# Reads file
date1 = text_file1.read().split(',')
# Finds unique elements from files date and date1
date = find_uncommon_elements(date, date1)

# State the monthly lag
lag = input('Enter the number of monthly lag: ')
# Convert to integer
lag = int(lag)

# State the day offset
offset = input('Enter the day offset: ')
# Convert to integer
offset = int(offset)

# State whether or not the starting date is different
start = input('If you need to start on a different date, enter its index. If not, enter 1: ')
# Convert to integer
start = int(start)
# Extracts portion of a list
date = date[start:]

# Uploads text file
d_text = input("Enter the adjusted date list text file: ")

# Opens and reads the list of dates
text_file = open(d_text, "r")

# Checks file's existence
while not os.path.exists(d_text, "r"):
  print("The date list txt file was not found. It should be in the same directory as the '.py' script.")
  n = input("Press enter to try again.")
  text_file = open(d_text, "r")

date = text_file.read().split(',')

# State the monthly lag
lag = input("Enter the number of monthly lag: ")
# Convert to integer
lag = int(lag)

# State the day offset
offset = input("Enter the day offset: ")
# Convert to integer
offset = int(offset)

# State whether or not the starting date is different
start = input("If you need to start on a different date, enter its index. If not, enter 1: ")
# Convert to integer
start = int(start) - 1
# Extracts a portion of a list
date = date[start:]
# State the file type
ftype = input("Enter the file extension: ")
# State the filename separator
sep = input("Enter the filename separator: ")
# State the position of date
d_pos = input("Enter the position of the date within the filenames, starting at index 0 (for example: for 'ALB_2000123', the position is 1): ")
# Convert to integer
d_pos = int(d_pos)
# State the year batch
yer = input("Enter the year you want to process. If you wish to process all, leave blank and press enter: ")

# Date Formatting
d_f = input("If the file use '%Y/%j' type: A, if '%Y/%m/%d' type: B: ")
while d_f != 'A' and d_f != 'B':
  d = input("Input ERROR. If file use '%Y/%j' type: A, if '%Y/%m/%d' type: B: ")
# Choice for formatting date
if d_f == 'A':
  d_format = '%Y/%j'
if d_f == 'B':
  d_format = '%Y/%m/%d'
# Creates list
fdir = os.listdir(input_dir)
ref_dir = []
for fd in fdir:
    if fd.endswith('.nc'):
        ref_dir.append(fd)

k = 0
i = start
# Sets format for date
for d in date:
    j = False
    # Converts current date to datetime and adds specified number of months
    date_n = pd.to_datetime(d, format="%m/%d/%Y") + pd.DateOffset(months=lag)
    # Extracts the year from date_n
    year = date_n.year
    # Adds specified days to date_n
    u_date_n = date_n + pd.DateOffset(days=offset)
    # Subtracts specified days from date_n
    l_date_n = date_n - pd.DateOffset(days=offset)
    for f in ref_dir:
        if j == True:
            break
        # Splits f using the separator (sep)
        file_p = f.split(sep)
        # Non-digit charac. are replaced
        file_p = re.sub("\D", "", file_p[d_pos])
        # Converts to datetime
        date_p = pd.to_datetime(file_p, format = d_format)

        if d_f == 'A':
          # Extracts day of year from date_n and stores in doy
            doy = date_n.timetuple().tm_yday
            # Concatenates the year with day of year of u_date_n
            u_date_c = str(u_date_n.year) + str(u_date_n.timetuple().tm_yday).zfill(3)
            # Concatenates the year with day of year of l_date_n
            l_date_c = str(l_date_n.year) + str(l_date_n.timetuple().tm_yday).zfill(3)

        if d_f == 'B':
          # Concatenates the year, month, and day of u_date_n
            u_date_c = str(u_date_n.year)  + str(u_date_n.month).zfill(2) + str(u_date_n.day).zfill(2)
          # Concatenates the year, month, and day of l_date_n
            l_date_c = str(l_date_n.year)  + str(l_date_n.month).zfill(2) + str(l_date_n.day).zfill(2)

        if date_p.year == year and (int(l_date_c) <= int(file_p) and int(file_p) <= int(u_date_c)):
          # Constructs full path
            input_raster = os.path.join(input_dir, f)
            # Has to by date index number, because the arcpy multipoint function has a name length limit
            d_n = str(date_n.year) + str(date_n.timetuple().tm_yday).zfill(3)

            data_name = product + "_" + d_n + layer_name + '.tif'
            # Constructs full path
            output_raster =  os.path.join(output_dir, data_name)
            print(output_raster + str(os.path.exists(output_raster)))
            if not os.path.exists(output_raster):
                print(file_p)
                print(data_name + " " + str(date_n))
                arcpy.SubsetMultidimensionalRaster_md(input_raster, output_raster, layer_name)
            #removes previously used files from list to prevent repeated data
            #ref_dir.remove(f)
            j = True
    if j == False:
        k = k + 1
        #print('Unable to find: ' + str(date_n.year)+ str(date_n.month).zfill(2) + str(date_n.day).zfill(2) )
        #print(k)
    i = i + 1

##### If the code above is incompatible with the user's data, the user must use the code below to ensure the program's successful execution. #####
    
#k = 0
#i = start
### Sets format for date
#for d in date:
#    j = False
#    # Converts current date to datetime and adds specified number of months
#    date_n = pd.to_datetime(d, format="%m/%d/%Y") + pd.DateOffset(months=lag)
    ### Extracts the year from date_n
#    year = date_n.year
    ### Adds specified days to date_n
#    u_date_n = date_n + pd.DateOffset(days=offset)
    ### Subtracts specified days from date_n
#    l_date_n = date_n - pd.DateOffset(days=offset)
#    for f in ref_dir:
#        if j == True:
#            break
        ### Splits f using the separator (sep)
#        file_p = f.split(sep)
        ### Non-digit charac. are replaced
#        file_p = re.sub("\D", "", file_p[d_pos])
        ### Converts to datetime
#        date_p = pd.to_datetime(file_p, format = d_format)

#        if d_f == 'A':
          ### Extracts day of year from date_n and stores in doy
#            doy = date_n.timetuple().tm_yday
            ### Concatenates the year with day of year of u_date_n
#            u_date_c = str(u_date_n.year) + str(u_date_n.timetuple().tm_yday).zfill(3)
            ### Concatenates the year with day of year of l_date_n
#            l_date_c = str(l_date_n.year) + str(l_date_n.timetuple().tm_yday).zfill(3)

#        if d_f == 'B':
          ### Concatenates the year, month, and day of u_date_n
#            u_date_c = str(u_date_n.year)  + str(u_date_n.month).zfill(2) + str(u_date_n.day).zfill(2)
          ### Concatenates the year, month, and day of l_date_n
#            l_date_c = str(l_date_n.year)  + str(l_date_n.month).zfill(2) + str(l_date_n.day).zfill(2)
#        if date_p.year == year and (int(l_date_c) <= int(file_p) and int(file_p) <= int(u_date_c)):
          ### Constructs full path
#            input_raster = os.path.join(input_dir, f)
            ### Has to by date index number, because the arcpy multipoint function has a name length limit
#            d_n = str(date_n.year) + str(date_n.timetuple().tm_yday).zfill(3)
#            data_name = product + "_" + d_n + layer_name + '.tif'
            ### Constructs full path
#            output_raster =  os.path.join(output_dir, data_name)
#            print(output_raster + str(os.path.exists(output_raster)))
#            if not os.path.exists(output_raster):
#                print(file_p)
#                print(data_name + " " + str(date_n))
#                arcpy.md.MakeMultidimensionalRasterLayer(input_raster, output_raster, layer_name)
#                arcpy.management.Resample(output_raster, output_raster)
            ### removes previously used files from the list to prevent repeated data
            #ref_dir.remove(f)
#            j = True
#    if j == False:
#        k = k + 1
        #print('Unable to find: ' + str(date_n.year)+ str(date_n.month).zfill(2) + str(date_n.day).zfill(2) )
        #print(k)
#    i = i + 1
