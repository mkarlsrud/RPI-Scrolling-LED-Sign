# coding=utf-8
from google.transit import gtfs_realtime_pb2
import requests
import time # imports module for Epoch/GMT time conversion
import os # imports package for dotenv

# The root directory requires a .env file with API_KEY assigned/defined within
# and dotenv installed from pypi. Get API key from http://datamine.mta.info/user
api_key = os.environ['MTA_API_KEY']
train_to_work_code = os.environ['MTA_TRAIN_ID']
feed_id = os.environ['MTA_FEED_ID']
train_names = os.environ['MTA_TRAIN_NAMES'].split(',')
show_next_x_trains = int(os.environ['SHOW_NEXT_X_TRAINS'])

# The MTA data feed uses the General Transit Feed Specification (GTFS) which
# is based upon Google's "protocol buffer" data format. While possible to
# manipulate this data natively in python, it is far easier to use the
# "pip install --upgrade gtfs-realtime-bindings" library which can be found on pypi
from protobuf_to_dict import protobuf_to_dict

def get_feed(api_key, feed_id):
    # Requests subway status data feed from City of New York MTA API
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get('http://datamine.mta.info/mta_esi.php?key={api_key}&feed_id={feed_id}'.format(api_key= api_key, feed_id= feed_id))
    feed.ParseFromString(response.content)
    return protobuf_to_dict(feed) # subway_feed is a dictionary

# This function takes a converted MTA data feed and a specific station ID and
# loops through various nested dictionaries and lists to (1) filter out active
# trains, (2) search for the given station ID, and (3) append the arrival time
# of any instance of the station ID to the collected_times list
def station_time_lookup(train_data, station, train_names):
    collected_times = []
    for trains in train_data: # trains are dictionaries
        if trains.get('trip_update', False) != False and True and trains['trip_update']['trip']['route_id'] in train_names:
            unique_train_schedule = trains['trip_update'] # train_schedule is a dictionary with trip and stop_time_update
            unique_arrival_times = unique_train_schedule['stop_time_update'] # arrival_times is a list of arrivals
            for scheduled_arrivals in unique_arrival_times: #arrivals are dictionaries with time data and stop_ids
                if scheduled_arrivals.get('stop_id', False) == station:
                    time_data = scheduled_arrivals['arrival']
                    unique_time = time_data['time']
                    if unique_time != None:
                        collected_times.append(unique_time)
    return collected_times

def minutes_until(time, current_time) :
    return int(((time - current_time) / 60))

def get_train_times():
    global api_key, train_to_work_code, feed_id, train_names, show_next_x_trains

    subway_feed = get_feed(api_key, feed_id)
    realtime_data = subway_feed['entity'] # train_data is a list
    collected_times = station_time_lookup(realtime_data, train_to_work_code, train_names)

    # Sort the collected times list in chronological order (the times from the data
    # feed are in Epoch time format)
    collected_times.sort()

    # Grab the current time so that you can find out the minutes to arrival
    current_time = int(time.time())
    return 'Next trains leave in {list} minutes'.format(list= ', '.join([str(minutes_until(collected_times[i], current_time))
                                                                         for i in range(0, show_next_x_trains)]))