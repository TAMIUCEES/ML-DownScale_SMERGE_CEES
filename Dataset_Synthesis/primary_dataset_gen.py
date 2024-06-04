# -*- coding: utf-8 -*-
"""primary_dataset_gen.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1EuWsRDvbe0UCVAvey_1PjqIo5nWD9gi5

# Introduction

The **primary_dataset_genV2** program uses various functions to compile data needed for files. The **Data_gen** function generates the values needed for variables using the dates given in the file. When generating these values there is a need to clean up the data or polish it to make a concise and more accurate reading of the data. This is done by using the **data_clean** funcion. In the **static_gen** function it is used to find the current/recent data for the date and variables needed. The **combine_data** function updated the *static* dictionary.

---

The following libraries are imported to allow the code to be run:

- **os** - The directory service provides the ability to create and remove directory folders, gather data, change and find the current directory, and provide a means for users and the operating system to interact with each other.
- **datetime** - Manipulates the data between dates and time.
- **string** - Allows strings or data to be split when needed.
- **warnings** - Informs the user of the state of the code or where an error has occurred.
- **sys** - Provides a way to manipulate the runtime of the program by using certain parameters and functions.
- **Pandas** - Is a tool for modeling, analyzing, and manipulating data sets.
> For more information visit: https://www.geeksforgeeks.org/introduction-to-pandas-in-python/#
- **NumPy** - Supports analysis and can perform operations on a large set of data.
> For more information visit: https://numpy.org/doc/stable/user/whatisnumpy.html
- **re** - regular expression (or **re**) specifies a set of strings, where a particular string will match the given regular expression.
> For more information visit:  https://docs.python.org/3/library/re.html



**sklearn.model_selection**

---

- **train_test_split** - Splits arrays into random train and test subsets which provides valid results.

**natsort**

---

- **natsorted** - Sorts strings and numbers separately.
"""

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

"""**train_test**

---
- Using the values **data**, **out**, **n**, and **index** the function is able to test and train the data to find the correct data in the file.

  - If verify equals 'Y' and verify2 equals 'N', then the first *if statement* is ran. This segment sets the column 'Verifier' as a missing value, which uses **index** to retrieve values from the column subset, converting them into a list.
  
    Using the rows from *df_train*, the **index** is used to list the new values for the columns, these values are assigned to *inst*.
    
     These rows are later removed from *df_train* and is appended to *df_test*, which can then create a CSV file and use the **out** and **n** parameters to create the file name.

  - If verify equals 'Y' and verify2 equals 'Y', then the second *if statement* is ran.
  
    Unlike the other segment, *df_train* and *df_test* are converted into CSV files with their names based on the values of **out** and **n** variables.
"""

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

"""# Class *day_data*
The class *day_data* contains the functions **____ init ____**, **data_gen**, and **data_clean**, which will be utilized later in the program.

**__ init __**

---
- The **__ init __** function is responsible for initializing all the variables in the class, which are subsequently utilized in the **data_gen** and **data_clean** function.

**data_gen**

---
- The **data_gen** function takes multiple CSV files and generates a single DataFrame. It starts by extracting the number of dates from the *date* column in each CSV file using the *num_dates* attribute. If the file is a CSV with a tag, it is added to a list of new file paths. The file list is then sorted, and an empty DataFrame, **total_data**, is created with the columns *index, tag*, and *'Date'*.

- Next, another empty DataFrame, **current**, is created with the same columns as **total_data**. The CSV file at index *k* in the *file_list* is read, and only the "MEAN" column is selected. The 'Date' column in the **current** DataFrame is set to the corresponding date from the *dates* list.

- Finally, the **current** DataFrame is concatenated with the **total_data** DataFrame, and the resulting DataFrame is assigned to the *self.df* attribute.

- Overall, this function generates data by reading CSV files according to their directory and adds them into the DataFrame **total_data** with their corresponding dates.

**data_clean**

---


- This function cleans several data operations in a DataFrame. To do so, the index is set to the column 'Date', append is true to keep the value the same throughout the code, and inplace is true so that it can modify the DataFrame.

- The **data_clean** function streamlines multiple data operations in a DataFrame. It sets the index to the 'Date' column, keeps the value consistent throughout the code by setting append to true, and modifies the DataFrame directly by setting inplace to True.
  - When the *zero_null* attribute is set to True, the DataFrame will only retain rows where the values in the column specified  by the tag are greater than or equal to zero.
  - When the *fill_value* is '*not None*', the DataFrame will be filtered to remove rows where the column value, as determined by the tag, is equal to the specified *fill_value*.
> - If the *if_below* attribute is True, the DataFrame is filtered from the row where the *fill_values* is less than the value.
> - If the *if_below* attribute is False, the DataFrame is filtered where the value is greater than the *fill_value*.
  - When the *na_valid* attribute is False, the DataFrame will drop all rows containing missing values (NaN). This operation modifies the DataFrame in place.
"""

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

