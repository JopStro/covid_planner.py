"""
A covid-19 planner/alarm clock that runs through a web server, providing news notifications and giving briefings about the weather, infection rate and news on alarms.
"""
import requests
import json
import sched
import time
import pyttsx3
import logging
import flask as f
from uk_covid19 import Cov19API


app = f.Flask(__name__)
s = sched.scheduler(time.time, time.sleep)
tts = pyttsx3.init()
notifs_hist = []
notifs = []

with open('config.json') as config_file:
    config = json.load(config_file)

logging.basicConfig(level=logging.DEBUG, filename=config['logfile'])

if config['city_name'] == 'auto':
    CITY = requests.get('https://ipapi.co/city').text
else:
    CITY = config['city_name']

current_location = [ 'areaName=' + CITY ]
cases = { 'areaName': 'areaName', 'newCases': 'newCasesBySpecimenDate', 'cumCases': 'cumCasesBySpecimenDate' }
covid_api = Cov19API(filters=current_location, structure=cases)

BASE_WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather?'
COMPLETE_WEATHER_URL = BASE_WEATHER_URL + 'appid=' + config['api_keys']['weatherapi'] + '&q=' + CITY

BASE_NEWS_URL = 'http://newsapi.org/v2/top-headlines?'
NEWS_QUERIES = ''.join(['q=' + i + '&' for i in config['news']['queries']])
COMPLETE_NEWS_URL = BASE_NEWS_URL + NEWS_QUERIES + 'country=gb&apiKey=' + config['api_keys']['newsapi']

covid_data = {}
weather_data = {}
news_data = {}

try:
    update_type = { 'page_reload':'reload',
            'on_alarm':'alarm',
            'interval_secs': 'interval',
            'interval_mins': 'interval',
            'interval_hours': 'interval',
            'debug': 'debug'
        }[config['updates']['update_type']]
except KeyError:
    logging.warning('Invalid or no update type given, defaulting to on_alarm.')
    update_type = 'alarm'

if update_type == 'interval':
    update_interval = {
            'interval_secs': config['updates']['interval'],
            'interval_mins': config['updates']['interval'] * 60,
            'interval_hours': config['updates']['interval'] * 360
            }[config['updates']['update_type']]
    update_scheduler = sched.scheduler(time.time, time.sleep)

if update_type == 'debug':
    # Get local placeholder data for debugging and testing
    with open(config['updates']['debug paths']['covid']) as covid_file:
        covid_data = json.load(covid_file)

    with open(config['updates']['debug paths']['weather']) as weather_file:
        weather_data = json.load(weather_file)

    with open(config['updates']['debug paths']['news']) as news_file:
        news_data = json.load(news_file)

def update_data():
    """
    Updates local data from api's
    """
    global covid_data
    global weather_data
    global news_data
    covid_data = covid_api.get_json()
    tmp_data = requests.get(COMPLETE_WEATHER_URL).json()
    if tmp_data['cod'] == 200:
        weather_data = tmp_data
    tmp_data = requests.get(COMPLETE_NEWS_URL).json()
    if tmp_data['status'] == 'ok':
        news_data = tmp_data


def breifing(alarm_name, weather=False, news=False):
    """
    Alerts the user using text to speech, giving the current number of new cases and also the latest weather or news as per the arguments weather and news
    """
    if update_type == 'alarm':
        update_data()
        update_notifs()

    current_covid_data = covid_data['data'][0]
    tts.say('Alert: ' + alarm_name)
    tts.say('There have been ' + str(current_covid_data['newCases']) + ' new covid 19 cases in your area, leading to a total of ' + str(current_covid_data['cumCases']) + ' cases.')
    if weather:
        tempature = int(weather_data['main']['temp']) - 273
        weather_desc = weather_data['weather'][0]['description']
        tts.say('The current weather is ' + weather_desc + '. With a tempature of ' + str(tempature) + ' degrees celsius.')
    if news:
        latest_headlines = [article['title'] for article in news_data['articles']]
        tts.say('The latest headlines are:')

        for i in range(5):
            try:
                tts.say(latest_headlines[i])
            except IndexError:
                break

    tts.runAndWait()

def set_alarm(alarm_time: str, alarm_title: str, weather, news):
    """
    Schedules an alarm
    """
    # Protect from having two alarms with the same title
    if alarm_title in [item.argument[0] for item in s.queue]:
        logging.error('Alarm with this title already exists')
        return
    if ' ^ ' in alarm_title:
        logging.error('" ^ " is a reserved pattern, ignoring (sorry!)')
        return
    try:
        delay = time.mktime(time.strptime(alarm_time, '%Y-%m-%dT%H:%M')) - time.time()
    except ValueError:
        logging.error('Invalid time and date format')
        return
    if delay > 0:
        s.enter(int(delay), 1, breifing, (alarm_title,weather,news))
        logging.info('alarm_add ^ ' + alarm_title + ' ^ ' + alarm_time + ' ^ ' + weather + ' ^ ' + news)

