# -*- coding: utf-8 -*-
"""MDR_layer_extractor_v1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1I_YHVjE7qsRCGje5eAvG13gUEqtCPGmR

#Introduction
The **MDR_layer_extractorV1** program utilizes the *arcpy.SubsetMultidimentionalRaster_md* function to extract subsets from multiple multidimensional raster datasets. The program saves these to a designated directory, thereby facilitating the analysis and management of specific raster layers.

---
The following program can be ran with these libraries
> * **arcpy** - Allows to run all train and test scripts in an interactive environment
* **os** - Allows the creation and removal of directory folders, gathering data, changing and finding current directory. Also, used for user and operation system to interact
"""

# Libraries used
import arcpy
import os

# Sets the environment to overwrite existing outputs with same name
arcpy.env.overwriteOutput = True

"""- User is asked to state the file input, the file output, the name of the file, and the name of the file extension.

- An example for the input directory would be the following:
>*Enter the input directory:* **E:\share\Copernicus_NDVI\M0204242\NDVI300_201601010000_GLOBE_PROBAV_V1.0.1**

 An example for the output directory would be the following:
>*Enter the output directory:* **E:\share\Copernicus_NDVI\M0204242\NDVI300_201601010000_GLOBE_PROBAV_V1.0.1**

  An example for the layer name is the following:
>*Enter the layer name to be extraced:* **NDVI**

  An example for the name of the extension is the following:
>*Enter the file extension:* **.nc**
"""

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

"""- Using the MD files list, subset operations can be used for the list.

  The output file is made by joining the output directory and the base name of the MD file.
  
  The file extension from the **output_file** is removed and the file extension is then replaced with ".tif".
  
  The *arcpy.SubsetMultidimensionalRaster_md* function is used to create a new subset multidimensional raster dataset from the current **md_file**, the **output_file**, and the **layer_name**.

- Each subset is then printed with the final statement being "Process complete".
"""

# Iterate through the list of MD files and perform the subset
for md_file in md_files:
  # Set the output file name
  output_file = os.path.join(output_dir, os.path.basename(md_file))
  output_file = os.path.splitext(output_file)[0] + ".tif"
  print(md_file)
  # Perform the subset
  arcpy.SubsetMultidimensionalRaster_md(md_file, output_file, layer_name)
print("Process complete.")