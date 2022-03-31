set global local_infile=1;


# Load into tbl_washroom
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_washroom.csv' 
into table tbl_washroom
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(washroom_id, washroom_name, washroom_description, @last_cleaned_dt, @dt)
set last_cleaned_dt = now(), dt = now();

# Load into tbl_sensor
load data local infile 'C:/Users/aznor/Singapore Management University/IS614 IoT - Technology and Applications - General/data/final/tbl_sensor.csv' 
into table tbl_sensor
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(sensor_id, washroom_id, @dt, @date_installed, useful_life)
set dt = str_to_date(@dt, "%d/%m/%Y %H:%i:%s"), date_installed = str_to_date(@date_installed, "%d/%m/%Y %H:%i:%s");


# Insert to reset cleaning to now
insert into tbl_washroom (washroom_id, washroom_name, washroom_description, last_cleaned_dt, dt)
values ("0", "Accessible Washroom A", "opposite SMU gallery", now(), now())
on duplicate key update washroom_name=washroom_name, washroom_description="opposite SMU gallery", last_cleaned_dt=now(), dt=now();

