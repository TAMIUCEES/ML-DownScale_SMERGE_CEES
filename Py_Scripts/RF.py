# -*- coding: utf-8 -*-

!pip install tensorflow tensorflow_decision_forests

import os
import datetime
import subprocess
import numpy as np
import pandas as pd
import xarray as xr
import seaborn as sns
import tensorflow as tf
import matplotlib.pyplot as plt
from contextlib import redirect_stdout
import tensorflow_decision_forests as forest
from tensorflow.python.client import device_lib

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

print(device_lib.list_local_devices())


def plot_tfdf_importances(inspector: forest.inspector.AbstractInspector, importance_type: str, fcn_name: str):
    scoredate = pd.DataFrame(columns=['fcn_name', 'scores'])
    try:
        importances = inspector.variable_importances()[importance_type]
    except KeyError:
        raise ValueError(f"Unknown importance type: {importance_type}")

    # Setting the labels for the variable importance plot
    plt.xlabel(importance_type)
    plt.title("Variable Importance")
    scoredate['fcn_name'] = names
    scoredate['scores'] = scores

    # Saving the variable importance data and plot
    scoredate.to_csv(name.replace('.png', '.csv'), index=False)
    plt.savefig(name)
    plt.show()

# Configuring the task type for the decision forest
task = forest.keras.Task.REGRESSION

name = [input("Enter the name of the dataset: ")]
home_directory = input("Enter the home directory where the datasets are located: ")
test_dataset_name = input("Enter the name of the testing dataset (including file extensions): ")
test_file = os.path.join(home_directory, test_dataset_name)

while not os.path.exists(test_file):
  print("The specified testing file does not exist. Please enter the correct dataset name.")
  test_dataset_name = input("Enter the name of the testing dataset (including file extension): ")
  test_file = os.path.join(home_directory, test_dataset_name)


train_dataset_name =  input("Enter the name of the training dataset (including file extension): ")
train_file = os.path.join(home_directory, train_dataset_name)

while not os.path.exists(train_file):
  print("The specified training file does not exist. Please enter the correct dataset name.")
  train_dataset_name = input("Enter the name of the training dataset (including file extension): ")
  train_file = os.path.join(home_directory, train_dataset_name)


variables_list_name = input("Enter the name of the variables list (make sure the file is in the text file format): ")
variables_file = os.path.join(home_directory, variables_list_name)

while not os.path.exists(variables_file):
  variables_list_name = input("The variable list txt was not found, it should be in the home directory. Try again.")
  variables_file = os.path.join(home_directory, variables_list_name)


text_file = open(variables_file, "r")
variables = text_file.read().split(',')
test_data = pd.read_csv(test_file)
test_data = test_data.loc[:, variables]


def process_object_columns(dataframe):
  def get_object_columns(df):
    return list(df.select_dtypes(include=['object']).columns)

  # Function to get object type columns
  object_columns = get_object_columns(dataframe)
  print("Object type columns:", object_columns)

  # Removing columns with 'object' dtype
  df_without_objects = dataframe.drop(object_columns, axis=1)

  # Creating separate variables for object type columns with their respective names
  for col in object_columns:
    globals()[f"{col}"] = dataframe[col]

  # Printing separate variables
  for col in object_columns:
    print(f"{col}:")
    print(globals()[f"{col}"])

  # Returning the original DataFrame without object type columns
  return df_without_objects


index_variable = input("Enter the index variable from the list of variables: ")
test_data = process_object_columns(test_data)

print(test_data)



date = pd.read_csv(test_file, usecols=['Date'])

