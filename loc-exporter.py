import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "geopy"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo"])

import os
import csv
import pymongo
import json

#[@] CSV file indexes
LAT = int(os.getenv('LAT', '0'))
LON = int(os.getenv('LON', '1'))
LINES = int(os.getenv('LINES', '3'))

lines = ['C2', 'C4']

loc_burst = []
with open('locs.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    next(spamreader, None) # skip header
    for row in spamreader:
        loc_burst.append({'lat': row[LAT],'lon': row[LON]})

def queryDb(db, locs, line):
    # return db.aggregate([
    #     {'$geoNear': {'near': {'type': 'Point', 'coordinates': locs }, 'distanceField': 'distance', 'query': {'lin': line}}}, 
    #     {'$limit': 2},
    #     {'$sort': {'num': -1}},
    #     {'$project': {'_id': 0, 'pos': 0, 'lin': 0}}
    # ])
    return db.aggregate([
    {
        '$geoNear': {
            'near': {
                'type': 'Point', 
                'coordinates': [
                    37.4036941, -5.9939919
                ]
            }, 
            'distanceField': 'dis'
        }
    }, {
        '$sort': {
            'ts': -1
        }
    }, {
        '$project': {
            'line': 1, 
            'num': 1, 
            'dis': 1, 
            'ts': {
                '$dateToString': {
                    'format': '%H:%M:%S.%L', 
                    'date': '$ts'
                }
            }
        }
    }, {
        '$group': {
            '_id': {
                'line': '$line', 
                'num': '$num'
            }, 
            'locs': {
                '$push': {
                    'dis': '$dis', 
                    'ts': '$ts'
                }
            }
        }
    }, {
        '$project': {
            'locs': {
                '$slice': [
                    '$locs', 2
                ]
            }, 
            'last': {
                '$arrayElemAt': [
                    '$locs', 0
                ]
            }
        }
    }, {
        '$project': {
            'locs': {
                '$reduce': {
                    'input': '$locs', 
                    'initialValue': 0, 
                    'in': {
                        '$subtract': [
                            '$$this.dis', '$$value'
                        ]
                    }
                }
            }, 
            'last': 1, 
            'id': {
                '$concat': [
                    '$_id.line', '-', {
                        '$substr': [
                            '$_id.num', 0, 1
                        ]
                    }
                ]
            }, 
            '_id': 0
        }
    }
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

    print('[Database] setup complete, ready')
    return col_paradas

# def nextStop(line, current_pos, db):
#     coordinates = [float(pos) for pos in current_pos.values()]
#     print(line, coordinates)

#     cursor = queryDb(db, coordinates, line)
#     results = list(cursor)
#     nearest = None
#     if any([stop["top"] for stop in results]):
#         print("Top stop detected -> choosing it")
#         filtered = filter(lambda x: x["top"] == True, results)
#         nearest = next(filtered)
#         print(nearest)
#     else: 
#         nearest = next(cursor)
#         print(nearest)
    
def calcNearby(stop):
    print("[Algorithm] calculating nearby buses for stop:", stop["num"])
    


#[@] Main void, scheduler process.
def main():
    # while (True):
    stops = db_setup()
    stops_list = stops.find({})

    # for each stop get last timestamp position of each bus
    for stop in stops_list: 
        calcNearby(stop)

    
    # nextStop(lines[0], loc_burst[15], stops)
        # Calculate gap interval
        # wait_t = 0
        # print('[Scheduler] sleeping until next spawn ~', wait_t, 'secs')
        # time.sleep(wait_t)

if __name__ == "__main__":
    main()