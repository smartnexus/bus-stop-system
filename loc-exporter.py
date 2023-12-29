import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "geopy"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "firebase-admin"])

import os
import pymongo
import json
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

SPEED = int(os.getenv('SPEED', '10'))
UPDATE = int(os.getenv('WAIT', '5'))


#[@] Returns nearby buses to a certain coords.
def nearby_query(db, stop_loc, lines):
    return db.aggregate([
        {'$geoNear': {'near': {'type': 'Point', 'coordinates': stop_loc}, 'distanceField': 'dis', 'query': {'line': {'$in': lines}}}}, 
        {'$sort': {'ts': -1}}, 
        {'$group': {'_id': {'line': '$line', 'num': '$num'}, 'locs': {'$push': {'dis': '$dis', 'ts': '$ts'}}}}, 
        {'$project': {'locs': {'$slice': ['$locs', 2]}, 'last': {'$arrayElemAt': ['$locs', 0]}}}, 
        {'$project': {'dir': {'$reduce': {'input': '$locs', 'initialValue': 0, 'in': {'$subtract': ['$$this.dis', '$$value']}}}, 'last': 1, 'vid': {'$concat': ['$_id.line', '-', {'$substr': ['$_id.num', 0, 1]}]}, '_id': 0}}
    ])

#[@] Database configurations.
def db_setup():
    db_client = pymongo.MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    db = db_client["demo"]
    print('[Database] cleaning previous collections...')
    db.drop_collection('paradas')

    col_paradas = db["paradas"]
    col_paradas.create_index([('pos', pymongo.GEOSPHERE)])
    col_paradas.insert_many(json.load(open('paradas.json')))

    col_coches = db["coches"]

    print('[Database] setup complete, ready')
    return col_paradas, col_coches

#[@] Realtime Database configurations.
def rtdb_setup():
    cred = credentials.Certificate('keys/bus-stop-system-firebase-adminsdk.json')
    firebase_admin.initialize_app(cred, { #
        'databaseURL': os.getenv('FIREBASE_URI', 'https://databaseName.firebaseio.com')
    })
    st = db.reference('stops')
    st.set({})
    return st

#[@] Returns nearby buses for a stop
def nearby_calc(stop, db):
    print("[Algorithm] calculating nearby buses for stop:", stop["num"], "(lines={})".format(stop["lin"]))
    result = list(nearby_query(db, stop["pos"]["coordinates"], stop["lin"]))
    print("[Algorithm] found", len(result), "buses nearby.")
    return result
    
def dump_stop_calcs(num, data, rtdb):
    stop_nearby = rtdb.child(str(num))
    for bus_info in data:
        output = stop_nearby.child(bus_info["vid"])
        if bus_info["dir"] >= 0: # update time remaining
            body = json.loads(json.dumps(bus_info, default=str))
            body["est"] = round(body["last"]["dis"] / ((1000/60) * SPEED)) # meters/minutes
            del body["vid"]
            output.set(body)
        else: # clear entry
            output.set({})

#[@] Main void, scheduler process.
def main():
    rtdb = rtdb_setup()
    stops, locs = db_setup()
    stops_list = list(stops.find({}))

    while (True):
        # for each stop get last timestamp position of each bus
        for stop in stops_list: 
            nearby_buses = nearby_calc(stop, locs)
            dump_stop_calcs(stop["num"], nearby_buses, rtdb)
        print('[Scheduler] sleeping until next update ~', UPDATE, 'secs')
        time.sleep(UPDATE)

if __name__ == "__main__":
    main()