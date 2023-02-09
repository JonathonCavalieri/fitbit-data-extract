-------------------------------
--  CREATE BIGQUERY OBJECTS  --
-------------------------------
BEGIN 
----------------------
--  FITBIT DATASET  --
----------------------
	CREATE SCHEMA IF NOT EXISTS `fitbit-data-extract.fitbit`;

----------------------
--  ACTIVITY TABLE  --
----------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.activity`(
		user_id STRING,
		date DATE,
		processed_date TIMESTAMP,
		log_id INT64,
		activity_id INT64,
		activity_parent_id INT64,
		activity_parent_name STRING,
		name STRING,
		description STRING,
		calories INT64,
		duration INT64,
		steps INT64,
		has_active_zone_minutes BOOL,
		has_start_time BOOL,
		is_favorite BOOL,
		last_modified TIMESTAMP,
		start_date DATE,
		start_time TIME,
	);

-------------------
--  GOALS TABLE  --
-------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.goals`(
		user_id STRING,
		date DATE,
		processed_date TIMESTAMP,
		active_minutes INT64,
		calories_out INT64,
		distance FLOAT64,
		floors INT64,
		steps INT64,
	);

---------------------
--  SUMMARY TABLE  --
---------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.summary`(
		user_id STRING,
		date DATE,
		processed_date TIMESTAMP,
		active_score INT64,
		steps INT64,
		floors INT64,
		elevation FLOAT64,
		resting_heart_rate STRING,
		calories_out INT64,
		marginal_calories INT64,
		activity_calories INT64,
		calories_bmr INT64,
		sedentary_minutes INT64,
		lightly_active_minutes INT64,
		fairly_active_minutes INT64,
		very_active_minutes INT64,
		total_distance FLOAT64,
		tracker_distance FLOAT64,
		logged_activities_distance FLOAT64,
		very_active_distance FLOAT64,
		moderately_active_distance FLOAT64,
		lightly_active_distance FLOAT64,
		sedentary_active_distance FLOAT64,
		run_distance FLOAT64,
	);

------------------------
--  HEART_RATE TABLE  --
------------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.heart_rate`(
		date DATE,
		user_id STRING,
		processed_date TIMESTAMP,
		resting_heart_rate INT64,
		out_of_range_calories FLOAT64,
		out_of_range_minutes INT64,
		fat_burn_calories FLOAT64,
		fat_burn_minutes INT64,
		cardio_calories FLOAT64,
		cardio_minutes INT64,
		peak_calories FLOAT64,
		peak_minutes INT64,
	);

--------------------
--  WEIGHT TABLE  --
--------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.weight`(
		user_id STRING,
		date DATE,
		processed_date TIMESTAMP,
		log_id INT,
		bmi FLOAT64,
		weight FLOAT64,
	);

-----------------------------
--  FILES_PROCESSED TABLE  --
-----------------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.files_processed`(
		date DATE,
		user_id STRING,
		processed_date TIMESTAMP,
		api_endpoint STRING,
		data_source STRING,
		file_processed STRING,
	);

-------------------------
--  CARDIOSCORE TABLE  --
-------------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.cardioscore`(
		user_id STRING,
		date DATE,
		processed_date TIMESTAMP,
		vo2_max STRING,
	);

-------------------
--  SLEEP TABLE  --
-------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.sleep`(
		user_id STRING,
		date DATE,
		processed_date TIMESTAMP,
		log_id INT64,
		efficiency STRING,
		start_time TIMESTAMP,
		end_time TIMESTAMP,
		duration INT64,
		minutes_after_wakeup INT64,
		minutes_asleep INT64,
		minutes_awake INT64,
		minutes_to_fall_asleep INT64,
		time_in_bed INT64,
		info_code INT64,
		is_main_sleep BOOL,
		log_type STRING,
		type STRING,
	);

--------------------------
--  SLEEP_DETAIL TABLE  --
--------------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.sleep_detail`(
		log_id INT64,
		date DATE,
		date_time TIMESTAMP,
		type STRING,
		level STRING,
		seconds INT64,
	);

-----------------------------
--  ACTIVITY_DETAIL TABLE  --
-----------------------------
	CREATE OR REPLACE TABLE `fitbit-data-extract.fitbit.activity_detail`(
		date DATE,
		user_id STRING,
		log_id INT,
		processed_date TIMESTAMP,
		date_time TIMESTAMP,
		point_order INT,
		sport STRING,
		lap_number INT64,
		total_time_seconds FLOAT64,
		distance_meters FLOAT64,
		calories INT64,
		intensity STRING,
		trigger_method STRING,
		latitude FLOAT64,
		longitude FLOAT64,
		altitude_meters FLOAT64,
		heart_rate_bpm INT64,
	);

END 
