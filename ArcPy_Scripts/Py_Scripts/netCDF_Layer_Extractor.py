# -*- coding: utf-8 -*-
import os
import arcpy
import fnmatch

def find_files(directory, extension):
    # Empty lists are created
    matches = []
    file_n = []
    # Sorts through all files
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, f'*.{extension}'):
            matches.append(os.path.join(root, filename))
            file_n.append(filename)
    return matches, file_n

# Set the input directory
input_dir = input("Enter the parent input directory: ")

# Set the output directory
output_dir = input("Enter the parent output directory: ")

# File Extension
file_ex = input("Please enter the input extension of the file: ")

# File Extraction
var = input("Please enter the variable for the extraction: ")

# geodatabase_path is created and checks if file was created
geodatabase_path = os.path.join(output_dir, 'netCDF_Layer_extractor.gdb')
if os.path.exists(geodatabase_path):
    print(geodatabase_path)
else:
    arcpy.CreateFileGDB_management(output_dir, 'netCDF_Layer_extractor')

files, file_ns= find_files(input_dir, file_ex)
XDimension = "lon"
YDimension = "lat"
i = 0
for file_path in files:
    if True:
        f_name = os.path.join(output_dir,file_ns[i].replace('.nc', '.crf').replace('0000', ''))
        print(f_name)
        arcpy.md.MakeMultidimensionalRasterLayer(file_path,f_name,var)
        arcpy.management.Resample(f_name, f_name)
    i = i + 1
