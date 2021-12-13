## PART 1: FETCH AQI DATA

# import libraries
import pandas as pd
import requests
import json
from datetime import date

# get today's date
day = date.today().day
month = date.today().month
year = date.today().year

# get post time
post_time = input("Enter the time you want to post the bot: 8 or 15 ")
post_time_2 = int(post_time) + 1
        
# pull data from AirNow
r = requests.get('https://www.airnowapi.org/aq/data/?startDate={year}-{month}-{day}T{time1}&endDate={year}-{month}-{day}T{time2}&parameters=PM25&BBOX=-84.500651,30.275370,-84.080424,30.684863&dataType=B&format=application/json&verbose=1&monitorType=2&includerawconcentrations=0&API_KEY=2BB44069-F9EF-4CA7-8B67-C9832B168B60'.format(day = day, month = month, year = year, time1 = post_time, time2 = post_time_2)).json()

# store in dataframe
df = pd.DataFrame.from_dict(r)

# clean data
df['date'] = df['UTC'].str.split('T').str[0]
df['time'] = df['UTC'].str.split('T').str[1]

df = df.drop(['UTC'], axis=1)

df['Category'] = df['Category'].astype(str)

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

# add conditions to original dataframe
def add_conditions(dataframe):
    for i in range(len(dataframe)):
        dataframe.loc[i, 'status'] = conditions[conditions['category'] == df.loc[i, 'Category']]['status'].loc[0]
        dataframe.loc[i, 'color'] = conditions[conditions['category'] == df.loc[i, 'Category']]['color'].loc[0]
        dataframe.loc[i, 'message'] = conditions[conditions['category'] == df.loc[i, 'Category']]['message'].loc[0]
    return dataframe

add_conditions(df)

# get formatted time
def format_time(post_time):
    if post_time > 12:
        time = post_time - 12
        hour = str(time) + 'PM'
    elif post_time:
        hour = str(post_time) + 'AM'
    return hour

hour = format_time(post_time=13)

# print status check
print("the AQI for {day} {hour} is {AQI}, category {level}".format(day=date.today(), hour = hour, AQI = df.iloc[0]['AQI'], level = df.iloc[0]['Category']))


## PART 2: EDIT PHOTO

# import libraries
from PIL import Image, ImageDraw, ImageFont
from datetime import date

# set name of file
fileName = conditions[conditions['category'] == df.iloc[0]['Category']].iloc[0]['color']

# generate saying
saying = "As of {month}/{day}/{year}, {time}M:".format(month=month, day=day, year=year, time='3P')

# store picture / create image object
pic = Image.open('/Users/shelbygreen/Repositories/aq-bot/templates/{color}.png'.format(color=fileName))

# add saying to the picture
# create draw object from image object
draw = ImageDraw.Draw(pic)

# add font and text size
font = ImageFont.truetype("Library/Fonts/GlacialIndifference-Regular.otf", 70)

# draw on image
draw.text((50, 350), '{saying}'.format(saying=saying), fill='#63625E', font=font)

# add AQI to the picture
# add font and text size
font = ImageFont.truetype("Library/Fonts/GlacialIndifference-Bold.otf", 150)

# draw on image
draw.text((90, 470), '{value}'.format(value=df.iloc[0]['AQI']), fill='#000000', font=font)

pic.save('/Users/shelbygreen/Repositories/aq-bot/templates/{month}-{day}-{year}-{post_time}.png'.format(month=month, day=day, year=year, post_time=post_time))

## PART 3: STORE AQI DATA

# store data in csv
with open('/Users/shelbygreen/Repositories/aq-bot/data/log.csv', 'a') as f:
    df.to_csv(f, header=False)
