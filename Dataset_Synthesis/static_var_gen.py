import os
import datetime
import modin.pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string
import warnings
import sys
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Constructing home paths
home = input("Enter the home directory where the datasets are located: ")

# Asking for the name of the training dataset and constructing the full path
static_dataset_name = input("Enter the name of the dataset containing static data (including file extension): ")
static_file = os.path.join(home, static_dataset_name)

while not os.path.exists(static_file):
  print(static_file + "does not exist. Please enter the correct dataset name. ")
  static_dataset_name = input("Enter the name of the dataset containing static data (including file extensions): ")
  static_file = os.path.join(home, static_dataset_name)

index_var = input("Enter the index variable from the list of variables: ")

i = ''
static_vars = [index_var]

# Reads static_file
data = pd.read_csv(static_file)
print('These are the column names of the given table, which columns are the static variables. Type "exit" when finished. The Pagename column will automatically be added. ')
print(data.columns)
while i != 'exit':
  i = input(': ')
  if i != 'exit':
    static_vars.appen(i)

# Constructing file name
name = input("Enter the name of the dataset (NOT including file extension): ")
static = data[static_vars]
static.to_csv(os.path.join(home, name + '_static.csv'), index = False)
