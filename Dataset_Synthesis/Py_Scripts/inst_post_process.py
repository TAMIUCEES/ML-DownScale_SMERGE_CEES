import os
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import string
import warnings
import sys
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Set data product name
d_name = input("Enter the name of the dataset (Include file extension): ")

# Set the input directory
input_dir = input("Enter the input directory: ")

# Set the output directory
output_dir = input("Enter the output directory: ")

stattion_p_file = open("station_pagenames", "r")

while not os.path.exists(stattion_p_file):
  print('The station_pagenames list txt was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  stattion_p_file = open("station_pagenames", "r")

stattion_p = stattion_p_file.read().split(',')
stattion_n_file = open("station_names.txt","r")

while not os.path.exists(stattion_n_file):
  print('The station_names.txt list txt was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  stattion_n_file = open("station_names.txt", "r")

stattion_n = stattion_n_file.read().split(',')

variables = input("Enter the name of the variables list (make sure the file is in the text file format): ")
variables_file = os.path.join(input_dir, variables)

while not os.path.exists(variables_file):
  variables = input("The variables list txt as not found, it should be in the home directory, try again. ")
  variables_file = os.path.join(input_dir, variables)

def date_formatting(data):
  date_format = input('If file uses "%m/%d/%Y" type: A, if "%Y/%m/%d" type: B, else "%Y/%j" type: C : ')

  while date_format != 'A' and date_format != 'B' and date_format != 'C':
    date_format = input('INPUT ERROR. If file uses "%m/%d/%Y" type: A, if "%Y/%m/%d" type: B, else "%Y/%j" type: C')

  if date_format == 'A':
    data['Date'] = pd.to_datetime(date['Date'], format = "%m/%d/%Y")
    data['Date'] = data['Date'].astype(int)

  if date_format == 'B':
    data['Date'] = pd.to_datetime(date['Date'], format = "%Y/%m/%d")
    data['Date'] = data['Date'].astype(int)

  if date_format == 'C':
    data['Date'] = pd.to_datetime(date['Date'], format = "%Y/%j")
    data['Date'] = data['Date'].astype(int)

  return data

  data = date_formatting(data)

p = len(stattion_p)
out = pd.DataFrame(columns = variables)

for q in range(0, p):
  inst = data[index_variable == stattion_p[q]]
  inst['Station'] == stattion_n[q]
  inst.reset_index(inplace=True)

  out = pd.concat([out,inst])

# Sort the DataFrame by 'Station' and 'Date' columns
out.sort_values(by=['Station', 'Date'], inplace = True)

# Drop the index_variable column
out.drop(columns = index_variable, inplace = True)

# Print the full path of the input directory (input_dir) and the name of the dataset (d_name)
print(os.path.join(input_dir, d_name))

# Save the DataFrame to a new CSV file with a different name
out.to_csv(os.path.join(input_dir, d_name.replace('.csv', 'inst.csv')), index=False)
