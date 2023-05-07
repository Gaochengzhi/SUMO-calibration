from math import sqrt
import random
import os
import sys
import time
import re
import csv
from utils import check_sumo_env
import shutil

check_sumo_env()
import traci
from traci import StepListener, constants as tc, vehicle
from plexe import (
    Plexe,
    ACC,
    CACC,
    GEAR,
    RPM,
    CONSENSUS,
    PLOEG,
    ENGINE_MODEL_REALISTIC,
    FAKED_CACC,
)
from utils import (
    start_sumo,
    running,
    add_platooning_vehicle,
    add_vehicle,
    communicate,
    get_distance,
)


TOTAL_TIME = 22539*4+2600*4

END_EDGE_ID = "E7"

GUI = False

# inter-vehicle distance

START_STEP = 0
# lane_number latoon insert
CHECK_ALL = 0b01111  # SpeedMode
LAN_CHANGE_MODE = 0b011001011000
#                   0123456789
ptype_list = []


def extract_number(string):
    match = re.search(r"p.(\d+)", string)
    if match:
        return int(match.group(1))
    return None




def get_random_vtype(distribution=0.7, vtype_list=["truck", "car"]):
    r = random.random()
    vtype_suffix = ""
    j = 0
    for i in distribution:
        if r < i:
            vtype_suffix = vtype_list[j]
            break
        j += 1
    vtype_num = random.randint(0, 999)
    return vtype_suffix + "1"


def get_veh_info(edge_id, writer, step):

    vehicle_list = traci.edge.getLastStepVehicleIDs(edge_id)

    if vehicle_list:
        p_veicle_list = [
            vehicle for vehicle in vehicle_list if vehicle.startswith("p.")
        ]  # find platoon vehicle
        vehicle_sum = len(vehicle_list)
        p_vehicle_sum = len(p_veicle_list)
        for idv in vehicle_list:
            idv_speed = traci.vehicle.getSpeed(idv)
            idv_acc = traci.vehicle.getAcceleration(idv)
            idv_lane_pos = traci.vehicle.getLanePosition(idv)
            idv_type = traci.vehicle.getTypeID(idv)
            idv_lane = traci.vehicle.getLaneIndex(idv)

            writer.writerow(
                [
                    idv,
                    int(step/4)+1,
                    idv_type,
                    round(idv_speed, 4),
                    round(idv_acc, 4),
                    round(idv_lane_pos, 4),
                    idv_lane,
                    vehicle_sum,
                    p_vehicle_sum,
                ]
            )


def init_csv_file(path):
    f = open(path, "w")
    writer = csv.writer(f)
    writer.writerow(
        [
            "id",
            "frame",
            "idv_type",
            "v",
            "acc",
            "x",
            "lane_index",
            "vehicle_sum",
            "p_vehicle_sum",
        ]
    )
    return f, writer


def gene_config():
    copy_cfg = (
    "simulated")
    shutil.copytree("../cfg", copy_cfg, dirs_exist_ok=True)
    return copy_cfg
def trajectory_tracking():
    tracks_meta_path = "../data/02_tracksMeta.csv"
    tracks_path = "../data/02_tracks.csv"

    # Read tracksMeta and store the relevant data in a dictionary
    tracks_meta = {}
    with open(tracks_meta_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['drivingDirection']) == 1:
                tracks_meta[int(row['id'])] = {
                    'initialFrame': int(row['initialFrame']),
                    'class': row['class']
                }

    # Read tracks, find the first occurrence of the target Ids, and store the required data
    with open(tracks_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            current_id = int(row['id'])
            if current_id in tracks_meta and tracks_meta[current_id].get('found') is None:
                tracks_meta[current_id].update({
                    'found': True,
                    'xVelocity': float(row['xVelocity']),
                    'x': float(row['x']),
                    'laneId': int(row['laneId'])
                })

    return tracks_meta

def has_vehicle_entered(step, vehicles_to_enter):
    return vehicles_to_enter.get(step) is not None


def aggregate_vehicles(tracks_meta):
    vehicles_to_enter = {}
    for vid, data in tracks_meta.items():
        if data.get('found'):
            data['id'] = vid
            frame = data['initialFrame']
            if frame in vehicles_to_enter:
                vehicles_to_enter[frame].append(data)
            else:
                vehicles_to_enter[frame] = [data]
    return vehicles_to_enter

def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    tracks_meta = trajectory_tracking()
    vehicles_to_enter = aggregate_vehicles(tracks_meta)
    cfg_file = gene_config()
    start_sumo(cfg_file + "/freeway.sumo.cfg", False, gui=GUI)
    step = 0
    times = 0
    random.seed(7)
    vid_list = 0
    insert_gap = 0
    f1, before_writer = init_csv_file(cfg_file + "/data/sumo.csv")
    

    while running(demo_mode, times, TOTAL_TIME + 1):
        traci.simulationStep()

        if demo_mode and times == TOTAL_TIME:
            f1.close()
            shutil.copytree(
                cfg_file + "/data", "../data/" + cfg_file, dirs_exist_ok=True
            )
            shutil.rmtree(cfg_file)
            time.sleep(4)
            traci.close()
            quit()

        if times > START_STEP and times%4==0:  # remove pass by cacc vehicles
            get_veh_info("E0", before_writer, times)

        if times>START_STEP and times%4 ==0:
            if has_vehicle_entered(step, vehicles_to_enter):
                for data in vehicles_to_enter[step]:
                    despeed = random.randint(31,33) if data['class']=='Car' else random.randint(24,25)
                    try:
                        traci.vehicle.add(
                            vehID=str(data['id']),
                            routeID="platoon_route",
                            typeID=str(data['class']).lower()+str(random.randint(0,999)),
                            departSpeed=despeed,
                            departPos=str(450-float(data['x'])),
                            departLane=str(int(data['laneId'])-1),
                        )
                    except Exception as e:
                        pass
            step += 1


        times+=1
    traci.close()


if __name__ == "__main__":
    main(True, False)
