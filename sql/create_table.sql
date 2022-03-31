create schema if not exists iotdb_acc_demo;
use iotdb_acc_demo;

# Create OCCUPANCY_CHANGE Table
create table tbl_occ_change
(	
    washroom_id varchar(3) not null,
    start_dt datetime default current_timestamp,
    is_locked varchar(1) not null,    
    constraint tbl_occ_change_pk primary key (washroom_id, start_dt)
);

# Create CURRENT_STATUS Table
create table tbl_current_status
(
    washroom_id varchar(3) not null,
    is_locked varchar(1) not null,
    start_dt datetime,
    constraint tbl_current_status_pk primary key (washroom_id)
);

# Create WASHROOM Table
create table tbl_washroom
(	
    washroom_id varchar(3) not null,
    washroom_name varchar(50),
    washroom_description varchar(200),
    last_cleaned_dt datetime,
    dt datetime,
    constraint tbl_washroom_pk primary key (washroom_id)
);

# Create SENSOR Table
create table tbl_sensor
(	
    sensor_id varchar(3) not null,
    washroom_id varchar(3),
    dt datetime default current_timestamp,
    date_installed datetime,
    useful_life smallint,
    constraint tbl_sensor_pk primary key (sensor_id)
);

# Create OVEROCCUPIED_ALERT Table
create table tbl_overoccupied_alert
(	
    washroom_id varchar(3) not null,
    start_dt datetime,
    alert_sent varchar(1),
    details varchar(5000),
    dt datetime,
    constraint tbl_overoccupied_alert_pk primary key (washroom_id, start_dt)
);

# Create CLEANING_ALERT Table
create table tbl_cleaning_alert
(	
	id mediumint not null auto_increment,
    washroom_id varchar(3) not null,
    alert_sent varchar(1),
    dt datetime,
    constraint tbl_cleaning_alert_pk primary key (id),
    constraint tbl_cleaning_alert_fk foreign key (washroom_id) references tbl_washroom (washroom_id)
);

# Create CLEANING_ALERT_STATUS Table
create table tbl_cleaning_alert_status
(	
    washroom_id varchar(3) not null,
    alert_sent varchar(1),
    dt datetime,
    constraint tbl_cleaning_alert_status_pk primary key (washroom_id),
    constraint tbl_cleaning_alert_status_fk foreign key (washroom_id) references tbl_washroom (washroom_id)
);

# Create CLEANING_SCHEDULE Table
create table tbl_cleaning_schedule
(	
	id mediumint not null auto_increment,
    washroom_id varchar(3) not null,
    period varchar(16),
    time_str varchar(16),
    constraint tbl_cleaning_schedule_pk primary key (id)
);

# Create trigger for current status
delimiter $$
create trigger after_occ_change_insert
    after insert on tbl_occ_change for each row
    begin
        # Insert new values into current status table
        insert into tbl_current_status
            (washroom_id, is_locked, start_dt) 
        values 
            (new.washroom_id, new.is_locked, new.start_dt)
        on duplicate key update
            is_locked = new.is_locked,
            start_dt = new.start_dt;
    end$$
delimiter ;

# Create trigger for cleaning alert
delimiter $$
create trigger after_washroom_update
    after update on tbl_washroom for each row
    begin
        # Insert new values into current status table
        insert into tbl_cleaning_alert_status
            (washroom_id, alert_sent, dt) 
        values 
            (new.washroom_id, "0", now())
        on duplicate key update
            alert_sent = "0",
            dt = now();
    end$$
delimiter ;


/* references

# Insert default values
insert into tbl_sensor (sensor_id, washroom_id)
values ("0", "0");

# Insert for cleaning since start of the day
insert into tbl_washroom (washroom_id, washroom_name, washroom_description, last_cleaned_dt, dt)
values ("0", "Accessible Washroom A", "beside SMU gallery", CONCAT(CURDATE(), " ","00:00:00"), now())
on duplicate key update washroom_name=washroom_name, washroom_description=washroom_description, last_cleaned_dt=last_cleaned_dt, dt=now();


# Insert to reset cleaning to now
insert into tbl_washroom (washroom_id, washroom_name, washroom_description, last_cleaned_dt, dt)
values ("0", "Accessible Washroom A", "beside SOE study room 3", now(), now())
on duplicate key update washroom_name=washroom_name, washroom_description="opposite SMU gallery", last_cleaned_dt=now(), dt=now();


# Insert test values
insert into tbl_occ_change (washroom_id, is_locked)
values ("0", "0");

insert into tbl_occ_change (washroom_id, is_locked)
values ("0", "1");

insert into tbl_occ_change (washroom_id, is_locked)
values ("0", "0");

*/






