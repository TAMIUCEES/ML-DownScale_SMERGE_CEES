# -*- coding: utf-8 -*-
# Libraries used
import arcpy
import os

# Sets the environment to overwrite existing outputs with same name
arcpy.env.overwriteOutput = True

# Sets the input directory
input_dir = input("Enter the input directory: ")
# Sets the output directory
output_dir = input("Enter the output directory: ")

# Sets the layer name
layer_name = input("Enter the layer name to be extracted: ")
# Sets the file extension
ext = input("Enter the file extenstion: ")

# Create a list of MD files in the input directory
md_files = []
for file in os.listdir(input_dir):
  if file.endswith(ext):
    md_files.append(os.path.join(input_dir, file))

# Iterate through the list of MD files and perform the subset
for md_file in md_files:
  # Set the output file name
  output_file = os.path.join(output_dir, os.path.basename(md_file))
  output_file = os.path.splitext(output_file)[0] + ".tif"
  print(md_file)
  # Perform the subset
  arcpy.SubsetMultidimensionalRaster_md(md_file, output_file, layer_name)
print("Process complete.")
