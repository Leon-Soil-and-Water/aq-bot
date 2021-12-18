# script that (1) fetches AQI data, (2) generates photo, and (3) posts it to twitter

"""import libraries"""
import schedule
import time
import pandas as pd
import requests
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import tweepy 
import yaml

"""define dataframes and keys"""
# create dataframe
conditions = pd.DataFrame({
    'category': ['1', '2', '3', '4', '5', '6'],
    'status': ['good', 'moderate', 'unhealthy for sensitive groups', 'unhealthy', 'very unhealthy', 'hazardous'],
    'color': ['green', 'yellow', 'orange', 'red', 'purple', 'maroon'],
    'message': ['In the Tallahassee area, the air quality is "good". Enjoy your outdoor activities!', 
            'In the Tallahassee area, the air quality is "moderate". If you are sensitive to air pollution, limit your time outdoors or wear a mask.',
            'In the Tallahassee area, the air quality is "unhealthy for sensitive groups',
            'In the Tallahassee area, the air quality is "unhealthy".',
            'In the Tallahassee area, the air quality is "very unhealthy',
            'In the Tallahassee area, the air quality is "hazardous.']
})

#read YAML file
yaml_file = open("../keys.yaml")
parsed_yaml_file = yaml.safe_load(yaml_file)

"""define functions"""
# add conditions to original dataframe
def add_conditions(dataframe):
    for i in range(len(dataframe)):
        dataframe.loc[i, 'status'] = conditions[conditions['category'] == df.loc[i, 'Category']]['status'].loc[0]
        dataframe.loc[i, 'color'] = conditions[conditions['category'] == df.loc[i, 'Category']]['color'].loc[0]
        dataframe.loc[i, 'message'] = conditions[conditions['category'] == df.loc[i, 'Category']]['message'].loc[0]
    return dataframe

# format time
def format_time(post_time):
    if post_time > 12:
        time = post_time - 12
        hour = str(time) + 'PM'
    elif post_time:
        hour = str(post_time) + 'AM'
    return hour

#authorization function
def twitter_api():
  auth = tweepy.OAuthHandler(parsed_yaml_file["consumer_key"], parsed_yaml_file["consumer_secret"])
  auth.set_access_token(parsed_yaml_file["access_token"], parsed_yaml_file["access_token_secret"])
  api = tweepy.API(auth)
  return api

# post picture
def post_tweet(post_time):
    # get today's date
    day = date.today().day
    month = date.today().month
    year = date.today().year
    
    # get post_time
    post_time_2 = int(post_time) + 1
    
    # pull data from AirNow
    r = requests.get('https://www.airnowapi.org/aq/data/?startDate={year}-{month}-{day}T{time1}&endDate={year}-{month}-{day}T{time2}&parameters=PM25&BBOX=-84.500651,30.275370,-84.080424,30.684863&dataType=B&format=application/json&verbose=1&monitorType=2&includerawconcentrations=0&API_KEY=2BB44069-F9EF-4CA7-8B67-C9832B168B60'.format(day = day, month = month, year = year, time1 = post_time, time2 = post_time_2)).json()
    
    # store in dataframe
    global df
    df = pd.DataFrame.from_dict(r)
    
    # clean data
    df['date'] = df['UTC'].str.split('T').str[0]
    df['time'] = df['UTC'].str.split('T').str[1]
    df = df.drop(['UTC'], axis=1)
    df['Category'] = df['Category'].astype(str)
    
    # add conditions to the dataframe
    add_conditions(df)
    
    # create formatted hour
    hour = format_time(int(post_time))
    
    # set name of file
    fileName = conditions[conditions['category'] == df.iloc[0]['Category']].iloc[0]['color']

    # generate saying
    saying = "As of {month}/{day}/{year}, {time}:".format(month=month, day=day, year=year, time=hour)

    # store picture
    pic = Image.open('../templates/{color}.png'.format(color=fileName))

    # create draw object from image object
    draw = ImageDraw.Draw(pic)

    # adjust font and text size
    font = ImageFont.truetype("Library/Fonts/GlacialIndifference-Regular.otf", 70)

    # add saying to picture
    draw.text((50, 350), '{saying}'.format(saying=saying), fill='#63625E', font=font)

    # add AQI to the picture
    font = ImageFont.truetype("Library/Fonts/GlacialIndifference-Bold.otf", 150)
    draw.text((90, 470), '{value}'.format(value=df.iloc[0]['AQI']), fill='#000000', font=font)

    # save photo to 'finished' folder
    finished_pic = '../finished/{month}-{day}-{year}-{post_time}.png'.format(month=month, day=day, year=year, post_time=post_time)
    pic.save(finished_pic)
    
    #post tweet
    api = twitter_api()

    media = api.media_upload(finished_pic)
    if post_time == 8:
        api.update_status(status='Good morning ☀️ ' + df['message'][0], media_ids=[media.media_id])
    else:
        api.update_status(status='Good afternoon 🍂 ' + df['message'][0], media_ids=[media.media_id])
    
    print("just posted tweet for {month}/{day}/{year} at {hour}!".format(month=month, day=day, year=year, time=hour))

    """run scheduled job"""
    schedule.every().day.at("08:00").do(post, post_time='8')
    schedule.every().day.at("15:00").do(post, post_time='15')

    while True:
        schedule.run_pending()
        time.sleep(1)
        
# post tweet
post_tweet()
