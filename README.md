# PiClock3 ForecastWind

Modified forecast display plugin: uses OpenWeatherMap data supplier to pull wind information.

## Install

cd ~/PiClock3

git clone https://github.com/ShawnPGHPublic/piclock3-forecastwind
plugins/forecastwind

## Test

python3 PyQtPiClock3.py examples/forecastwind.yaml

------------------------------------------------------------------------

### Use it

Add the openweathermapwind provider to your config (openmeteo doesn't supply wind) and use it in the new forecast display:

```
providers:
  openweathermap:
    plugin: plugins.OpenWeatherMapWind
    apikey: '{apikeys.owmapi}'
    refresh: 30
    forecast-days: 6

forecast:
  plugin: plugins.ForecastWind
  region: forecast
  forecast-provider: openweathermap
  hourly: 3
  daily: 6
  hourly-step: 3   # free OWM grid is already 3 hours
```

