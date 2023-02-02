# API CONSTANTS
WEB_API_URL = "https://api.fitbit.com"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
AUTHORIZATION_URL = "https://www.fitbit.com/oauth2/authorize"
POSSIBLE_SCOPES = [
    "activity",
    "cardio_fitness",
    "electrocardiogram",
    "heartrate",
    "location",
    "nutrition",
    "oxygen_saturation",
    "profile",
    "respiratory_rate",
    "settings",
    "sleep",
    "social",
    "temperature",
    "weight",
]


# General Constants
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# Transform Constants
TABLE_NAME_MAPPING = {
    "get_activity_summary_by_date_activity": "activity",
    "get_activity_summary_by_date_goals": "goals",
    "get_activity_summary_by_date": "summary",
    "get_heart_rate_by_date": "heart_rate",
    "get_body_weight_by_date": "weight",
    "file_processing_log": "files_processed",
    "get_cardio_score_by_date": "cardioscore",
    "get_sleep_by_date": "sleep",
    "get_activity_tcx_by_id": "activity_detail",
}

ACTIVITY_FIELDS = {
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "date": {"bq_name": "date", "bq_type": "DATE"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "logId": {"bq_name": "log_id", "bq_type": "INT64"},
    "activityId": {"bq_name": "activity_id", "bq_type": "INT64"},
    "activityParentId": {"bq_name": "activity_parent_id", "bq_type": "INT64"},
    "activityParentName": {"bq_name": "activity_parent_name", "bq_type": "STRING"},
    "name": {"bq_name": "name", "bq_type": "STRING"},
    "description": {"bq_name": "description", "bq_type": "STRING"},
    "calories": {"bq_name": "calories", "bq_type": "INT64"},
    "duration": {"bq_name": "duration", "bq_type": "INT64"},
    "steps": {"bq_name": "steps", "bq_type": "INT64"},
    "hasActiveZoneMinutes": {"bq_name": "has_active_zone_minutes", "bq_type": "BOOL"},
    "hasStartTime": {"bq_name": "has_start_time", "bq_type": "BOOL"},
    "isFavorite": {"bq_name": "is_favorite", "bq_type": "BOOL"},
    "lastModified": {"bq_name": "last_modified", "bq_type": "TIMESTAMP"},
    "startDate": {"bq_name": "start_date", "bq_type": "DATE"},
    "startTime": {"bq_name": "start_time", "bq_type": "TIME"},
}

GOAL_FIELDS = {
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "date": {"bq_name": "date", "bq_type": "DATE"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "activeMinutes": {"bq_name": "active_minutes", "bq_type": "INT64"},
    "caloriesOut": {"bq_name": "calories_out", "bq_type": "INT64"},
    "distance": {"bq_name": "distance", "bq_type": "FLOAT64"},
    "floors": {"bq_name": "floors", "bq_type": "INT64"},
    "steps": {"bq_name": "steps", "bq_type": "INT64"},
}

SUMMARY_FIELDS = {
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "date": {"bq_name": "date", "bq_type": "DATE"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "activeScore": {"bq_name": "active_score", "bq_type": "INT64"},
    "steps": {"bq_name": "steps", "bq_type": "INT64"},
    "floors": {"bq_name": "floors", "bq_type": "INT64"},
    "elevation": {"bq_name": "elevation", "bq_type": "FLOAT64"},
    "restingHeartRate": {"bq_name": "resting_heart_rate", "bq_type": "STRING"},
    "caloriesOut": {"bq_name": "calories_out", "bq_type": "INT64"},
    "marginalCalories": {"bq_name": "marginal_calories", "bq_type": "INT64"},
    "activityCalories": {"bq_name": "activity_calories", "bq_type": "INT64"},
    "caloriesBMR": {"bq_name": "calories_bmr", "bq_type": "INT64"},
    "sedentaryMinutes": {"bq_name": "sedentary_minutes", "bq_type": "INT64"},
    "lightlyActiveMinutes": {"bq_name": "lightly_active_minutes", "bq_type": "INT64"},
    "fairlyActiveMinutes": {"bq_name": "fairly_active_minutes", "bq_type": "INT64"},
    "veryActiveMinutes": {"bq_name": "very_active_minutes", "bq_type": "INT64"},
    "total_distance": {"bq_name": "total_distance", "bq_type": "FLOAT64"},
    "tracker_distance": {"bq_name": "tracker_distance", "bq_type": "FLOAT64"},
    "loggedActivities_distance": {
        "bq_name": "logged_activities_distance",
        "bq_type": "FLOAT64",
    },
    "veryActive_distance": {"bq_name": "very_active_distance", "bq_type": "FLOAT64"},
    "moderatelyActive_distance": {
        "bq_name": "moderately_active_distance",
        "bq_type": "FLOAT64",
    },
    "lightlyActive_distance": {
        "bq_name": "lightly_active_distance",
        "bq_type": "FLOAT64",
    },
    "sedentaryActive_distance": {
        "bq_name": "sedentary_active_distance",
        "bq_type": "FLOAT64",
    },
    "Run_distance": {"bq_name": "run_distance", "bq_type": "FLOAT64"},
}

WEIGHT_FIELDS = {
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "date": {"bq_name": "date", "bq_type": "DATE"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "logId": {"bq_name": "log_id", "bq_type": "INT"},
    "bmi": {"bq_name": "bmi", "bq_type": "FLOAT64"},
    "weight": {"bq_name": "weight", "bq_type": "FLOAT64"},
}

SLEEP_FIELDS = {
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "dateOfSleep": {"bq_name": "date", "bq_type": "DATE"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "logId": {"bq_name": "log_id", "bq_type": "INT64"},
    "efficiency": {"bq_name": "efficiency", "bq_type": "STRING"},
    "startTime": {"bq_name": "start_time", "bq_type": "TIMESTAMP"},
    "endTime": {"bq_name": "end_time", "bq_type": "TIMESTAMP"},
    "duration": {"bq_name": "duration", "bq_type": "INT64"},
    "minutesAfterWakeup": {"bq_name": "minutes_after_wakeup", "bq_type": "INT64"},
    "minutesAsleep": {"bq_name": "minutes_asleep", "bq_type": "INT64"},
    "minutesAwake": {"bq_name": "minutes_awake", "bq_type": "INT64"},
    "minutesToFallAsleep": {"bq_name": "minutes_to_fall_asleep", "bq_type": "INT64"},
    "timeInBed": {"bq_name": "time_in_bed", "bq_type": "INT64"},
    "infoCode": {"bq_name": "info_code", "bq_type": "INT64"},
    "isMainSleep": {"bq_name": "is_main_sleep", "bq_type": "BOOL"},
    "logType": {"bq_name": "log_type", "bq_type": "STRING"},
    "type": {"bq_name": "type", "bq_type": "STRING"},
}

SLEEP_DETAILS_FIELDS = {
    "logId": {"bq_name": "log_id", "bq_type": "INT64"},
    "dateTime": {"bq_name": "date_time", "bq_type": "TIMESTAMP"},
    "level": {"bq_name": "level", "bq_type": "STRING"},
    "seconds": {"bq_name": "seconds", "bq_type": "INT64"},
}

CARDIOSCORE_FIELDS = {
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "dateTime": {"bq_name": "date", "bq_type": "DATE"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "value.vo2Max": {"bq_name": "vo2_max", "bq_type": "STRING"},
}

HEART_RATE_FIELDS = {
    "dateTime": {"bq_name": "date", "bq_type": "DATE"},
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "value.restingHeartRate": {"bq_name": "resting_heart_rate", "bq_type": "INT64"},
    "out_of_range_calories": {"bq_name": "out_of_range_calories", "bq_type": "FLOAT64"},
    "out_of_range_minutes": {"bq_name": "out_of_range_minutes", "bq_type": "INT64"},
    "fat_burn_calories": {"bq_name": "fat_burn_calories", "bq_type": "FLOAT64"},
    "fat_burn_minutes": {"bq_name": "fat_burn_minutes", "bq_type": "INT64"},
    "cardio_calories": {"bq_name": "cardio_calories", "bq_type": "FLOAT64"},
    "cardio_minutes": {"bq_name": "cardio_minutes", "bq_type": "INT64"},
    "peak_calories": {"bq_name": "peak_calories", "bq_type": "FLOAT64"},
    "peak_minutes": {"bq_name": "peak_minutes", "bq_type": "INT64"},
}

ACTIVITY_TCX_FIELDS = {
    "date": {"bq_name": "date", "bq_type": "DATE"},
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "log_id": {"bq_name": "log_id", "bq_type": "INT"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "Time": {"bq_name": "date_time", "bq_type": "TIMESTAMP"},
    "point_order": {"bq_name": "point_order", "bq_type": "INT"},
    "Sport": {"bq_name": "sport", "bq_type": "STRING"},
    "lap_number": {"bq_name": "lap_number", "bq_type": "INT64"},
    "TotalTimeSeconds": {"bq_name": "total_time_seconds", "bq_type": "FLOAT64"},
    "DistanceMeters": {"bq_name": "distance_meters", "bq_type": "FLOAT64"},
    "Calories": {"bq_name": "calories", "bq_type": "INT64"},
    "Intensity": {"bq_name": "intensity", "bq_type": "STRING"},
    "TriggerMethod": {"bq_name": "trigger_method", "bq_type": "STRING"},
    "LatitudeDegrees": {"bq_name": "latitude", "bq_type": "FLOAT64"},
    "LongitudeDegrees": {"bq_name": "longitude", "bq_type": "FLOAT64"},
    "AltitudeMeters": {"bq_name": "altitude_meters", "bq_type": "FLOAT64"},
    "HeartRateBpm": {"bq_name": "heart_rate_bpm", "bq_type": "INT64"},
}

FILES_PROCESSED_FIELDS = {
    "date": {"bq_name": "date", "bq_type": "DATE"},
    "user_id": {"bq_name": "user_id", "bq_type": "STRING"},
    "processed_date": {"bq_name": "processed_date", "bq_type": "TIMESTAMP"},
    "api_endpoint": {"bq_name": "api_endpoint", "bq_type": "STRING"},
    "file_processed": {"bq_name": "file_processed", "bq_type": "STRING"},
}

TABLE_NAME_METADATA_MAPPING = {
    "activity": ACTIVITY_FIELDS,
    "goals": GOAL_FIELDS,
    "summary": SUMMARY_FIELDS,
    "heart_rate": HEART_RATE_FIELDS,
    "weight": WEIGHT_FIELDS,
    "files_processed": FILES_PROCESSED_FIELDS,
    "cardioscore": CARDIOSCORE_FIELDS,
    "sleep": SLEEP_FIELDS,
    "sleep_detail": SLEEP_DETAILS_FIELDS,
    "activity_detail": ACTIVITY_TCX_FIELDS,
}