def del_alarm(alarm_title: str):
    """
    Deletes the alarm with the given title
    """
    try:
        s.cancel(s.queue[[alarm.argument[0] for alarm in s.queue].index(alarm_title)])
        logging.info('alarm_del ^ ' + alarm_title)
    except ValueError:
        logging.error('No alarm with that title')


def get_alarms() -> list:
    """
    Returns a list of scheduled alarms.
    """
    alarms = []
    for alarm in s.queue:
        alarm_time = time.localtime(alarm.time + 60)
        alarms.append({'title': alarm.argument[0], 'content': 'Set to go off at ' + time.strftime("%H:%M on %d/%m/%Y", alarm_time)})
    return alarms

def add_notif(title: str, content: str):
    """
    Adds a new notification to the notification list with the appropriate title and content, providing it hasn't already been added in the past.
    """
    global notifs
    global notifs_hist
    new_notif = {'title': title, 'content': f.Markup(content)}
    if not new_notif in notifs_hist:
            notifs.insert(0,new_notif)
            notifs_hist.insert(0,new_notif)
            logging.info('notif_add ^ ' + title + ' ^ ' + content)

def del_notif(title: str):
    """
    Deletes a the notification with the given title
    """
    try:
        notifs.pop([notif['title'] for notif in notifs].index(title))
        logging.info('notif_del ^ ' + title)
    except ValueError:
        logging.error('No notification with that title')


def update_notifs():
    """
    Updates notifications based on current data.
    """
    global notifs
    global notifs_hist

    #News Notifications
    for article in news_data['articles'][::-1]:
        add_notif(article['title'], article['description'] + ' <a rel="noopener noreferrer" target="_blank" href="' + article['url'] + '">Link to article</a>')

    #Covid Notifications
    if covid_data['data'][0]['newCases'] > 0:
        add_notif(str(covid_data['data'][0]['newCases']) + ' New COVID-19 Cases on ' + covid_data['lastUpdate'].split('T')[0], 'Total recorded cases in your area now ' + str(covid_data['data'][0]['cumCases']))

def scheduled_update():
    """
    Updates data and notifs and schedules the next update
    """
    update_data()
    update_notifs()
    update_scheduler.enter(update_interval, 1, scheduled_update)

def restore_state():
    with open('sys.log') as logfile:
        restore_alarms = []
        restore_notifs = []
        remove_notifs = []
        for line in logfile.readlines():
            if line[:10] == 'INFO:root:':
                split_line = line[10:].strip().split(' ^ ')
                if split_line[0] == 'alarm_add':
                    restore_alarms.append((split_line[2], split_line[1], split_line[3], split_line[4]))
                elif split_line[0] == 'alarm_del':
                    restore_alarms.pop([alarm[1] for alarm in restore_alarms].index(split_line[1]))
                elif split_line[0] == 'notif_add':
                    restore_notifs.append((split_line[1], split_line[2]))
                elif split_line[0] == 'notif_del':
                    remove_notifs.append(split_line[1])
    [set_alarm(*args) for args in restore_alarms]
    [add_notif(*args) for args in restore_notifs]
    [del_notif(title) for title in remove_notifs]


@app.route('/index')
def index():
    """
    Parses form input and renders the index webpage
    """

    if update_type == 'interval':
        update_scheduler.run(blocking=False)
    elif update_type == 'reload':
        update_data()
        update_notifs()

    s.run(blocking=False)

    set_alarm_time = f.request.args.get('alarm')
    set_alarm_title = f.request.args.get('two')
    set_weather = f.request.args.get('weather', '')
    set_news = f.request.args.get('news', '')
    if set_alarm_time:
        set_alarm(set_alarm_time, set_alarm_title, set_weather, set_news)
    removal = f.request.args.get('alarm_item', '')
    if removal: del_alarm(removal)
    alarms = get_alarms()
    
    notif_removal = f.request.args.get('notif', False)
    if notif_removal:
        del_notif(notif_removal)

    return f.render_template('index.html', alarms=alarms, title='Covid Planner', notifications=notifs)

if __name__ == '__main__':
    restore_state()
    if update_type != 'debug':
        update_data()
        if update_type == 'interval':
            update_scheduler.enter(update_interval, 1, scheduled_update)
    update_notifs()

    app.run()
