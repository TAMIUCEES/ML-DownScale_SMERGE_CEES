# -*- coding: utf-8 -*-
import os
import re
import pandas  as pd
import arcpy
from arcpy import env
from arcpy.sa import *
from datetime import datetime

# Define the parent folder and the geodatabase name
parent_folder = input('Enter the path to the parent folder: ')
geodatabase_name = input('Enter the name of the geodatabase: ')

# Create the file geodatabase
geodatabase_path = os.path.join(parent_folder, geodatabase_name)

# Generates the geodatabase (geodatabase is used as a working directory) and crucial to keep code as it is needed to run.
#arcpy.CreateFileGDB_management(parent_folder, geodatabase_name)

# Set the geodatabase as the workspace
arcpy.env.workspace = geodatabase_path

# Set up the environment
arcpy.CheckOutExtension("Spatial")

arcpy.env.matchMultidimensionalVariable = False
#arcpy.env.cellSize = 200
arcpy.env.overwriteOutput = True
#input_dir = r"D:\LST\TXson_Rasters\New_folder"

# Set the input directory
input_dir = input("Enter the input directory: ")

# Set the output directory
output_dir = input("Enter the output directory: ")

# State the amount of files that will be merged at a time.
file_n = input("Enter the number of files that need to be merged at a time: ")

# Get a list of all files and directories in input_dir
dir = os.listdir(input_dir)

# Subtracts 1 from the length of the list
total_files = len(dir) - 1

# Prints out the value of total_files
print(total_files)

i = 0
k = 4
print(i)
while i < total_files:
    if i > 646:
        file_p1 = dir[i].split('.')
        file_d1 = re.sub("\D", "", file_p1[1])
        print(i)
        f_inputs = []
        for j in range(int(file_n)):
            f_inputs.append(os.path.join(input_dir, dir[i + j]))
        # f1 = os.path.join(input_dir,dir[i])
        # f2 = os.path.join(input_dir,dir[i+1])
        print(f_inputs)
        f_out = os.path.join(output_dir, file_p1[0] + '_' + file_p1[1] + '.crf')
        arcpy.md.MergeMultidimensionalRasters(f_inputs, f_out, 'MEAN')
    i = i + 2
