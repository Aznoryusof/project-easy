set global local_infile=1;

# Load into tbl_occ_change
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_occ_change.csv' 
into table tbl_occ_change
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(washroom_id, @start_dt, is_locked)
set start_dt = str_to_date(@start_dt, "%d/%m/%Y %H:%i:%s");


# Load into tbl_current_status
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_current_status.csv' 
into table tbl_current_status
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(washroom_id, is_locked, @start_dt)
set start_dt = str_to_date(@start_dt, "%d/%m/%Y %H:%i:%s");


# Load into tbl_washroom
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_washroom.csv' 
into table tbl_washroom
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(washroom_id, washroom_name, washroom_description, @last_cleaned_dt, @dt)
set last_cleaned_dt = str_to_date(@last_cleaned_dt, "%d/%m/%Y %H:%i:%s"), dt = str_to_date(@dt, "%d/%m/%Y %H:%i:%s");


# Load into tbl_sensor
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_sensor.csv' 
into table tbl_sensor
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(sensor_id, washroom_id, @dt, @date_installed, useful_life)
set dt = str_to_date(@dt, "%d/%m/%Y %H:%i:%s"), date_installed = str_to_date(@date_installed, "%d/%m/%Y %H:%i:%s");


# Load into tbl_overoccupied_alert
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_overoccupied_alert.csv' 
into table tbl_overoccupied_alert
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(washroom_id, @start_dt, alert_sent, details, @dt)
set start_dt = str_to_date(@start_dt, "%d/%m/%Y %H:%i:%s"), dt = str_to_date(@dt, "%d/%m/%Y %H:%i:%s");


# Load into tbl_cleaning_alert
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_cleaning_alert.csv' 
into table tbl_cleaning_alert
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, washroom_id, alert_sent, @dt)
set dt = str_to_date(@dt, "%d/%m/%Y %H:%i:%s");


# Load into tbl_cleaning_alert_status
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_cleaning_alert_status.csv' 
into table tbl_cleaning_alert_status
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(washroom_id, alert_sent, @dt)
set dt = str_to_date(@dt, "%d/%m/%Y %H:%i:%s");


# Load into tbl_cleaning_schedule
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_cleaning_schedule.csv' 
into table tbl_cleaning_schedule
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, washroom_id, period, time_str);


