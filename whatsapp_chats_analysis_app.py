# -*- coding: utf-8 -*-
"""Whatsapp Chats Analysis App.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1i3SPjvoV2DQ6DE_ZPyT8t_gtbMnFxdUF
"""

# Commented out IPython magic to ensure Python compatibility.
import re
import regex
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as animation
from os import path
from datetime import *
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import bar_chart_race as bcr
# %matplotlib inline

# Function to check if the given line starts with a DateTime of the required format.
def startsWithDateTime(line):
  pattern = '^[0-9]+\/[0-9]+\/[0-9]+,\s[0-9]+:[0-9][0-9]\s(am|pm|AM|PM)\s-' # Regular Expression to identify the DateTime format.
  result = re.match(pattern, line)
  if result:
    return True
  else:
    return False

# Function to check if the given line starts with a DateTime of the required format.
def startsWithAuthor(line):
  patterns = [
        '([\w]+):',                             # First Name
        '([\w]+[\s]+[\w]+):',                   # First Name + Last Name
        '([\w]+[\s]+[\w]+[\s]+[\w]+[\s]*[\d]*):',    # First Name + Middle Name + Last Name + Digits
        '([+]\d{2} \d{5} \d{5}):',              # Mobile Number (India)
        '([+]\d{2} \d{3} \d{3} \d{4}):',        # Mobile Number (US)
        '([\w]+)[\u263a-\U0001f999]+:',         # Name and Emoji
        '^([\w]+(?:[\s]+[\w]+)*):'
    ]
  pattern = '^' + '|'.join(patterns)
  result = re.match(pattern, line)
  if result:
      return True
  return False

# This is a function which will extract date, time, author, and message from the line.
def getDataPoint(line):
  # line = 06/03/21, 2:30 am - RK: hello.
  splitLine = line.split(' - ')  # splitLine = ['06/03/21, 2:30 am', 'RK: hello.']
  dateTime = splitLine[0] # dateTime = '03/06/21, 2:30 am'
  date, time = dateTime.split(', ') # date = '03/06/21'; time = '2:30 am'
  message = ' '.join(splitLine[1:]) # message = 'RK: hello.'
  author = None
  if startsWithAuthor(message):
    splitMessage = message.split(':') # splitMessage = ['RK', 'hello.']
    author = splitMessage[0] # author = 'RK'
    message = ' '.join(splitMessage[1:]) # message = ' hello.'
  else:
    author = None
  return date, time, author, message

def parsedFile(textFile):
  parsedData = []
  with open(textFile, encoding='utf-8') as fp:
    messageBuffer = []
    line = None
    date, time, author = None, None, None
    n = 0
    while True:
      line = fp.readline()
      if not line:
        print("count:", n)
        break
      line = line.strip()
      if startsWithDateTime(line):
        n += 1
        if len(messageBuffer) > 0:
          parsedData.append([date, time, author, ' '.join(messageBuffer)])
        messageBuffer.clear()
        date, time, author, message = getDataPoint(line)
        messageBuffer.append(message)
      else:
        messageBuffer.append(line)
    parsedData.append([date, time, author, ' '.join(messageBuffer)])
    return parsedData

textFile = '/content/drive/MyDrive/tRIP Chats Backup/WhatsApp Chat with CMPE 202 Team.txt'
parsedFile = parsedFile(textFile)

# Define the parse_time function
def parse_time(time_str):
    try:
        # Try parsing as 12-hour format
        return datetime.strptime(time_str, "%I:%M %p")
    except ValueError:
        try:
            # Try parsing as 24-hour format
            return datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return None  # Return None for invalid formats

chats = pd.DataFrame(parsedFile, columns = ['Date', 'Time', 'Author', 'Message'])
chats['Date'] = pd.to_datetime(chats['Date'])
# chats['Time'] = pd.to_datetime(chats['Time'], format='%I:%M %p').dt.strftime('%I:%M %p')
chats['Time'] = chats['Time'].apply(parse_time)

chats

print("Before dropna():", chats.shape)
before = chats.shape[0]
chats = chats.dropna()
after = chats.shape[0]
print("After dropna():", chats.shape)
print("Difference:", before - after)

# changing datatype of 'Author' column to str.
chats = chats.astype ({"Author": str, "Message": str})
chats

# Prepare the data
data = pd.DataFrame(chats['Author'].value_counts()).reset_index()
data.columns = ['Name', 'Message Count']


# Create the Plotly horizontal bar chart
fig = px.bar(
    data,
    x='Message Count',
    y='Name',
    orientation='h',
    title='Message Count Ranking',
    text='Message Count'  # Display message count on the bars
)

