import os
import datetime
import string
import warnings
import sys
import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from natsort import natsorted

def train_test(data, out, index, n):
  df_train, df_test = train_test_split(data, test_size = 0.30, random_state = 42)
  if verify == 'Y' and verify2 == 'N':
    v = data[data['Verifier'] != pd.NA]
    ver = v[index].tolist()
    inst = df_train.loc[df_train[index].isin(ver)]
    df_train = df_train.loc[~df_train[index].isin(ver)]
    df_test = pd.concat([df_test, inst])
    df_train.to_csv(out, n+'_train.csv', index = False)
    df_test.to_csv(out, n+'_test.csv', index = False)
  if verify == 'Y' and verify2 == 'Y':
    df_train.to_csv(os.path.join(out, n+'_train.csv'))
    df_test.to_csv(os.path.join(out, n+'_test.csv'))

# Initalizes parameters, generates data, and cleans document
class day_data:
  def __init__(self, tag, dates, index, zero_null, fill_value, input_dir, if_below, na_valid):
    # Initalizes the parameters
    self.tag = tag
    self.dates = dates
    self.zero_null = zero_null
    self.fill_value = fill_value
    self.input_dir = input_dir
    self.index = index
    self.if_below = if_below
    self.na_valid = na_valid

  def data_gen(self):
    # Number of dates
    num_dates = len(date)
    # List will be used to save files
    file_list = []
    for f in os.listdir(self.input_dir):
      # Finds if file is a CSV file and has a tag/prefix
      if f.endswith(".csv") and f.startswith(self.tag):
        # Adds file to file_list
        file_list.append(os.path.join(self.input_dir, f))
    # Sorts files from file list
    file_list = natsorted(file_list)
    # Creates DataFrame, columns: index, tag, and 'Date'
    total_data = pd.DataFrame(columns=[self.index, self.tag, 'Date']).set_index(self.index)
    for k in range(0, num_dates):
      current = pd.DataFrame(columns=[self.index, self.tag, 'Date']).set_index(self.index)
      current[self.tag] = pd.read_csv(file_list[k], usecols = ["MEAN", self.index]).set_index(self.index)
      current['Date'] = self.dates[k]
      total_data = pd.concat([total_data, current])
    self.df = total_data

  def data_clean(self):
    self.df.set_index('Date', append=True, inplace = True)
    # Checks if the value is null
    if self.zero_null == True:
      self.df = self.df[self.df[self.tag] >= 0]
    # Checks if there is a value
    if self.fill_value is not None:
      self.df = self.df[(self.df[self.tag]) != self.fill_value]
      if self.if_below:
          self.df = self.df[(self.df[self.tag]) < self.fill_value]
      if not self.if_below:
          self.df = self.df[(self.df[self.tag]) > self.fill_value]
    # Checks if the value is not valid
    if self.na_valid is not True:
        self.df.dropna(inplace = True)

# Creates an empty DataFrame and static variable is opened
def static_gen(path, date, index, config):
    # Reads CSV file path
    static = pd.read_csv(path)
    # Number of dates
    num_dates = len(date)
    # Creates a DataFrame column named 'Date' and index (user input)
    total_data = pd.DataFrame(columns=[index, 'Date']).set_index(index)

    for k in range(0, num_dates):
      current = static.set_index(index)
      # Assigns a value of the current date from date[k] in the 'Date' column
      current['Date'] = date[k]
      # Added to total_data DataFrame
      total_data = pd.concat([total_data, current])

    for s in config:
        if config[s]:
            # Filters total_data to keep only the column values greater than 0
            total_data = total_data[total_data[s] >= 0]
    # Total_data is set to 'Date' and adds the existing index
    total_data.set_index('Date', append=True, inplace = True)
    # Drops rows that contain missing values from the total_data column
    total_data.dropna(inplace=True)
    # Returns the results from the total_data DataFrame
    return total_data

def dynamic_gen(d_name, input_d, dex, date, dynamic):
    # List created
    all_data_list = []
    for d in dynamic:
        print(d)
        current = day_data(d[0],date, dex, d[2], d[1], input_d, d[3], d[4])
        # Generates and cleans data
        current.data_gen()
        current.data_clean()
        # Current is appended to the list
        all_data_list.append(current)
    # Updated list
    return all_data_list

def combine_data(static, dynamic):
    for dy in dynamic:
        static[dy.tag] = dy.df[dy.tag]
    return static

# Read list of dates from file
text_file = open("dates.txt","r")

# Checks if file exists
while not os.path.exists("dates.txt"):
  print('The date list txt was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  text_file = open("dates.txt", "r")

# Dates are now used as a list
date = text_file.read().split(',')

# Read the list of dates from the file
static_file = open("static.csv", "r")

# Checks if the file exists
while not os.path.exists("static.csv"):
  print('The static_config text was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  static_file = open("static.csv", "r")
# Dates are now used as a list
static_config = {}
with static_file as f:
    for line in f:
##       (key, val) = line.split()
       key = line.split()
       val = False
##       static_config[key] = bool(val=='True')

# Read list of dates from file
dynamic_file = open("dynamic_config.txt","r")

# Checks if file exists
while not os.path.exists("dynamic_config.txt"):
  print('The dynamic_config text was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  dynamic_file = open("dynamic_config.txt", "r")

# Dates are now used as a list
with dynamic_file as file:
    dynamic_config = [[x for x in line.split(' ')] for line in file]
for d in dynamic_config:
    try:
        # Tries to convert the index to float value
        d[1] = float(d[1])
    except:
        # If it does not convert, then set to 'None'
        d[1] = None
    # Checks if indices are equal to '1'
    d[2] = bool(d[2]=='1')
    d[3] = bool(d[3]=='1')
    d[4] = d[4].replace('\n', '')
    d[4] = bool(d[4]=='1')

# Prints the static and dynamic configurations
print(static_config)
print(dynamic_config)

# Set data product name
d_name = input("Enter the name of the dataset: ")

# Set the input directory
input_d = input("Enter the input directory: ")

# Set the output directory
output_d = input("Enter the output directory: ")

# Set static data csv path
static_path = input("Enter the path to static data (include file and file exit): ")

# Asks for verification of data and index number
verify = input('Do you have verification data? Y/N: ')
verify2 = input('Is the verification complete? Y/N: ')
dex = input("Input the name of the index variable: ")

dyn = dynamic_gen(d_name, input_d, dex,  date, dynamic_config)
untrim_data = combine_data(static, dyn)
train_test(untrim_data, output_d, dex, d_name)
