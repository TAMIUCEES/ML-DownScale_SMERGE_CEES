# -*- coding: utf-8 -*-
"""RF.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CqY5etakuhzSDQck4Wa-0Scf-f4OXuUu

# Introduction

The Machine Learning technique used will be Random Forest (RF). Random Forest is a machine learning algorithm that generates a single prediction by collecting the output of multiple decision trees. For this notebook, we are working with Random Forest Regressor.

> **Disclaimer:** *Random Forest* **only** runs in Linux.

---

Before running the code, first check if tensorflow is in the library. If it is not, install using the given code so we may proceed in using tensorflow_decision_forests in our code.
"""

!pip install tensorflow tensorflow_decision_forests

"""The following libraries will be imported to be able to run the code.

---

TensorFlow is a library most commonly used for Random Forest as it trains, runs, and interprets decision forest models such as RF.

**tensorflow-python-client**

---

- **device_lib** - Provides access to TensorFlow device library. The library can be used to designate which device to use for a specific operation.

**tensorflow**

---
- **tensorflow**
  > For more information visit: https://www.tensorflow.org/guide/basics
- **tensorflow_decision_forests** - TensorFlow Decision Forests is a library for training, running, and interpreting decision forest models in TensorFlow.
  > For more information visit: https://www.tensorflow.org/decision_forests


**contextlib**

---

- **redirect_stdout** - Redirects the output of a program to a different file, which can be helpful for troubleshooting problems. redirect_stdout is helpful with debugging.
  > For more information visit: https://docs.python.org/3/library/contextlib.html


---

Additionally, the packages of *datetime* and *subprocess*, as well as *os*, are imported.
- **datetime** - The Python Datetime module provides classes for working with dates and times.
  > For more information visit: https://www.geeksforgeeks.org/python-datetime-module/#
- **subprocess** - The Python Subprocess module is used to create new processes, as well as run new code and applications.
  > For more information visit: https://docs.python.org/3/library/subprocess.html
- **os** - Os is used to concatenate path components with exactly one directory separator "/", and create one path.
  > For more information visit: https://www.geeksforgeeks.org/python-os-path-join-method/

The other packages contain python features such as *pandas* and *numpy*. Furthermore, we included the packages of *xarray* and *seaborn* that will be imported as well.
  > See the links below for more information on the packages:
  - **Pandas** - https://pandas.pydata.org/docs/user_guide/index.html
  - **NumPy** - https://numpy.org/doc/stable/

- **xarray** - xarray is an open-source Python package that makes working with labeled multi-dimensional arrays more efficient and easier to comprehend.
  > For more information visit: https://xarray.pydata.org/en/v0.12.3/#:~:text=xarray%20(formerly%20xray)%20is%20an,simple%2C%20efficient%2C%20and%20fun!
- **seaborn** - Seaborn is a Python library for creating statistical graphics.
  > For more information visit: https://seaborn.pydata.org/tutorial/introduction.html
"""

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

"""- Setting environment variables for TensorFlow configuration.
  - *'TF_ENABLE_ONEDNN_OPTS'*, dictates whether TensorFlow will utilize Intel's oneDNN library for CPU inference. To disable oneDNN, set '*TF_ENABLE_ONEDNN_OPTS*' to '*0*'.
  - *'CUDA_VISIBLE_DEVICES'*, can be used to specify which GPUs are visible to a CUDA application. Setting the environment variable to '*0*' would mean that the CUDA application would only see GPU '*0*'.
"""

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

"""- Setting the display options for pandas.
  - '*display.max_columns*' sets the maximum number of columns to display 500.
  - '*display.width*' indicates that columns will not be truncated if they exceed 1000 characters when the DataFrame is printed.
"""

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

"""- Checking for available local devices in TensorFlow, including both CPU and GPU devices. This is useful for confirming GPU usage."""

print(device_lib.list_local_devices())

"""- Defining a function to plot variable importances for TensorFlow Decision Forests"""

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

"""- The user will then be asked to input the name of the dataset.

  An example would be:
  > *Enter the name of the dataset:* **ARM**
"""

name = [input("Enter the name of the dataset: ")]

