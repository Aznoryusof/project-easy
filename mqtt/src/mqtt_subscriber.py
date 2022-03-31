#!/usr/bin/env python3
# -*- coding: utf-8 -*-

ENV = "DEMO"
TOPIC = "is614-g-01/team4/gateway_1/sensors"
MAX_OCCUPIED_SECS = 40 * 1
CLEANING_THRESHOLD = 3

import mysql.connector
import traceback
import requests
import json
import paho.mqtt.client as mqtt
import logging
import time
from datetime import datetime
if ENV == "DEMO": 
    from config_demo import *
else:
    from config_dev import *


# Configure logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(filename)s:%(funcName)s():%(lineno)i: %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MQTT client object
mqttc = None


# Handles an MQTT client connect event
# This function is called once, just after the mqtt client is connected to the server.
def handle_mqtt_connack(client, userdata, flags, rc) -> None:
    logger.debug(f"MQTT broker said: {mqtt.connack_string(rc)}")
    if rc == 0:
        client.is_connected = True

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(f"{TOPIC}")
    logger.info(f"Subscribed to: {TOPIC}")
    logger.info(f"Publish something to {TOPIC} and the messages will appear here.")


def check_any_empty(msg_split):
    for val in msg_split:
        if val == "":
            return True
    return False


def parse_data(msg):
    msg_decoded = msg.payload.decode('utf8')
    msg_split = msg_decoded.split(",")
    has_empty = check_any_empty(msg_split)
    if not has_empty and len(msg_split) == 3:
        return (msg_split[0], msg_split[1], int(msg_split[2]))
    else:
        return None


def insert_occ_change(data):
    # Check washroom occupancy status for latest dt
    q = f"select is_locked from tbl_occ_change where washroom_id={data[0]} and start_dt=(select max(start_dt) from tbl_occ_change where washroom_id={data[0]})"
    locked_status = query_mysqldb(q)
    
    # If no previous records, set locked status as -1
    if len(locked_status) == 0:
        locked_status = -1
    else:
        locked_status = locked_status[0][0]
    
    # Insert if there is a change from the previous state
    if locked_status != data[1]:
        # Insert data
        q = f"insert into tbl_occ_change (washroom_id, is_locked) values (%s, %s)"
        meta_data = f"Washroom occupancy status for washroom {data[0]}"
        insert_mysqldb(q, "tbl_occ_change", (data[0], data[1]), meta_data)


def update_sensor_status(data):
    q = f"insert into tbl_sensor (sensor_id, washroom_id) values (%s, %s) on duplicate key update dt=NOW()"
    meta_data = f"Sensor status for sensor {data[0]}"
    insert_mysqldb(q, "tbl_sensor", (data[0], data[0]), meta_data)


def check_overoccupied(data):
    q = f"select start_dt from tbl_occ_change where washroom_id={data[0]} and is_locked=1 and start_dt=(select max(start_dt) from tbl_occ_change where washroom_id={data[0]})"
    occupied_start_dt = query_mysqldb(q)
    if len(occupied_start_dt) > 0:
        difference = datetime.now() - occupied_start_dt[0][0]
        if difference.total_seconds() > int(MAX_OCCUPIED_SECS):
            return occupied_start_dt
        else:
            return None


def check_alerted_overoccupied(data, occupied_start_dt):
    start_dt = occupied_start_dt[0][0].strftime('%Y-%m-%d %H:%M:%S')
    q = f"select alert_sent from tbl_overoccupied_alert where washroom_id={data[0]} and start_dt='{start_dt}'"
    alert_status = query_mysqldb(q)
    if len(alert_status) == 0 or alert_status[0][0] == "0":
        return False
    else: 
        return True
    

def post_message_to_slack(payload):
    res = requests.post(config["slack_webhook"], json.dumps(payload))
    if res.status_code == 200:
        return True
    else:
        logger.info(f"Posting to slack failed with error: {res.status_code}")
        return False


def parse_overoccupied_msg(data, washroom_data, washroom_headers):
    current_dt = datetime.now()
    date = current_dt.strftime('%d %b %Y').upper()
    time = current_dt.strftime('%H%M')
    washroom_name = washroom_data[washroom_headers.index("washroom_name")]
    washroom_location = washroom_data[washroom_headers.index("washroom_description")]
    max_occupied_mins = round(MAX_OCCUPIED_SECS / 60, 2)
    
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":rotating_light: ALERT: {date} @ {time}HRS"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{washroom_name} - {washroom_location} occupied for more than {max_occupied_mins} minutes. Please check on user and acknowledge with :white_check_mark:"
                }
            },
            {
                "type": "divider"
            }
    	]
    }
    return payload


def send_overoccupied_alert(data, start_dt):
    # Retrieve and prep data
    queried_data = query_mysqldb(f"select * from tbl_washroom where washroom_id={data[0]}")
    queried_headers = query_mysqldb("show columns from tbl_washroom")
    payload = parse_overoccupied_msg(data, queried_data[0], [col[0] for col in queried_headers])
    
    # Send alert to slack channel
    alert_sent = post_message_to_slack(payload)
    
    # Update database
    if alert_sent:
        q = f"insert into tbl_overoccupied_alert (washroom_id, start_dt, alert_sent, details, dt) values (%s, %s, %s, %s, now()) on duplicate key update alert_sent='1', dt=now()"
        meta_data = f"Overoccupied alert for washroom {data[0]}"
        start_dt = start_dt[0][0].strftime('%Y-%m-%d %H:%M:%S')
        insert_mysqldb(q, "tbl_overoccupied_alert", (data[0], start_dt, '1', ''), meta_data)


