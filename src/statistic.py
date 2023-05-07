import pandas as pd
import glob
import os

path = "../data"
all_files = glob.glob(os.path.join(path, "*_tracksMeta.csv"))

merged_data = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
merged_data = merged_data[merged_data["minTHW"] > 0.5]

total_ids = len(merged_data)
num_cars = len(merged_data[merged_data["class"] == "Car"])
num_trucks = len(merged_data[merged_data["class"] == "Truck"])

print(f"Total IDs: {total_ids}")
print(f"Number of Cars: {num_cars}")
print(f"Number of Trucks: {num_trucks}")


def iqr_filter(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    filtered_df = df[
        (df[column] >= (Q1 - 1.5 * IQR)) & (df[column] <= (Q3 + 1.5 * IQR))
    ]
    return filtered_df


params = ["width", "minXVelocity", "maxXVelocity", "meanXVelocity", "minTHW","minDHW"]

filtered_data = {param: {} for param in params}

for param in params:
    filtered_data[param]["Car"] = iqr_filter(
        merged_data[merged_data["class"] == "Car"], param
    )
    filtered_data[param]["Truck"] = iqr_filter(
        merged_data[merged_data["class"] == "Truck"], param
    )
results_df = pd.DataFrame(
    columns=[
        "parameter",
        "class",
        "count",
        "mean",
        "std",
        "min",
        "50%",
        "max",
    ]
)

for param in params:
    for vehicle_class in ["Car", "Truck"]:
        filtered_df = filtered_data[param][vehicle_class]
        summary = filtered_df[param].describe(percentiles=[])
        summary["parameter"] = param
        summary["class"] = vehicle_class
        summary_df = pd.DataFrame(summary).transpose()
        results_df = pd.concat([results_df, summary_df], ignore_index=True)

results_df.to_csv("result.csv", index=False)