"""- Paths will be constructed based on the zone and name.

  An example would be:
  > *Enter the home directory where the datasets are located:* **/content/ARM/**
"""

home_directory = input("Enter the home directory where the datasets are located: ")

"""- Input the name of the testing dataset, this will be used to construct the full path.

  An example would be:
  > *Enter the name of the testing dataset:* **Era1_2ARM_400m_dataV1_test.csv**

- While the code is running it will also be checking if the testing file exists. If the file does not exist, then the code will prompt the user until a valid file is provided.
"""

test_dataset_name = input("Enter the name of the testing dataset (including file extensions): ")

test_file = os.path.join(home_directory, test_dataset_name)

while not os.path.exists(test_file):
  print("The specified testing file does not exist. Please enter the correct dataset name.")
  test_dataset_name = input("Enter the name of the testing dataset (including file extension): ")
  test_file = os.path.join(home_directory, test_dataset_name)

"""- Input the name of the training dataset, this will be used to construct the full path.

  An example would be:
  > *Enter the name of the training dataset:* **Era1_2ARM_400m_dataV1_train.csv**

- While the code is running it will also be checking if the training file exists. If the file does not exist, then the code will prompt the user until a valid file is provided.
"""

train_dataset_name =  input("Enter the name of the training dataset (including file extension): ")

train_file = os.path.join(home_directory, train_dataset_name)

while not os.path.exists(train_file):
  print("The specified training file does not exist. Please enter the correct dataset name.")
  train_dataset_name = input("Enter the name of the training dataset (including file extension): ")
  train_file = os.path.join(home_directory, train_dataset_name)

"""# Variables
- Prior to exporting testing and training data, it is necessary to create and upload a text file list (comma-separated values) containing the names of all the variables (including the target variable). The text file must be saved in the same folder as the training and testing files.

- Given that the variable names can vary depending on the user's data, it is more convenient to create a separate file with the variable names and then adjust them to the code.

- An example of the list of variables woud be:

  > *PageName*, *Clay*, *Sand*, *Silt*, *Elevation*, *Slope*, *Ascept*, *NDVI*, *SMERGE*
"""

variables_list_name = input("Enter the name of the variables list (make sure the file is in the text file format): ")
variables_file = os.path.join(home_directory, variables_list_name)

while not os.path.exists(variables_file):
  variables_list_name = input("The variable list txt was not found, it should be in the home directory. Try again.")
  variables_file = os.path.join(home_directory, variables_list_name)

text_file = open(variables_file, "r")
variables = text_file.read().split(',')

"""# Testing Data

- First, we created a variable called *test_data* to read our testing data, then using *variables* from the previous section we will save all of the data into *test_data*. Testing data is going to help us measure the performance of our model.

"""

test_data = pd.read_csv(test_file)
test_data = test_data.loc[:, variables]

"""  > **Warning:** Before separating the predictor variables from the target variable, we created a filter to make sure the data saved will be compatible with Random Forest. This machine learning module is created to deal with  numerical values.

- The following code will remove all the *object type* column variables from the testing set, create new variables that will hold those columns, and eventually create a list of all of the columns that will be removed.
  - **Object type** columns variables refers to the columns that contain a combination of strings, letters, and numbers. Random Forest is compatible with numeric values.

- As a result, prior to applying the testing set to the Random Forest model, we must eliminate those columns.

- However, if you want to keep that variable as part of your variables for the model, make sure to format that column beforehand for both testing and training sets.

- In our case, we dealt with a variable called *PageName*.
  - **PageName** - This variable holds string values and can not be used in our model. However, the variable holds the position grids of the data by coordinates with letters and numbers such as C3.

- Although **PageName** was not part of the Random Forest model predictions, it was saved in a variable separately so that it could be added back into the final prediction output. The variable will be called *index variable*.
If this is the case for you, and you want to save your data to place back into the output, you will be able to use the variables that this section will create. Otherwise, if you are just planning to remove them, you can just run this section and move on to the next one.

"""

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

"""- Input the name of the index variable, which will be integrated in the output dataframe."""

index_variable = input("Enter the index variable from the list of variables: ")

