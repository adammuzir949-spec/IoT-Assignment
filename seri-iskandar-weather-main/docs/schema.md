📋 Database schema (please use these exact names in your code)

Table 1: observations (actual weather, 1 row per hour)
- obs_time: hour of the observation (Malaysia time)
- temperature: °C
- humidity: %
- precipitation: rainfall in mm
- wind_speed: km/h
- fetched_at: when the script actually ran

Table 2: forecasts (predicted weather, ~72 rows per hour)
- issued_at: when the forecast was made
- target_time: the hour being predicted
- horizon_hours: how many hours ahead (target_time − issued_at)
- temperature, humidity, precipitation, wind_speed: same units as above
- precip_probability: chance of rain in %

🔗 How they connect: forecasts.target_time matches observations.obs_time
Please don't rename anything without telling me first 🙏