def date_formatting(dataframe2):
  # Processing 'Date' column for testing
  date_format = input('If file use "%m/%d/%Y" type: A, if "%Y/%m/%d" type: B, else "%Y/%j" type: C: ')
  # date_column = dataframe2[column_name]
  while date_format != 'A' and date_format != 'B' and date_format != 'C':
    date_format = input('Input ERROR. If file use "%m/%d/%Y" type: A, if "%Y/%m/%d" type: B, else if "%Y/%j" type: C: ')

  if date_format == 'A':
    # date_format = '%m%d%Y
    dataframe2['Date'] = pd.to_datetime(date['Date'], format="%m/%d/%Y")
    dataframe2['Date'] = dataframe2['Date'].astype(int)

  if  date_format == 'B':
    # date_format = '%Y/%m/%d'
    dataframe2['Date'] = pd.to_datetime(date['Date'], format="%Y/%m/%d")
    dataframe2['Date'] = dataframe2['Date'].astype(int)

  if date_format == 'C':
    # date_format = '%Y%j'
    dataframe2['Date'] = pd.to_datetime(date['Date'], format="%Y/%j")
    dataframe2['Date'] = dataframe2['Date'].astype(int)

  #else:
      #print("Data format not recognized. Make sure your data is formatted as "%m%d%Y", "%Y%m%d", or "%Y%j")
    # date_format = 0
  return dataframe2

test_data = date_formatting(test_data)


# Separating target variable (dependent) from the initial variables (independent).
target_variable = input("Write the name of the target variable to extract it from the list of variables: ")
variables = test_data.columns.tolist()

while target_variable in variables:
  variables.remove(target_variable)

y_test = test_data[target_variable]
x_test = test_data[variables]


train_data = date_formatting(train_data)

# Defining x_train and y_train
x_train = train_data[variables]
y_train = train_data[target_variable]

k = 10
tuner = forest.tuner.RandomSearch(num_trials=9 * 10, use_predefined_hps=True)
model_img_file = str(name) + "model.png"
n = test_data.shape[0]

## Initializing output array
out = np.empty(shape=(0, 1))

## Creating an empty DataFrame with specific columns
x = pd.DataFrame(columns = test_data.columns)

print(test_data.columns)


# Configuring the random forest model
model = forest.keras.RandomForestModel(
        verbose=1,
        tuner=tuner,
        num_trees=1100,
        allow_na_conditions=True,
        task=task,
        winner_take_all=True,
        categorical_algorithm='CART',
        honest=True,
        honest_fixed_separation=True,
        honest_ratio_leaf_examples=0.75,
        bootstrap_size_ratio=1.05,
        adapt_bootstrap_size_ratio_for_maximum_training_duration=True,
        keep_non_leaf_label_distribution=False,
        max_depth=9)

# Creating a TensorFlow dataset for training
train_ds = forest.keras.pd_dataframe_to_tf_dataset(train_data, label= target_variable, task=task)

# Compiling and training the model
model.compile(metrics=["mae"])
model.fit(train_ds)

# Creating a TensorFlow dataset for testing
test_ds = forest.keras.pd_dataframe_to_tf_dataset(test_data.drop(target_variable), task=task)

# Extracting relevant data for output processing
out_data = test_data

"""- Obtaining the prediction with the trained model."""

pred = model.predict(test_ds, verbose=1)
out = np.vstack([out, pred])
x = pd.concat([x, out_data])


with open(name + "sum_model.txt", "w") as txt_file:
  with redirect_stdout(txt_file):
    model.summary()


with open(name + "model.html", "w") as html_file:
  html_file.write(forest.model_plotter.plot_model(model, tree_idx=0, max_depth=10))


model.reset_states()


x['ML_'] = out
df_out = pd.DataFrame(pred, columns=['ML_'])
x['NDVI'] = ndvi
x['Date'] = dates
x[index_variable] = test_page

x.to_csv(name + ".csv", index=False)

## Generating variable importance plots
inspector = model.make_inspector()
plot_tfdf_importances(inspector=inspector, importance_type='INV_MEAN_MIN_DEPTH',  fcn_name= str(name) + "_IMMD.png")
plot_tfdf_importances(inspector=inspector, importance_type='NUM_NODES', fcn_name= str(name) + "_NumNodes.png")
