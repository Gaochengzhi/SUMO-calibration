import pandas as pd
import warnings

warnings.filterwarnings("ignore")
import math
import numpy as np
import matplotlib.pyplot as plt


def smape(y_true, y_pred):
    return 100 * np.mean(
        2 * np.abs(y_pred - y_true) / (np.abs(y_pred) + np.abs(y_true))
    )


# Load the data


def ailign_and_normalize_frames(sumo_group, tracks_group):
    min_sumo_frame = sumo_group["frame"].min()
    min_tracks_frame = tracks_group["frame"].min()

    sumo_group.loc[:, "frame"] = sumo_group["frame"] - min_sumo_frame
    tracks_group.loc[:, "frame"] = tracks_group["frame"] - min_tracks_frame

    # Take the minimum length between the two trajectories
    min_length = min(len(sumo_group), len(tracks_group))

    return sumo_group.iloc[:min_length], tracks_group.iloc[:min_length]

def align_and_normalize_frames(sumo_group, tracks_group):
    min_sumo_frame = sumo_group["frame"].min()
    min_tracks_frame = tracks_group["frame"].min()

    sumo_group.loc[:, "frame"] = sumo_group["frame"] - min_sumo_frame
    tracks_group.loc[:, "frame"] = tracks_group["frame"] - min_tracks_frame

    max_frame = max(sumo_group["frame"].max(), tracks_group["frame"].max())
    sumo_group = sumo_group[sumo_group["frame"] <= max_frame]
    tracks_group = tracks_group[tracks_group["frame"] <= max_frame]

    sumo_group.loc[:, "frame"] = sumo_group["frame"].astype(int)
    tracks_group.loc[:, "frame"] = tracks_group["frame"].astype(int)

    return sumo_group, tracks_group


sumo_df = pd.read_csv("../data/simulated/sumo.csv")
tracks_df = pd.read_csv("../data/02_tracks.csv")

# Filter tracks_df to keep only ids present in sumo_df
filtered_tracks_df = tracks_df[tracks_df["id"].isin(sumo_df["id"].unique())]

# Reverse the x direction for 02_tracks.csv data
filtered_tracks_df["x"] = 450 - filtered_tracks_df["x"]

# Group data by id
grouped_sumo = sumo_df.groupby("id")
grouped_tracks = filtered_tracks_df.groupby("id")

# Calculate SMAPE values for each id pair and store in a list
smape_values = []

# for id in sumo_df["id"].unique():
#     sumo_group = grouped_sumo.get_group(id)
#     tracks_group = grouped_tracks.get_group(id)
#
#     # Align trajectories by starting frame
#     sumo_group, tracks_group = align_and_normalize_frames(sumo_group, tracks_group)

for id in sumo_df["id"].unique():
    sumo_group = grouped_sumo.get_group(id)
    tracks_group = grouped_tracks.get_group(id)

    # Align and normalize frames
    sumo_group, tracks_group = align_and_normalize_frames(
        sumo_group, tracks_group
    )

    if len(sumo_group) > 100 and len(tracks_group) > 100:
        min_length = min(len(sumo_group), len(tracks_group))
        truncated_sumo = sumo_group.iloc[:min_length]
        truncated_tracks = tracks_group.iloc[:min_length]
        merged_data = truncated_sumo[["id", "frame", "x"]].merge(
            truncated_tracks[["id", "frame", "x"]],
            on=["id", "frame"],
            suffixes=("_sumo", "_tracks"),
        )

        smape_value = smape(merged_data["x_sumo"], merged_data["x_tracks"])
        smape_values.append((id, smape_value))
# Sort SMAPE values by similarity (ascending)
smape_values = list(filter(lambda x: not math.isnan(x[1]), smape_values))
sorted_smape_values = sorted(smape_values, key=lambda x: x[1])

# Print sorted SMAPE values
print("Sorted SMAPE values:")
i = 0

res_smape_list = []
for id, value in sorted_smape_values:
    i += 1
    res_smape_list.append(value)
    # print(f"{i} ID: {id}, SMAPE: {value}")

s = pd.Series(res_smape_list)
print(s.describe())

# Input the range of most similar trajectories you want to plot (e.g., [0, 7] for the most similar 8 pairs)
nth = len(s)
print(nth)
nth_most_similar = [int(nth)-22, int(nth)-1]

# Get the ids of the most similar trajectories within the specified range
selected_ids = [
    sorted_smape_values[i][0]
    for i in range(nth_most_similar[0], nth_most_similar[1] + 1)
]

# Plot the most similar trajectories within the specified range
# plt.figure(figsize=(10, 6))

for i, nth_id in enumerate(selected_ids):
    sumo_nth = sumo_df[sumo_df["id"] == nth_id]
    tracks_nth = filtered_tracks_df[filtered_tracks_df["id"] == nth_id]

    # Align and normalize frames
    sumo_aligned, tracks_aligned = align_and_normalize_frames(
        sumo_nth, tracks_nth
    )

    plt.figure(figsize=(8, 3))
    plt.plot(
        sumo_aligned["frame"],
        sumo_aligned["x"],
        label=f"Sumo ID: {nth_id}",
        linestyle=":",
    )
    plt.plot(
        tracks_aligned["frame"],
        tracks_aligned["x"],
        label=f"HighD ID: {nth_id}",
        linestyle="-.",
    )
    plt.legend()
    plt.xlabel("Frame")
    plt.ylabel("X")
    plt.title(f"Trajectories Pair {i+1}: Sumo ID {nth_id} vs HighD ID {nth_id}")
    plt.show()


smape_list = [value for _, value in sorted_smape_values]

# Plot the histogram
plt.figure(figsize=(5, 4))
plt.hist(smape_list, bins=28, range=(0, 35), edgecolor='black')
plt.xlabel('SMAPE (%)')
plt.ylabel('Frequency (pairs)')
plt.title(f'SMAPE Distribution (Totol : {len(smape_list)})')

# Show the histogram
plt.show()
