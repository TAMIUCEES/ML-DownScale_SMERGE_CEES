# Libraries used
import arcpy
from arcpy import env
import re
import pandas as pd
from arcpy.sa import *
import os

# Define the parent folder and the geodatabase name
parent_folder = os.getcwd()
geodatabase_name = "example.gdb"

# Create the file geodatabase
geodatabase_path = os.path.join(parent_folder, geodatabase_name)
if os.path.exists(geodatabase_path):
  print(geodatabase_path)
else:
  arcpy.CreateFileGDB_management(parent_folder, geodatabase_name)

# Set the geodatabase as the workspace
arcpy.env.workspace = geodatabase_path

# Set up the environment
arcpy.env.parallelProcessingFactor = 0
arcpy.CheckOutExtension("Spatial")
acrpy.env.mathMultidimensionalVariable = False
acrpy.env.overwriteOutput = True

# Set data product name
product = input("Enter the name of the data product: ")

# Select point file
point_shape_name = input('Enter the name of the point shape file you want to use: ')
gb_thirty_points = os.path.join(geodatabase_path, point_shape_name)

table = gb_thirty_points

# List the fields you want to include
columns = [f.name for f in arcpy.ListFields(table) if f.type!="Geometry" and product in f.name]
print(columns)

fields = []
for c in columns:
  temp = [c, 'MEAN']
  fields.append(temp)

grid_shape_file = input("Enter the full file path and name of the grid shape file: ")
while not os. path.isfile(grid_shape_file):
  print('The shapefile was not found.')
  co = input("Please try again: ")

# Set resolution
out_n = input('Enter name of output: ')
grid_db = 'Grid_'+ resolution
arcpy.conversion.FeatureClassToFeatureClass(grid_shape_file, geodatabase_path, grid_db)

arcpy.gapro.AggregatePoints(point_layer=gb_thirty_points, out_feature_class=out_n, polygon_or_bin='polygon', polygon_layer=grid_db, summary_fields=fields)

out_folder = input('Enter output folder path for table: ')
arcpy.conversion.TableToTable(out_n, out_folder, out_n + '.csv')