test_data = process_object_columns(test_data)

"""- After removing the object type columns, this is how the new test data looks like:"""

print(test_data)

"""- The next step is to create a variable that holds the date column.
  - Since the *date* column is a component of our predictor variables, we must format its numerical values to a value that Random Forest can interpret as a date, rather than just a number. However, before formatting the *date* column we create this **date** variable to preserve its original format and then insert it back into the output frame. The date format thatn can be taken can be found in the **Date Formatting** section.
"""

date = pd.read_csv(test_file, usecols=['Date'])

"""# Date Formatting

- For regression models it is important to follow the required formatting to make sure to have a high performance. This section will change the date format to a *to_datetime* format which works better with machine learning regression models. Therefore, there will be a date formatting for both testing and training sets.
> **Note:** This section only allows three types of date formats: "%m/%d/%Y", "%Y/%m/%d", and "%Y/%j". If you are using another type of format make sure to change it to one of those formats beforehand.

>
"""

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

"""- Lastly, to get the testing data ready, you need to separate the predictor variables from the target variable."""

# Separating target variable (dependent) from the initial variables (independent).
target_variable = input("Write the name of the target variable to extract it from the list of variables: ")
variables = test_data.columns.tolist()

while target_variable in variables:
  variables.remove(target_variable)

y_test = test_data[target_variable]
x_test = test_data[variables]

"""# Training Data

- First, we create a variable called *train_data* to read our training data. Then, using the *variables* from the previous section, we save all of the data into *train_data*. The training data will be used to create our model and make it able to create predictions.
  > **Note:** Since we already removed the object type columns in a previous section we will use *variables* from the **Variables** section to retrieve just the numerical columns values and define **x_train**. Additionally, we will use **target_variable** from testing data to also define **y_train** in the training data.
"""

train_data = pd.read_csv(train_file)

"""- Prior to defining the predictor variables (**x_train**) and target variable (**y_train**) for training, we must also format the date for the training data.
  - To do this, we will use the same function that we used in the **Date Formatting** section.
"""

train_data = date_formatting(train_data)

# Defining x_train and y_train
x_train = train_data[variables]
y_train = train_data[target_variable]

"""*Confirming for the model training*


---

- The *forest.tuner.RandomSearch* class is used to tune the hyperparameters of a random forest model. It operates by randomly sampling hyperparameter values from a specified distribution, and then evaluating the model's performance on a validation set for each sample.

- Two arguments are taken by the RandomSearch class:
  - **num_trials** - The number of random hyperparameter values to be evaluated.
    - 'k': number of trials in random search, and is multiplied to obtain the number of trials or *num_trials*.
  - **use_predefined_hps** - If *True*, automatically configures the hyperparameter space.

- For more information visit: https://www.tensorflow.org/decision_forests/api_docs/python/tfdf/tuner/RandomSearch

> **Note:**
Depending on the size and variance of the dataset, it may be necessary to increase the number of trials in random search. If the rows in the dataset are similar in range, then there is no need to change the number of trials. However, if the rows in the dataset are not similar in range, then it may be necessary to increase the number of trials.
"""

k = 10
tuner = forest.tuner.RandomSearch(num_trials=9 * 10, use_predefined_hps=True)
model_img_file = str(name) + "model.png"
n = test_data.shape[0]

## Initializing output array
out = np.empty(shape=(0, 1))

## Creating an empty DataFrame with specific columns
x = pd.DataFrame(columns = test_data.columns)

print(test_data.columns)

