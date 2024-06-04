# -*- coding: utf-8 -*-

pip install shap
pip install os

import os
import shap
import pandas as pd
import numpy as np
from numpy import mean
from numpy import std
from sklearn import preprocessing
import matplotlib.pyplot as plt
from sklearn import datasets, ensemble
from sklearn.metrics import accuracy_score
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_error as mse

name = input("Enter the name of the dataset: ")
home_directory = input("Enter the home directory where the datasets are located: ")
test_dataset_name = input("Enter the name of the testing dataset (including file extensions): ")
test_file = os.path.join(home_directory, test_dataset_name)

while not os.path.exists(test_file):
  print("The specified training file does not exist. Enter the correct dataset name.")
  test_dataset_name = input("Enter the name of the testing dataset (including file extensions): ")
  test_file = os.path.join(home_directory, test_dataset_name)


train_dataset_name = input("Enter the name of the training dataset (including file extensions): ")
train_file = os.path.join(home_directory, train_dataset_name)

while not os.path.exists(train_file):
  print("The specified training file does not exist. Enter the correct dataset name.")
  train_dataset_name = input("Enter the name of the training dataset (including file extensions): ")
  train_file = os.path.join(home_directory, train_dataset_name)


variables_list_name = input("Enter the name of the variables list (make sure the file is in text file format): ")
variables_file = os.path.join(home_directory, variables_list_name)

while not os.path.exists(variables_file):
  variables_list_name = input("The variable list txt was not found, it should be in the home directory, try again. ")
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
ver = pd.read_csv(test_file, usecols=['Verifier'])

#Removing verifier column
test_data = test_data.drop("Verifier", axis=1)

def date_formatting(dataframe2):
    # Processing 'Date' column for testing
    date_format = input('If file uses "%m/%d/%Y" type: A, if "%Y/%m/%d" type: B, else "%Y/%j" type: C : ')
    #date_column = dataframe2[column_name]
    while date_format != 'A' and date_format != 'B' and date_format != 'C':

        date_format = input('Input ERROR. If file uses "%m/%d/%Y" type: A, if "%Y/%m/%d" type: B, else if "%Y/%j" type: C')

    if date_format == 'A':

        #date_format = '%m/%d/%Y'
        dataframe2['Date'] = pd.to_datetime(date['Date'], format="%m%d%Y")
        dataframe2['Date'] =  dataframe2['Date'].astype(int)

    if date_format == 'B':

        #date_format = '%Y/%m/%d'
        dataframe2['Date'] = pd.to_datetime(date['Date'], format = '%Y/%m/%d')
        dataframe2['Date'] =  dataframe2['Date'].astype(int)

    if date_format == 'C':

        #date_format = '%Y/%j'
        dataframe2['Date'] = pd.to_datetime(date['Date'], format="%Y/%j")
        dataframe2['Date'] =  dataframe2['Date'].astype(int)
    #else:
      #print("Data format not recognized. Make sure your data is formatted as %m%d%Y, %Y%m%d, or %Y%j")
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
train_data = pd.read_csv(train_file)
train_data = date_formatting(train_data)

#Defining x_train and y_train
x_train = train_data[variables]
y_train = train_data[target_variable]

params = {
    "n_estimators": 200,
    "max_depth": 10,
    "min_samples_split": 4,
    "learning_rate": 0.3,
    "loss": "squared_error",
    "verbose": 1
}

x_train_nu = x_train.to_numpy()
y_train_nu = y_train.to_numpy()
x_test_nu = x_test.to_numpy()


reg = ensemble.GradientBoostingRegressor(**params)
reg.fit(x_train, y_train.values.ravel())

MSE = mean_squared_error(y_test, reg.predict(x_test))
print("The mean squared error (MSE) on test set: {:.4f}".format(MSE))

predictions = reg.predict(x_test_nu)
test_data['Date'] = date
test_data['ML_'] = predictions
test_data['Verifier'] = ver
test_data[index_variable] = index_variable

# Saving the output dataframe to a CSV file
test_data.to_csv(name + ".csv", index=False)

# Generating variable importance plots
model = reg.fit(x_train, y_train)
X_sampled = x_train.sample(1000, random_state=10)

explainer = shap.Explainer(model, X_sampled)
shap_values = explainer(X_sampled)
number_variables = len(variables)
shap.plots.bar(shap_values, max_display=number_variables)

# Saving variable importance plot
mean_shap = np.abs(shap_values.values).mean(axis=0)
shap_pd = pd.DataFrame(mean_shap, index=X_sampled.columns).sort_values(by=[0], ascending=False)
shap_pd.to_csv(name[0] + '_SHAP.csv')
