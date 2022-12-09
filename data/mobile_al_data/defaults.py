from collections import OrderedDict

# The default stamp field and its type:
default_stamp_field = OrderedDict({
    'stamp': 'dt'
})

# Default sensors and their types, in order:
default_sensors = OrderedDict({
    'yaw': 'f',
    'pitch': 'f',
    'roll': 'f',
    'rotation_rate_x': 'f',
    'rotation_rate_y': 'f',
    'rotation_rate_z': 'f',
    'user_acceleration_x': 'f',
    'user_acceleration_y': 'f',
    'user_acceleration_z': 'f',
    'latitude': 'f',
    'longitude': 'f',
    'altitude': 'f',
    'course': 'f',
    'speed': 'f',
    'horizontal_accuracy': 'f',
    'vertical_accuracy': 'f',
    'battery_state': 's'
})

# Default tags and their types, in order:
default_tags = OrderedDict({
    'activity_query': 's'
})

# Default fields and their types, in order:
# TODO: Does this guarantee preserved order in older versions of Python?
default_fields = OrderedDict({
    **default_stamp_field,
    **default_sensors,
    **default_tags
})

default_sensor_names = dict({
    'yaw': 'Yaw',
    'pitch': 'Pitch',
    'roll': 'Roll',
    'rotation_rate_x': 'RotationRateX',
    'rotation_rate_y': 'RotationRateY',
    'rotation_rate_z': 'RotationRateZ',
    'user_acceleration_x': 'UserAccelerationX',
    'user_acceleration_y': 'UserAccelerationY',
    'user_acceleration_z': 'UserAccelerationZ',
    'latitude': 'Latitude',
    'longitude': 'Longitude',
    'altitude': 'Altitude',
    'course': 'Course',
    'speed': 'Speed',
    'horizontal_accuracy': 'HorizontalAccuracy',
    'vertical_accuracy': 'VerticalAccuracy'
})
