# -*- coding: utf-8 -*-

# Libraries used
import arcpy
import os

arcpy.env.overwriteOutput = True

#Set the input directory
input_dir = input("Enter the input directory: ")
#Set the output directory
output_dir = input("Enter the output directory: ")
#Set the layer name
layer_name = input("Enter the layer name to be extracted: ")
#File extension
ext = input("Enter the file extenstion: ")

# Create a list of .hdf files in the input directory
hdf_files = []
for file in os.listdir(input_dir):
  if file.endswith(ext):
    hdf_files.append(os.path.join(input_dir,file))

# Iterate through the list of .hdf files and perform the subset
for hdf_file in hdf_files:
  # Set the output file name
  output_file = os.path.join(output_dir,os.path.basename(hdf_file))
  output_file = os.path.splitext(output_file)[0] + ".tif"
  print(hdf_file)
  # Perform the subset
  arcpy.SubsetMultidimensionalRaster_md(hdf_file,output_file,layer_name)
print("Process complete")
