
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo"])

import os
import random
import time
import threading
import csv
import pymongo
import datetime
import json

#[@] CSV file indexes
LAT = int(os.getenv('LAT', '0'))
LON = int(os.getenv('LON', '1'))
LINES = int(os.getenv('LINES', '3'))

#[@] Constants
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
LOC_SPAWN_INTERVAL = int(os.getenv('LOC_SPAWN_INTERVAL', '5')) # in seconds
LOC_TTL = int(os.getenv('LOC_TTL', '10')) # in seconds

lines = ['c2', 'c4']

#[@] Saves a certain location to mongodb
def dump_loc(line, num, lat, lon, col):
    ts = datetime.datetime.utcnow()
    mydict = { 'line': line, 'num': num, 'lat': lat, 'lon': lon, 'ts': ts }
    col.insert_one(mydict)

#[@] Generates a new random bus
def spawn_bus(counter,col):
    rand_line = lines[random.randint(0,1)]
    id = "{0}-{1}".format(rand_line, counter)
    print('[Spawner] generating new bus with id:', id)

    loc_burst = []
    with open('locs.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row in spamreader:
            if row[LINES] == 'both' or row[LINES] == rand_line:
                loc_burst.append({'lat': row[LAT],'lon': row[LON]})

    for iloc, loc in enumerate(loc_burst):
        time.sleep(LOC_SPAWN_INTERVAL)
        print('[Spawner] dumping location of "{0}" ({1}/{2})'.format(id,iloc+1,len(loc_burst)))
        dump_loc(rand_line, counter, loc['lat'], loc['lon'], col)
    print('[Spawner] terminating bus with id:', id)

#[@] Database configurations.
def db_setup():
    db_client = pymongo.MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    db = db_client["demo"]
    print('[Database] cleaning previous collections...')
    db.drop_collection('paradas')
    db.drop_collection('coches')

    col_paradas = db["paradas"]
    col_paradas.insert_many(json.load(open('paradas.json')))
    

    col_coches = db["coches"]
    col_coches.create_index('ts', expireAfterSeconds = LOC_TTL)
    print('[Database] setup complete, ready')

    return col_coches

#[@] Main void, scheduler process.
def main():
    col = db_setup()

    if DRY_RUN:
        spawn_counter = 1
        spawn_bus(spawn_counter,col)
    else:
        while (True):
            # Calculate gap interval
            wait_t = random.randint(25,30)
            print('[Scheduler] sleeping until next spawn ~', wait_t, 'secs')
            time.sleep(wait_t)

            # Invoke child thread
            thread = threading.Thread(target=spawn_bus, args=(spawn_counter,))
            thread.start()
            spawn_counter = spawn_counter + 1;

if __name__ == "__main__":
    main()