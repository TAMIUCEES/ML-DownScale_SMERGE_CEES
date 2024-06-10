# -*- coding: utf-8 -*-
import os
import sys
import arcpy

# State the file path
raster_path = input("Enter the full file path of the template point shape file: ")

# State the name of the raster file
raster_name = input("Enter the name of the raster file: ")

# Creating a full path of the point shape file path and the name of the raster file
raster_file = os.path.join(raster_path, raster_name)

# Gets a list of the bands that make up the raster
arcpy.env.workspace = raster_file
bRng = arcpy.ListRasters()

for ThisBnd in bRng:
  # Loop through the bands and export each one with CopyRaster
  InBand = os.path.join(raster_file, ThisBnd)
  bndDesc = arcpy.Describe(InBand)
  NoData = bndDesc.noDataValue
  # Splits the image name and extension
  InSplit = os.path.splitext(raster_file)
  OutRas = '{}_{}{}'.format(InSplit[0], ThisBnd, InSplit[1])
  arcpy.CopyRaster_management(InBand, OutRas, nodata_value = NoData)
