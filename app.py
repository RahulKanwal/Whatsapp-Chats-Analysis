import streamlit as st
import pandas as pd
import re
from datetime import datetime
from wordcloud import WordCloud, STOPWORDS
import plotly.express as px
import plotly.graph_objects as go
import bar_chart_race as bcr

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

# Streamlit app starts here
st.title("WhatsApp Chat Analysis App")

# File upload section
uploaded_file = st.file_uploader("Upload your WhatsApp chat text file", type=["txt"])

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("uploaded_chat.txt", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Parse the file
    parsed_data = parsedFile("uploaded_chat.txt")
    
    # Create DataFrame
    chats = pd.DataFrame(parsed_data, columns=['Date', 'Time', 'Author', 'Message'])
    
    # Preprocess data
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

    chats['Date'] = pd.to_datetime(chats['Date'])
    chats['Time'] = chats['Time'].apply(parse_time)
    chats.dropna(inplace=True)
    
    st.write("### Parsed Chat Data")
    st.dataframe(chats.head())
    
    # Visualizations
    
    # 1. Message Count by Author
    st.subheader("Message Count by Author")
    data = chats['Author'].value_counts().reset_index()
    data.columns = ['Name', 'Message Count']
    st.dataframe(data)
    fig1 = px.bar(data, x='Message Count', y='Name', orientation='h', title="Message Count Ranking", text='Message Count')
    fig1.update_layout(
    xaxis_title='Number of Messages',
    yaxis_title='Member',
    title_font_size=20,
    xaxis=dict(title_font=dict(size=20)),
    yaxis=dict(title_font=dict(size=20)),
    font=dict(size=12)
    )

    fig1.update_yaxes(autorange='reversed')

    st.plotly_chart(fig1)
    
    # 2. Word Cloud of Messages
    st.subheader("Word Cloud of Messages")
    text = " ".join(str(msg) for msg in chats["Message"])
    
    stopwords = set(STOPWORDS)
    stopwords.update(["Media", "omitted", "message", "deleted"])
    
    wordcloud = WordCloud(width=800, height=400, stopwords=stopwords, background_color="white").generate(text)
    
    st.image(wordcloud.to_array(), use_container_width=True)
    
    # 3. Daily Message Count Trend
    st.subheader("Daily Message Count Trend")
    
    daily_counts = chats.groupby('Date').size().reset_index(name='MessageCount')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=daily_counts['Date'], y=daily_counts['MessageCount'], mode='lines', name='Messages'))
    
    fig2.update_layout(title="Messages Over Time", xaxis_title="Date", yaxis_title="Number of Messages")
    
    st.plotly_chart(fig2)

    # 4. Messages by Day of the week
    def dayofweek(i):
        l = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return l[i]
    day_df=pd.DataFrame(chats["Message"])
    day_df['day_of_date'] = chats['Date'].dt.weekday
    day_df['day_of_date'] = day_df["day_of_date"].apply(dayofweek)
    day_df["messagecount"] = 1
    day = day_df.groupby("day_of_date").sum()
    day.reset_index(inplace=True)

    fig3 = px.pie(day, values='messagecount', names='day_of_date', title='Messages by Day of the Week')
    fig3.update_traces(textposition='inside', textinfo='percent+label+value')
    st.plotly_chart(fig3)

    # 5. Messages by hour of the day
    times = pd.DatetimeIndex(chats.Time)
    times_df = pd.DataFrame(times.hour.value_counts())
    times_df.sort_index(axis = 0, inplace=True)
    times_df.reset_index(inplace=True)
    times_df.rename(columns={'Time':'Hour', 'count':'MessageCount'}, inplace=True)
    times_df['Hour'] = pd.to_datetime(times_df['Hour'], format='%H').dt.strftime('%I %p')
    
    fig4 = px.bar(times_df, x='Hour', y='MessageCount', title='Hour Wise Distribution', labels={'x':'Hour'}, text='MessageCount', color=times_df['Hour'])
    st.plotly_chart(fig4)

    # 6. Bar Chart Race Video
    data = chats[['Date', 'Author']]
    data = chats.groupby([chats.Date, chats.Author]).size().unstack(fill_value=0).stack()
    data = pd.DataFrame(data).reset_index()
    data.rename(columns = {0:'Frequency'}, inplace = True)

    df = pd.pivot_table(data, index = 'Date', columns = ['Author'], values = 'Frequency')
    df1 = df.cumsum(axis = 0) # cumulative sum

    # Get the last row and repeat it for additional frames
    last_row = df1.iloc[[-1]]  # Get the last row
    n_extra_frames = 30       # Number of extra frames to freeze
    last_row_repeated = pd.concat([last_row] * n_extra_frames)
    df_extended = pd.concat([df1, last_row_repeated])

    # Button to trigger video generation
    if st.button("Generate Video"):
        with st.spinner("Generating video... Please wait."):
            # Simulate video generation process (replace with actual logic)              
            bcr.bar_chart_race(df =  df_extended, title = 'Chats Messages Race', filename = 'Chats Bar Chart Race.mp4', steps_per_period=3, period_length=200, interpolate_period=False, fixed_max=True)
            
        st.success("Video generated successfully!")
        
        # Display the generated video
        video_file = open("Chats Bar Chart Race.mp4", "rb")
        video_bytes = video_file.read()
        st.video(video_bytes)

    # bcr.bar_chart_race(df =  df_extended, title = 'Chats Messages Race', filename = 'Chats Bar Chart Race.mp4', steps_per_period=3, period_length=200, interpolate_period=False, fixed_max=True)
    # # Display video in Streamlit
    # video_file = open("Chats Bar Chart Race.mp4", "rb")
    # video_bytes = video_file.read()
    # st.video(video_bytes)