"""# Random Forest

Random Forest is a machine learning algorithm that aggregates the output of multiple decision trees to generate a single prediction. It is a versatile algorithm that can be used for both classification and regression problems. The benefits of Random Forest include its ability to reduce overfitting by accommodating the samples in the training data, and its flexibility in handling either classification or regression problems with high accuracy. Although Random Forest can be more complex than other ML algorithms, it provides more accurate predictions.
For this project,

The Random Forest attributes for the model are listed as follows:

---

- **verbose** - Enable verbose output
  - 0 = Silent
  - 1 = Small details
  - 2 = Full details
- **tuner** - If enabled, the tuner will automatically optimized the hyperparameters of the model.
- **num_trees** - The number of individual decision trees in a model can be increased to improve its accuracy, but this comes at the cost of increased model size, training speed, and inference latency.
- **allow_na_conditions** - If *true*, the tree training will evaluate conditions of the type "X is NA".
- **task** - Is used to define the kind of machine learning task that the model will be used to perform.
  - e.g. *classification, regression,* or *categorical_uplift*
- **winner_take_all** - Controls how classification trees vote.
  - If *true*, each tree will vote for a single class.
  - If *false*, each tree will vote for a distribution of classes.
- **categorical_algorithm** - There's a few ways to learn splits on categorical attributes.
  - ***CART*** - CART algorithm. The solution is precise for binary classification, regression, and ranking. It is approximated for multi-class classification.
  - ***ONE_HOT*** - One-hot encoding. This method is similar to converting each possible categorical value into a boolean feature, but it is more efficient. This method can be used for comparison purposes.
  - ***RANDOM*** - The best splits among a set of random candidates are chosen. The solution can be seen as an approximation of the CART algorithm.
- **honest** - In honest trees, different training examples are used to determine the tree's structure and leaf values. This regularization technique sacrifices examples in exchange for more accurate bias estimates.
- **honest_fixed_separation** - For honest trees only.
  - If *true*, a new random separation is generated for each tree.
  - If *false*, the same separation is used for all the trees.
- **honest_ratio_leaf_examples** - For honest trees only. A ratio of examples is used to determine the leaf values.
- **bootstrap_size_ratio** - The number of examples used to train each tree, expressed as a fraction of the size of the training dataset.
- **adapt_bootstrap_size_ratio_for_maximum_training_duration** - Determine how the maximum training time is applied.
  - If *true*, adjust the size of the sampled dataset used to train each tree so that num_trees will train within maximum_training_duration.
  - If *false*, the training will cease when the time limit is reached.
- **keep_non_leaf_label_distribution** - Controls whether to keep the value of nodes that are not leaves in a tree model. This information is not used when the model is serving predictions, but it can be used for model interpretation and hyperparameter tuning.
- **max_depth** - Maximum depth of the tree.

>For more information visit: https://www.tensorflow.org/decision_forests/api_docs/python/tfdf/keras/RandomForestModel

*Configuring the Random Forest model*

---



The parameters that were used for Random Forest are inside the RandomForestModel function.
"""

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

"""- Generating a model summary to be written to a text file."""

with open(name + "sum_model.txt", "w") as txt_file:
  with redirect_stdout(txt_file):
    model.summary()

"""- The resulting plot of the model will be saved in an HTML file."""

with open(name + "model.html", "w") as html_file:
  html_file.write(forest.model_plotter.plot_model(model, tree_idx=0, max_depth=10))

"""- The states of all layers of the model will be resetted, if there is any."""

model.reset_states()

"""- To conclude, we will prepare the output dataframe, which will then be saved to a CSV file."""

x['ML_'] = out
df_out = pd.DataFrame(pred, columns=['ML_'])
x['NDVI'] = ndvi
x['Date'] = dates
x[index_variable] = test_page

x.to_csv(name + ".csv", index=False)

"""# Inverse Mean Minimum Depth (IMMD)

 The variable '*inspector*' is used to inspect the performace or features of the model. The TensorFlow framework uses functions such as inverse-mean-minimum-depth (IMMD) and number of nodes (num_nodes) to help understand how features are contributing to the model’s predictions. IMMD is used to calculate Random Forest sensitivity. The number of nodes controls the size and complexity of the trees in the forest. The greater the value, the more complex the trees, but it also results in higher accuracy. Both the IMMD and the number of nodes will be plotted and saved under two separate '.png' files.
"""

## Generating variable importance plots
inspector = model.make_inspector()
plot_tfdf_importances(inspector=inspector, importance_type='INV_MEAN_MIN_DEPTH',  fcn_name= str(name) + "_IMMD.png")
plot_tfdf_importances(inspector=inspector, importance_type='NUM_NODES', fcn_name= str(name) + "_NumNodes.png")