"""**static_gen**

---

- The user input for the static path is read and stored in the *static* variable. Next, the number of dates is saved in the *num_dates* variable. An empty DataFrame called **total_data** is created with columns *index* and *'Dates'*. The *index* is set to the name of the index variable provided by the user.

- In a loop, the code iterates over each data and sets the static index to *index*, assigning it to the variable *current*. The program then attaches a new column labeled 'Date' to the *current* column and allocates a value to all rows. **Total_data** is updated by concatenating it with *current*, appending the data to the current date. This iteration successfully combines the information.

- After the interaction is complete, a new iteration is created in the *config* dictionary which checks if the values are true. If true, the **total_data** variable is filtered by keeping only rows where the column value is greater than or equal to 0. Lastly, the index of **total_data** is set to include 'Date' as a second index level and drops any rows with missing values. Finally, **total_data** is returned.
"""

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
    # Total_data is set to 'Date' and adds existing index
    total_data.set_index('Date', append=True, inplace = True)
    # Drops rows that contain missing values from the total_data column
    total_data.dropna(inplace=True)
    # Returns the results from the total_data DataFrame
    return total_data

"""**dynamic_gen**

---

- Through the utilization of dynamic list elements, the program can employ the **day_data** class to conduct data generation and cleaning for every instance.

  Subsequently, these instances will be added and returned to the initially created empty *all_data_list* within the function.

- Using the elements of the current element *d* in the *dynamic* list, the line instantiates an object named *current* of the class **day_data**.

  The *current* object's *data_gen* method generates data, while its *data_clean* method cleans the generated data.
  
   The *current* object is then added to a list called *all_data_list*.
   
   Furthermore, the program returns the *all_data_list*, which includes all the processed **day_data** objects.
"""

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

"""**combine_data**

---

- The *dynamic* list elements are utilized to assign values to the *static* dictionary in the iteration process. Once the values are assigned, the *static* dictionary is returned and updated accordingly.
"""

def combine_data(static, dynamic):
    for dy in dynamic:
        static[dy.tag] = dy.df[dy.tag]
    return static

"""*text_file*

---


- The program will open and read the text file, "dates.txt". The contents of the file will be stored in the variable named *text_file*.

- The code performs two tasks simultaneously: running and checking for the existence of the file. In the event that the file is not found, the code engages the user in a prompt loop until a valid file is provided.

- The program proceeds to read the entire contents of the file, splitting it into a list of strings using the comma as the delimiter. The resultant list of strings is then stored in the variable *date*.
"""

# Read list of dates from file
text_file = open("dates.txt","r")