# Update layout for better appearance
fig.update_layout(
    xaxis_title='Number of Messages',
    yaxis_title='Member',
    title_font_size=20,
    xaxis=dict(title_font=dict(size=20)),
    yaxis=dict(title_font=dict(size=20)),
    font=dict(size=12)
)

# Invert the y-axis to match the Matplotlib version
fig.update_yaxes(autorange='reversed')

# Show the figure
fig.show()

# making 1 variable out of all messages.
# exclude_messages_list = ['this message has been deleted', 'was added to chat', 'was removed from chat', 'left chat', 'sticker']
text = ' '.join(str(msg) for msg in chats.Message)

# wordcloud
stopwords = set(STOPWORDS)
# stopwords.update(['ha', 'haa', 'bc', 'mkc', 'and', 'toh','hai', 'na', 'a', 'an', 'the', 'XD', 'xD', 'kya', 'ka', 'mai', 'nhi', 'ye', 'bhi', 'nahi', 'sab', 'ab', 'aaya', 'abhi', 'vo', 'koi', 'wo', 'ko', 're', 'hi', 'tha', 'se', 'aur', 'ke', 'tu', 'woh', 'ki'])
stopwords.update([ 'Media', 'omitted', 'message', 'deleted', 'percentage', 'cgpa'])
wordcloud = WordCloud(width=1600, height=800, stopwords=stopwords, background_color="white").generate(text)
plt.figure(figsize=(20,10))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()

date_df = chats.groupby("Date")['Message'].count()
idx = pd.date_range(date_df.index.min(), date_df.index.max())
date_df.index = pd.DatetimeIndex(date_df.index)
date_df = date_df.reindex(idx, fill_value=0)
date_df = date_df.to_frame()
date_df.reset_index(inplace=True)
date_df.rename(columns = {'index':'Date', 'Message':'MessageCount'}, inplace = True)
# date_df['7DayMA'] = date_df.iloc[:,1].rolling(window = 7).mean()
fig = go.Figure()
fig.add_trace(go.Scatter(x=date_df.Date, y=date_df.MessageCount,
                    mode='lines',
                    name='No of Messages',
                    ))
# fig.add_trace(go.Scatter(x=date_df.Date, y=date_df["7DayMA"],
#                     mode='lines+markers',
#                     name='7 Day Moving Average',
#                     ))
# fig.update_traces(mode="markers+lines", hovertemplate=None)
fig.update_layout(hovermode='x')
# fig.update_traces(hovertemplate = '%{Date}: <br>Message Count: %{MessageCount} </br> %{7DayMA}')
fig.update_layout(
    title="Progression of Messages",
    xaxis_title="Date",
    yaxis_title="Number of Messages",
)
fig.update_xaxes(nticks=20)
fig.show()

def dayofweek(i):
  l = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
  return l[i];
day_df=pd.DataFrame(chats["Message"])
day_df['day_of_date'] = chats['Date'].dt.weekday
day_df['day_of_date'] = day_df["day_of_date"].apply(dayofweek)
day_df["messagecount"] = 1
day = day_df.groupby("day_of_date").sum()
day.reset_index(inplace=True)

fig = px.pie(day, values='messagecount', names='day_of_date', title='tRIP Messages by Day of the Week')
fig.update_traces(textposition='inside', textinfo='percent+label+value')
fig.show()

times = pd.DatetimeIndex(chats.Time)
times_df = pd.DataFrame(times.hour.value_counts())
times_df.sort_index(axis = 0, inplace=True)
times_df.reset_index(inplace=True)
times_df.rename(columns={'Time':'Hour', 'count':'MessageCount'}, inplace=True)
times_df['Hour'] = pd.to_datetime(times_df['Hour'], format='%H').dt.strftime('%I %p')
times_df

import plotly.express as px
fig = px.bar(times_df, x='Hour', y='MessageCount', title='Hour Wise Distribution', labels={'x':'Hour'}, text='MessageCount', color=times_df['Hour'])
fig.show()

data = chats[['Date', 'Author']]
data = chats.groupby([chats.Date, chats.Author]).size().unstack(fill_value=0).stack()
data = pd.DataFrame(data).reset_index()
data.rename(columns = {0:'Frequency'}, inplace = True)
data.head(20)

df = pd.pivot_table(data, index = 'Date', columns = ['Author'], values = 'Frequency')
df1 = df.cumsum(axis = 0) # cumulative sum
df.head()

# Get the last row and repeat it for additional frames
last_row = df1.iloc[[-1]]  # Get the last row
n_extra_frames = 30       # Number of extra frames to freeze
last_row_repeated = pd.concat([last_row] * n_extra_frames)
df_extended = pd.concat([df1, last_row_repeated])

bcr.bar_chart_race(df =  df_extended, title = 'Chats Messages Race', steps_per_period=3, period_length=200, interpolate_period=False, fixed_max=True)