# Covid Planner

Covid planner is a python based alarm clock and news notification system that uses a web interface to schedule or view alarms and view notifications about the news and covid-19 cases in your area. Alarms give a text to speech briefing on covid-19 infections and the news or weather.

# Module Dependencies
pyttsx3
flask
uk-covid-19

you can install these dependencies using the following command
```
pip install pyttsx3 flask uk-covid-19
```

# Configuration

Covid planner is configured using a config.json file in your working directory. A sample config file exists called "sample_config.json"

## Format

### "api_keys"

This is where you put your required api keys for [newsapi.org](https://newsapi.org/) and [openweathermap.org](https://openweathermap.org/). These are both required for the program to run.
#### "newsapi" (required)
this is where you put the newsapi.org api key

#### "weatherapi" (required)
this is where you put the openweathermap.org key

### "city_name"
This is where you put your city name for local data.
You can also put in "auto" for the program to use ipapi.co to get your city name (beware that you may get rate limited if you restart the program multiple times, causing the program to not run properly and that the city name is never stored in a permanent location. It is recommended that you do *not* use this option in deployment).

### "updates"
configure information regarding the frequency that data is fetched from the apis.

#### "update_type"
This is where you put the type of update you want.
Options below

* page_reload: Update whenever the web interface is loaded.

* on_alarm: Update whenever an alarm goes off (this is the default if none is given or if the option given is invalid)

* interval\_\[secs|mins|hours\]: Update on a configurable time interval using seconds minutes or hours respectively.

* debug: Get data from local files for testing purposes (these local files will have to be provided by yourself as they may contain sensitive data)

#### "interval"
The time interval for the interval update types.

#### "debug paths"
This is where the locations of debug data files are kept.

#### "logfile"
The path to the log file (defaults to sys.log)

# Usage
Run covid_planner.py, using python, in a directory with a valid config.json file.

The web interface will then be accessible at 127.0.0.1:5000/index

# Credits
Originally made my Joseph Strong (myself) in December 2020 and licenced under the MIT licence.
