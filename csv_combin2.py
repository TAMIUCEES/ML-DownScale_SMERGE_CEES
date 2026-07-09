import pandas as pd
import dask.dataframe as dd
import os
import sys

def merge_csv_files(directory_path, output_filename):
    # List to hold data from each CSV file
    dataframes = []

    # Loop through all files in the directory
    for filename in os.listdir(directory_path):
        if (filename.endswith('.csv')) & ('_shap' not in filename) & ('_params' not in filename) & (output_filename in filename) & ('_trials' not in filename) & ('tuning' not in filename):
            # Construct full file path
            file_path = os.path.join(directory_path, filename)
            # Read the CSV file and append it to the list
            df = pd.read_csv(file_path, engine='pyarrow')
            dataframes.append(df)

    # Concatenate all DataFrames in the list
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(combined_df)
    # Save the combined DataFrame to a new CSV file
    out_path = os.path.join(directory_path, output_filename + '.csv')
    dask_data = dd.from_pandas(combined_df, npartitions=16)
    dask_data.to_csv(out_path,index=False, single_file=True)
    #combined_df.to_csv(out_path, index=False)
    print(f"Combined CSV saved as {out_path}")
    return combined_df


directory_path = sys.argv[1]
output_filename = sys.argv[2]
# Example usage
# directory_path = r'\\geo06\share\State_Run\ALL\500v2\Torch\OK'  # Replace this with your directory path
# output_filename = r'\\geo06\share\State_Run\ALL\500v2\Torch\OK\Torch_OK_500v6.csv'  # Name of the output file
df = merge_csv_files(directory_path, output_filename)