# Checks if file exists
while not os.path.exists("dates.txt"):
  print('The date list txt was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  text_file = open("dates.txt","r")

# Dates are now used as a list
date = text_file.read().split(',')

"""*static_file*

---


- The program will open and read the text file, "static_config.txt". The contents of the file will be stored in the variable titled *static_file*.

- The code performs two tasks simultaneously: running and checking for the existence of the file. If the file is not found, the code engages the user in a prompt loop until a valid file is provided.

- We initialize an empty dictionary, called *static_config*.

    Then, the *static_file* is iterated over for each line. Each line is split into two parts, *key* and *val*, respectively.
    A new key-value pair is then added to the *static_config* dictionary.
  
   The *bool(val=='True')* function is used to convert the string *val* to a boolean value. If *val* is equal to the string '*True*', it is converted to *True*. Otherwise, it is converted to *False*.

> **Note:**
 - The initial column of the file stores the name of the variables found in the "*static_config.txt*" file.
 - The second column verifies whether the static variable is empty; if so, it is deemed invalid and can be removed.
  - Within the file, the variables *Slope*, *Elevation* and *Aspect* must have uniform data. The *Aspect* variable is restricted from being '*0*' or lower, and as such, it is automatically assigned a value of **True**. If one of the three variables is incorrect, the data from the variables is invalid. The data must correspond with the three variables.
  - Additionally, for the variables *Clay*, *Sand*, and *Silt*, if one has a value of '*0*', the other two must adjust their values to maintain equilibrium. For instance, if *Sand* has a value of '*0*', then *Clay* would need to be approximately 60 percent, while *Silt* would be 40 percent, resulting in a balance of 100.
  - Rules for determining if a value is valid:
    - The value is considered **True**, if the value that is '0' or below is *invalid*, then set the input to '*1*'.
    - The value is considered **False**, if the value that is '0' or below is *valid*, then set the input to '*0*'.
"""

# Read list of dates from file
##static_file = open("static_config.txt","r")
static_file = open("static.csv", "r")
# Checks if file exists
##while not os.path.exists("static_config.txt"):
while not os.path.exists("static.csv"):
  print('The static_config txt was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
##  static_file = open("static_config.txt","r")
  static_file = open("static.csv", "r")
# Dates are now used as a list
static_config = {}
with static_file as f:
    for line in f:
##       (key, val) = line.split()
       key = line.split()
       val = False
##       static_config[key] = bool(val=='True')

"""*dynamic_file*

---


- The program will open and read the text file, "dynamic_config.txt". The contents of the file will be stored in the variable titled *dynamic_file*.

- The code performs two tasks simultaneously: running and checking for the existence of the file. If the file is not found, the code engages the user in a prompt loop until a valid file is provided.

- The file named *dynamic_file* is opened in read mode and assigned to the file object *file*. Next, each line in the file is split into a list of strings using whitespace as the delimiter. Finally, an iteration over each line in the file is performed, and the entire process is stored in *dynamic_config*.

  In the *dynamic_config*, the following sublists are iterated:
  - *d[1] = float(d[1])*: Changes the second element in the sublist to a float value.
    - When *d[1] = None*, the conversion fails and the second element is set to *None*.
  - *d[2] = bool([2] == '1')* : Converts the **third** element into a boolean value, depending on whether it's equal to the string *1*.
  - *d[3] = bool(d[3] == '1')* : Converts the **fourth** element to a boolean value, depending on whether it's equal to the string *1*.
  - *d[4] = d[4].replace('\n',* ' ' ) : In the fifth element, substitute all instances of the *\n,* string with a space character.

> **Note:**
  - The initial column of the file stores the name of the variables found in the "*dynamic_config.txt*" file.
  - The subsequent column in the file, named *fill_value*, holds a numeric value that, when applicable, represents the maximum value of the sample. If there is no *fill_value*, maintain the space.
  - Within the binary section of the columns:
    - The first column checks whether the value is equal to 0 or negative.
      - If it is, then the value is considered *Null* and assigned a value of '*0*'.
      - If the value is not *Null*, then it is assigned a value of '*1*'.
    - The second column denotes whether the value is higher or lower than the *fill_value*. The ***valid*** values are the ones below the *fill_value*.
      Depending on the value, the following applies:
      - If the value is higher than the *fill_value*, then it is **True**, and the input is set to '*1*'.
      - If the value is lower than the *fill_value*, then it is **False**, and the input is set to '*0*'.
    - The final column verifies the validity of the value by checking for *NA* values.
      - If the file value is retained, it is considered **False**, and the input is set to '*0*'.
      - If the file value is removed, it is considered **True**, and the input is set to '*1*'.
"""

# Read list of dates from file
dynamic_file = open("dynamic_config.txt","r")

# Checks if file exists
while not os.path.exists("dynamic_config.txt"):
  print('The dynamic_config txt was not found. It should be in the same directory as the .py script. ')
  n = input("Press enter to try again.")
  dynamic_file = open("dynamic_config.txt","r")

# Dates are now used as a list
with dynamic_file as file:
    dynamic_config = [[x for x in line.split(' ')] for line in file]
for d in dynamic_config:
    try:
        # Tries to convert index to float value
        d[1] = float(d[1])
    except:
        # If does not convert, then set to 'None'
        d[1] = None
    # Checks if indices is equal to '1'
    d[2] = bool(d[2]=='1')
    d[3] = bool(d[3]=='1')
    d[4] = d[4].replace('\n', '')
    d[4] = bool(d[4]=='1')

# Prints the static and dynamic configurations
print(static_config)
####print(dynamic_config)

"""- The user will be asked to input the data product name, the input directory, the output directory, and the static data csv path."""

# Set data product name
d_name = input("Enter the name of the dataset: ")

# Set the input directory
input_d = input("Enter the input directory: ")

# Set the ouput directory
output_d = input("Enter the output directory: ")

# Set static data csv path
static_path = input("Enter the path to static data (include file and file exit): ")

"""- Provide either 'Y' or 'N' to indicate whether the verification data is available and if the data is complete.

- Furthermore, to execute the program, the user is required to provide the index variable.
"""

# Asks for verification of data and index number

verify = input('Do you have verification data? Y/N: ')
verify2 = input('Is the verification complete? Y/N: ')

dex = input("Input the name of the index variable: ")

"""- The function *static* will take four arguments:
  - *static_path* : The directory path containing all static files.
  - *date* : The current date.
  - *dex* : The index variable.
  - *static_config* : Dictionary that stores key-value pairs.
"""

static = static_gen(static_path, date, dex, static_config)

"""- The variable *dyn* takes five arguments:
  - *d_name* : The name of the dataset
  - *input_d* : The input directory.
  - *dex* : The index variable.
  - *date* : The current date.
  - *dynamic_config* : Comprises a series of lists, where each of the lists corresponds to a line from *dynamic_file*.
"""

dyn = dynamic_gen(d_name, input_d, dex,  date, dynamic_config)

"""- The variable *untrim_data* combines the data from the *static* and *dyn* variables that were previously initialized."""

untrim_data = combine_data(static, dyn)

"""- Lastly, the data is tested using these four arguments:
  - *untrim_data* : Combined data from *static* and *dyn*.
  - *output_d* : The output directory.
  - *dex* : The index variable.
  - *d_name* : The name of the dataset.
"""

train_test(untrim_data, output_d, dex, d_name)