def check_need_cleaning(data):
    q = f"select count(*) from tbl_occ_change where washroom_id={data[0]} and is_locked=1 and start_dt>=(select last_cleaned_dt from tbl_washroom where washroom_id={data[0]})"
    usage_no = query_mysqldb(q)
    if len(usage_no) > 0:
        usage_no = usage_no[0][0]
        if usage_no >= CLEANING_THRESHOLD:
            return True
        else:
            return False


def check_alerted_cleaning(data):
    q = f"select alert_sent from tbl_cleaning_alert_status where washroom_id={data[0]}"
    alert_status = query_mysqldb(q)
    if len(alert_status) == 0 or alert_status[0][0] == "0":
        return False
    else: 
        return True


def parse_cleaning_msg(data, washroom_data, washroom_headers):
    current_dt = datetime.now()
    date = current_dt.strftime('%d %b %Y').upper()
    time = current_dt.strftime('%H%M')
    washroom_name = washroom_data[washroom_headers.index("washroom_name")]
    washroom_location = washroom_data[washroom_headers.index("washroom_description")]
    
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":restroom: ALERT: {date} @ {time}HRS"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Cleaning needed at {washroom_name} - {washroom_location}. Acknowledge with :white_check_mark:"
                }
            },
            {
                "type": "divider"
            }
    	]
    }
    return payload


def send_cleaning_alert(data):
    # Retrieve and prep data
    queried_data = query_mysqldb(f"select * from tbl_washroom where washroom_id={data[0]}")
    queried_headers = query_mysqldb("show columns from tbl_washroom")
    payload = parse_cleaning_msg(data, queried_data[0], [col[0] for col in queried_headers])
    
    # Send alert to slack channel
    alert_sent = post_message_to_slack(payload)
    
    # Update database
    if alert_sent:
        q = f"insert into tbl_cleaning_alert_status (washroom_id, alert_sent, dt) values (%s, %s, now()) on duplicate key update alert_sent='1'"
        meta_data = f"Cleaning alert for washroom {data[0]}"
        insert_mysqldb(q, "tbl_cleaning_alert_status", (data[0], '1'), meta_data)
        
        q = f"insert into tbl_cleaning_alert (washroom_id, alert_sent, dt) values (%s, %s, now())"
        meta_data = f"Cleaning alert for washroom {data[0]}"
        insert_mysqldb(q, "tbl_cleaning_alert", (data[0], '1'), meta_data)


def query_mysqldb(query):
    mydb = mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["pwd"],
        database=config["db"]
    )
    mycursor = mydb.cursor()
    mycursor.execute(query)
    data_list = [data for data in mycursor]
    mycursor.close()
    mydb.close()
    
    return data_list
    

def insert_mysqldb(query, table, data, meta_data):
    mydb = mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["pwd"],
        database=config["db"]
    )
    mycursor = mydb.cursor()
    mycursor.execute(query, data)
    mydb.commit()
    logger.info(f"Inserted to {table}: {meta_data}")


# Handles an incoming message from the MQTT broker.
def handle_mqtt_message(client, userdata, msg) -> None:
    data = parse_data(msg)
    if data:
        # Insert data to occupancy change table
        try:
            insert_occ_change(data)
        except:
            logger.info(traceback.format_exc())
            sys.exit()
        
        # Insert alive status to sensor table
        if data[2] % 60 == 0:
            update_sensor_status(data)

        # Send alert to slack channel when usage reaches a minimum threshold (i.e. Overoccupied)
        try:
            occupied_start_dt = check_overoccupied(data)
            if occupied_start_dt:
                has_alerted = check_alerted_overoccupied(data, occupied_start_dt)
                if not has_alerted:
                    send_overoccupied_alert(data, occupied_start_dt)
        except:
            logger.info(traceback.format_exc())
            sys.exit()

        # Send alert to slack channel (for cleaning)
        try:
            if data[1] == "0":
                need_cleaning = check_need_cleaning(data)
                if need_cleaning:
                    has_alerted = check_alerted_cleaning(data)
                    if not has_alerted:
                        send_cleaning_alert(data)
        except:
            logger.info(traceback.format_exc())
            sys.exit()


def main() -> None:
    global mqttc

    # Create mqtt client
    mqttc = mqtt.Client()

    # Register callbacks
    mqttc.on_connect = handle_mqtt_connack
    mqttc.on_message = handle_mqtt_message

    # Set this flag to false first, handle_mqtt_connack will set it to true later
    mqttc.is_connected = False

    # Connect to broker
    mqttc.connect("broker.mqttdashboard.com")

    # start the mqtt client loop
    mqttc.loop_start()

    # approximate amount of time to wait for client to be connected
    time_to_wait_secs = 5

    # keep looping until either the client is connected, or waited for too long
    waited_for_too_long = False
    while not mqttc.is_connected and not waited_for_too_long:
        # sleep for 0.1s
        time.sleep(0.1)
        time_to_wait_secs -= 0.1

        # set this to true if waited for too long
        if time_to_wait_secs <= 0:
            waited_for_too_long = True

    # exit if client couldn't connect even after waiting for a long time
    if waited_for_too_long:
        logger.error(f"Can't connect to broker.mqttdashboard.com, waited for too long")
        return

    # Loopy loop
    # Keep looping, when messages come in they'll be handled by handle_mqtt_message()
    while True:
        time.sleep(10)

    # Stop the MQTT client
    mqttc.loop_stop()


if __name__ == "__main__":
    main()
