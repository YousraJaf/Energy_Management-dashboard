import streamlit as st
import pandas as pd
import holoviews as hv
from holoviews import opts
hv.extension('bokeh')

st.set_option('deprecation.showPyplotGlobalUse', False)
option = st.sidebar.selectbox("Which Dashboard?", ('Energy Management Dashboard', 'Usage by rooms and appliances', 'Anticipate next month’s consumption'))

###
#read data
path1 = 'smart-meter-data/2014/'
path2 = 'smart-meter-data/2015/'
path3 = 'smart-meter-data/2016/'

smarthome14 = pd.read_csv(path1 + 'Home-meter1_2014.csv')
weather14 = pd.read_csv(path1 + '../home2014.csv')
smarthome15 = pd.read_csv(path2 + 'Home-meter1_2015.csv')
weather15 = pd.read_csv(path2 + '../home2015.csv')
smarthome16 = pd.read_csv(path3 + 'Home-meter1_2016.csv')
weather16 = pd.read_csv(path3 + '../home2016.csv')

# converting half hourly or minutely data to hourly data
smarthome14['Date & Time'] = pd.to_datetime(smarthome14['Date & Time'])
smarthome14 = smarthome14.groupby(pd.Grouper(key="Date & Time", freq="1H")).mean().reset_index()

smarthome15['Date & Time'] = pd.to_datetime(smarthome15['Date & Time'])
smarthome15 = smarthome15.groupby(pd.Grouper(key="Date & Time", freq="1H")).mean().reset_index()

smarthome16['Date & Time'] = pd.to_datetime(smarthome16['Date & Time'])
smarthome16 = smarthome16.groupby(pd.Grouper(key="Date & Time", freq="1H")).mean().reset_index()

smarthome_frames = [smarthome14, smarthome15, smarthome16]
smarthome = pd.concat(smarthome_frames)

#smarthome[smarthome.isnull().any(axis=1)]
smarthome.drop([1610, 1586, 1730], inplace=True)

# convert unix timestamp to datetime
weather14['Date & Time'] = pd.to_datetime(weather14['time'],unit='s')
weather15['Date & Time'] = pd.to_datetime(weather15['time'],unit='s')
weather16['Date & Time'] = pd.to_datetime(weather16['time'],unit='s')

weather_frames = [weather14, weather15, weather16]
weather = pd.concat(weather_frames)

#weather.isna().sum().reset_index(name="missing_value").plot.bar(x='index', y='missing_value', rot=90, color='red')

# deal with missing values
weather['cloudCover'].replace(['cloudCover'], method='bfill', inplace=True)
weather['cloudCover'] = weather['cloudCover'].astype('float')
# weather.drop(['cloudCover'], axis=1, inplace=True)

## Let's convert temperature and apparent temperature units to degrees Celsius (°C)
def fahr_to_celsius(temp_fahr):
    """Convert Fahrenheit to Celsius
    
    Return Celsius conversion of input"""
    temp_celsius = (temp_fahr - 32) * 5 / 9
    return temp_celsius

weather['apparentTemperature_Celsius'] = fahr_to_celsius(weather['apparentTemperature'])
weather['temperature_Celsius'] = fahr_to_celsius(weather['temperature'])
weather.drop(['apparentTemperature', 'temperature'], axis=1, inplace=True)

# finally merge the smarthome and weather data
df = pd.merge(smarthome, weather, on="Date & Time")

# ## Ensuring there are no temporal gaps
# import matplotlib.pyplot as plt


# plt.figure(figsize=(10,5))
# df['Date & Time'].plot() 
# plt.xlabel('Reading Count')
# plt.ylabel('Date')
# plt.show()
# st.line_chart(data=df['Date & Time'], width=300, height=400, use_container_width=True)

df.dropna(inplace=True)

## consumption unit is converted into 'kWh' from 'kW', right the monent we aggregated hourly data, so let's drop column names:
for col in df.columns:
    df.rename(columns={col:col.replace(' [kW]', '')}, inplace=True)
    
## a little feature engineering!
df['Furnace'] = df[['Furnace 1', 'Furnace 2']].sum(axis=1)
df['Kitchen'] = df[['Kitchen 12', 'Kitchen 14', 'Kitchen 38']].sum(axis=1)
df.drop(['Furnace 1','Furnace 2','Kitchen 12','Kitchen 14','Kitchen 38', 'time'], axis=1, inplace=True)

## correlation between columns
df_corr = df.corr()

# # corr_heatmap = hv.HeatMap((df_corr.columns, df_corr.index, df_corr > 0.95))
# # corr_heatmap.opts(tools=['hover'], width=1200, height=500, title='Correlation Heatmap', xrotation = 90, colorbar=True, clim=(-1, 1), invert_yaxis=True)
# # corr_heatmap * hv.Labels(corr_heatmap).opts(text_color='white')

## from the correlation heatmap we can see, 'use' - 'House overall' and 'gen' and 'Solar' columns' correlation coefficient is almost over 0.95, 
## so we can consider only one of them and delete the other one.
df['HO_use'] = df['use']
df['Sol_gen'] = df['gen']
df.drop(['use','House overall','gen','Solar'], axis=1, inplace=True)

###

df['Date & Time'] = pd.to_datetime(df['Date & Time'])

df['year'] = df['Date & Time'].dt.year # df['year'] = df['Date & Time'].apply(lambda x : x.year)
df['month'] = df['Date & Time'].dt.month
df['day'] = df['Date & Time'].dt.day
df['weekday'] = df['Date & Time'].dt.day_name()
df['weekofyear'] = df['Date & Time'].dt.isocalendar().week # df['Date & Time'].dt.isocalendar()[['week']]
df['hour'] = df['Date & Time'].dt.hour

df = df.set_index('Date & Time')
# df_day = df.groupby(pd.Grouper(freq='1D')).mean()
# df_month = df.groupby(pd.Grouper(freq='1M')).mean()
#df.index = pd.to_datetime(df.index)

def periods(x):
    if x in (23, 0, 1, 2, 3, 4, 5):
        period = 'Night'
    elif x in range(5, 9):
        period = 'Morning'
    elif x in range(9, 11):
        period = 'forenoon'
    elif x in range(11, 14):
        period = 'Noon'
    elif x in range(14, 18):
        period = 'Afternoon'
    elif x in range(18, 23):
        period = 'Evening'
    else:
        period = 'None'
    return period    

df['periodsofday'] = df['hour'].apply(periods)

df.rename({'windSpeed': 'windspeed', 'windBearing': 'windbearing', 'precipIntensity': 'precipitation_intensity', 'dewPoint': 'dewpoint', 'precipProbability': 'precipitation_probability', 'apparentTemperature_Celsius': 'apparent_temperature', 'temperature_Celsius': 'temperature'}, axis=1, inplace=True)

# converting 'month' column values from month integers to month name
df['month'] = pd.to_datetime(df['month'], format='%m').dt.month_name().str.slice(stop=3)

def groupbymonth(col):
    #return df[[col, 'month']].groupby(by='month').agg({col:'mean'})[col]
    monthdf = df.groupby('month').agg({col:['mean']})
    monthdf.columns = [f"{i[0]}_{i[1]}" for i in monthdf.columns]
    monthdf['month_num'] = [['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(i) for i in monthdf.index]
    monthdf.sort_values('month_num', inplace=True)
    monthdf.drop('month_num', axis=1, inplace=True)
    return monthdf
    
def groupbyweekday(col):
    weekdaydf = df.groupby('weekday').agg({col:['mean']})
    weekdaydf.columns = [f"{i[0]}_{i[1]}" for i in weekdaydf.columns]
    weekdaydf['week_num'] = [['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(i) for i in weekdaydf.index]
    weekdaydf.sort_values('week_num', inplace=True)
    weekdaydf.drop('week_num', axis=1, inplace=True)
    return weekdaydf    
    
def groupbyperiods(col):
    periodsdf = df.groupby('periodsofday').agg({col:['mean']})
    periodsdf.columns = [f"{i[0]}_{i[1]}" for i in periodsdf.columns]
    periodsdf['periods_num'] = [['Morning', 'forenoon', 'Noon', 'Afternoon', 'Evening', 'Night'].index(i) for i in periodsdf.index]
    periodsdf.sort_values('periods_num', inplace=True)
    periodsdf.drop(['periods_num'], axis=1, inplace=True)
    return periodsdf 

def avg_econ_t():
    if genre == 'per day':
        time = 'day'
        df_energy = df.filter(items=['HO_use']).resample('D').mean()
    else:
        time = 'month'
        df_energy = df.filter(items=['HO_use']).resample('M').mean()
    energy_cons = hv.Curve(df_energy).opts(width=800, height=500, xlabel= 'time', ylabel= 'House overall energy in [kW]', title=f'Average energy consumption per {time}', tools=['hover'])
    st.bokeh_chart(hv.render(energy_cons, backend='bokeh'))

def dist():
    if box5 == 'Consumption and Generation':
        use = hv.Distribution(df['HO_use']).opts(title="Total Energy Consumption Distribution", color="red")
        gen = hv.Distribution(df['Sol_gen']).opts(title="Total Energy Generation Distribution", color="blue")
        dist = use + gen
        dist.opts(opts.Distribution(xlabel="Energy Consumption", ylabel="Density", xformatter='%.1fkw', width=600, height=400,tools=['hover'],show_grid=True))
    elif box5 == 'House Appliances':
        dw = hv.Distribution(df[df['Dishwasher']<1.0]['Dishwasher'],label="Dishwasher").opts(color="red")
        ho = hv.Distribution(df[df['Home office']<1.0]['Home office'],label="Home office").opts(color="blue")
        fr = hv.Distribution(df[df['Fridge']<1.0]['Fridge'],label="Fridge Distribution").opts(color="orange")
        wc = hv.Distribution(df[df['Wine cellar']<1.0]['Wine cellar'],label="Wine cellar").opts(color="green")
        gd = hv.Distribution(df[df['Garage door']<1.0]['Garage door'],label="Garage door").opts(color="purple")
        ba = hv.Distribution(df[df['Barn']<1.0]['Barn'],label="Barn").opts(color="grey")
        we = hv.Distribution(df[df['Well']<1.0]['Well'],label="Well").opts(color="pink")
        mcr = hv.Distribution(df[df['Microwave']<1.0]['Microwave'],label="Microwave").opts(color="yellow")
        lr = hv.Distribution(df[df['Living room']<1.0]['Living room'],label="Living room").opts(color="brown")
        fu = hv.Distribution(df[df['Furnace']<1.0]['Furnace'],label="Furnace").opts(color="skyblue")
        ki = hv.Distribution(df[df['Kitchen']<1.0]['Kitchen'],label="Kitchen").opts(color="lightgreen")

        dist = dw * ho * fr * wc * gd * ba * we * mcr * lr * fu * ki
        dist.opts(opts.Distribution(xlabel="Energy Consumption", ylabel="Density", xformatter='%.1fkw',title='Energy Consumption of Appliances Distribution', width=1000, height=500,tools=['hover'],show_grid=True))
    else:
        temp = hv.Distribution(df['temperature'],label="temperature").opts(color="red")
        apTemp = hv.Distribution(df['apparent_temperature'],label="apparentTemperature").opts(color="orange")
        temps = (temp * apTemp).opts(opts.Distribution(title='Temperature Distribution')).opts(legend_position='top',legend_cols=2)
        hmd = hv.Distribution(df['humidity']).opts(color="yellow", title='Humidity Distribution')
        vis = hv.Distribution(df['visibility']).opts(color="blue", title='Visibility Distribution')
        prs = hv.Distribution(df['pressure']).opts(color="green", title='Pressure Distribution')
        wnd = hv.Distribution(df['windspeed']).opts(color="purple", title='WindSpeed Distribution')
        prc = hv.Distribution(df['precipitation_intensity']).opts(color="skyblue", title='PrecipIntensity Distribution')
        dew = hv.Distribution(df['dewpoint']).opts(color="lightgreen", title='DewPoint Distribution')

        dist = temps + hmd + vis + prs + wnd + prc + dew
        dist.opts(opts.Distribution(xlabel="Values", ylabel="Density", width=600, height=400,tools=['hover'],show_grid=True)).cols(2)
    st.bokeh_chart(hv.render(dist, backend='bokeh'))
    
def ts_congen():
    if box1 == 'by day':
        use = hv.Curve(df.filter(items=['HO_use']).resample('D').mean()).opts(title="Total Energy Consumption Time-Series by Day", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(df.filter(items=['Sol_gen']).resample('D').mean()).opts(title="Total Energy Generation Time-Series by Day", color="blue", ylabel="Energy Generation")
        xlab = "Day"
    elif box1 == 'by month':
        use = hv.Curve(groupbymonth('HO_use')).opts(title="Total Energy Consumption Time-Series by Month", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(groupbymonth('Sol_gen')).opts(title="Total Energy Generation Time-Series by Month", color="blue", ylabel="Energy Generation")
        xlab = "Month"
    elif box1 == 'by weekdays':
        use = hv.Curve(groupbyweekday('HO_use')).opts(title="Total Energy Consumption Time-Series by Weekdays", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(groupbyweekday('Sol_gen')).opts(title="Total Energy Generation Time-Series by Weekdays", color="blue", ylabel="Energy Generation")
        xlab = "Weekdays"
    else:
        use = hv.Curve(groupbyperiods('HO_use')).opts(title="Total Energy Consumption Time-Series by Periods of day", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(groupbyperiods('Sol_gen')).opts(title="Total Energy Generation Time-Series by Periods of day", color="blue", ylabel="Energy Generation")
        xlab = "Periods of day"
    line = use + gen
    line.opts(opts.Curve(xrotation = 90, xlabel=xlab, yformatter='%.2fkw', width=600, height=400,tools=['hover'],show_grid=True,fontsize={'title':10}))
    st.bokeh_chart(hv.render(line, backend='bokeh'))

    
cols = ['Dishwasher', 'Home office', 'Fridge', 'Wine cellar', 'Garage door', 'Barn',  'Well', 'Microwave', 'Living room', 'Furnace', 'Kitchen']
colors = ["red",  "teal", "blue", "magenta", "orange", "green", "brown", "purple", "grey", "salmon", "turquoise"]

curve_Items = ['dw', 'ho', 'fr', 'wc', 'gd', 'ba', 'we', 'mcr', 'lr', 'fu', 'ki']    
def appl_ts():
    for items in range(len(cols)):
        if box2 == 'by day':
            curve_Items[items] = hv.Curve(df[cols[items]].resample('D').mean(),label=f"{cols[items]} Time-Series by Day").opts(color=colors[items])
            #xlab="Day"
        elif box2 == 'by month':
            curve_Items[items] = hv.Curve(groupbymonth(cols[items]),label=f"{cols[items]} Time-Series by Month").opts(color=colors[items])
            #xlab="Month"
        elif box2 == 'by weekdays':
            curve_Items[items] = hv.Curve(groupbyweekday(cols[items]),label=f"{cols[items]} Time-Series by Weekday").opts(color=colors[items])
            #xlab="Weekdays"
        else:
            curve_Items[items] = hv.Curve(groupbyperiods(cols[items]),label=f"{cols[items]} Time-Series by Timing").opts(color=colors[items])
            #xlab="Periods of day"
    return curve_Items

weather_element = ['apparent_temperature', 'humidity', 'visibility', 'pressure', 'windspeed', 'precipitation_intensity', 'dewpoint']
ts_items = ['apTemp', 'hmd', 'vis', 'prs', 'wnd', 'prc', 'dew']
def weather_ts():
    for items in range(len(weather_element)):
        if box3 == 'by day':
            ts_items[items] = hv.Curve(df[weather_element[items]].resample('D').mean()).opts(color=colors[items], title=f'{weather_element[items]} Time-Series by Day')
            #xlab = "Day"
        elif box3 == 'by month':
            ts_items[items] = hv.Curve(groupbymonth(weather_element[items]),label=f"{weather_element[items]} Time-Series by Month").opts(color=colors[items])
            #xlab = "Months"
        elif box3 == 'by weekdays':
            ts_items[items] = hv.Curve(groupbyweekday(weather_element[items]),label=f"{weather_element[items]} Time-Series by Weekdays").opts(color=colors[items])
            #xlab = "Weekdays"
        else:
            ts_items[items] = hv.Curve(groupbyperiods(weather_element[items]),label=f"{weather_element[items]} Time-Series by Periods of day").opts(color=colors[items])
            #xlab = "Periods of day"
    return ts_items
      
# prox = [df_day, df_month]
# def atem_vscon():
#     if box4 == 'day':
#         data = prox[0]
#     else:
#         data = prox[1]
        
#     scatter = hv.Scatter(data, kdims='apparentTemperature_Celsius', vdims='HO_use')
#     scatter.opts(width=800, height=500, title='Relation between apparent Temperature and Household overall energy consumption', xlabel='apparent Temperature in [°C]', ylabel='Consumption in [kWh]')
#     st.bokeh_chart(hv.render(scatter, backend='bokeh')) 
    
def energy_dist():
    if option1 == 'rooms':
        df_sub = df.filter(items=['Home office', 'Wine cellar', 'Barn', 'Living room', 'Kitchen'])
    elif option1 == 'devices':    
        df_sub = df.filter(items=['Dishwasher', 'Furnace',  'Fridge', 'Garage door', 'Well', 'Microwave'])
        with st.expander("See explanation"):
             st.write("""
         Watch out! Your Furnace is eating up all the energy!
     """)
    else:
        df_sub = df.filter(items=['Home office', 'Wine cellar', 'Barn', 'Living room', 'Kitchen', 'Dishwasher', 'Furnace',  'Fridge', 'Garage door', 'Well', 'Microwave'])
        with st.expander("See explanation"):
             st.write("""
         Watch out! Your Furnace is eating up all the energy!
     """)

    sub_sum = pd.DataFrame(df_sub.sum(axis=0), columns=['total_energy_consumption'])
    bar_chart = hv.Bars(sub_sum).opts(opts.Bars(color='blue', ylim=(0, 5600)))
    hline = hv.HLine(3500).opts(color='red', line_dash='dashed', line_width=2.0)
    bars =  bar_chart * hline
    bars.opts(xrotation=90, width=600, height=400, xlabel=f'{option1}', ylabel='Consumption [kWh]', title=f'Total Consumption by all {option1} in [kWh] from 2014-2016' )    
    st.bokeh_chart(hv.render(bars, backend='bokeh'))
    


######################################################################################################################################################

if option == 'Energy Management Dashboard':
    st.header('Energy Dashboard')
#     st.subheader("Missing timestamp?")
#     """
#     To ensure that there is no temporal gaps in the data, i.e. there is no abrupt time jump or missing timestamp, the timestamp v/s index is plotted.
#     """
#     st.image("timestamp.jpg")
    
             
#     st.subheader("Here's how our dataframe (for hourly redaing) looks like after cleaning:")
#     st.dataframe(df)
    
    st.subheader("Average energy consumption")
    radio1_names = ['per day', 'per month']
    genre = st.radio(
     "Plot average energy consumption", radio1_names, index=0)
    avg_econ_t()
    

    st.subheader("Total Energy Consumption and Generation Time-Series")
    box1 = st.selectbox(
     'select options?',
     ('by day', 'by month', 'by weekdays', 'by periods of day'))

    st.write("You've selected total energy consumption and generation time-series", box1) 
    ts_congen()
    with st.expander("See explanation"):
        st.write("""
         with the start of cold season, energy consumption increases from November to February, and gradually decreases after February till May. On the other hand, eneregy generation gradually rises from January to April and reaches its peak at June then slowly declines for the rest of the year.
     """)
    
    st.subheader("Rooms and Appliances Time-Series")
    st.write("select rooms and appliances Time-Series by day, month, weekdays or periods of day:")
    box2 = st.selectbox(
     'select items',
     ('by day', 'by month', 'by weekdays', 'by periods of day'), index=1)
    st.write('You selected:', box2)
    dw, ho, fr, wc, gd, ba, we, mcr, lr, fu, ki = appl_ts()
    appliances_timeseries = dw + ho + fr + wc + gd + ba + we + mcr + lr + fu + ki
    appliances_timeseries.opts(opts.Curve(xlabel='time', ylabel="Energy Consumption", yformatter='%.2fkw' ,
                                                                           width=450, height=350,tools=['hover'],show_grid=True)).cols(2) 
    st.bokeh_chart(hv.render(appliances_timeseries, backend='bokeh'))
    
    st.subheader("Weather Information Time-Series")
    st.write("select weather elements Time-Series by day, month, weekdays or periods of day:")
    box_names = ['by day', 'by month', 'by weekdays', 'by periods of day']
    box3 = st.selectbox(
     "select time-series", box_names, index=1)
    st.write("You've selected weather element time-series", box3)
    apTemp, hmd, vis, prs, wnd, prc, dew = weather_ts()
    weather_timeseries = apTemp + hmd + vis + prs + wnd + prc + dew
    weather_timeseries.opts(opts.Curve(xlabel='time', ylabel="Values", width=450, height=350,tools=['hover'],show_grid=True)).cols(2)  
    st.bokeh_chart(hv.render(weather_timeseries, backend='bokeh'))
    
    st.subheader("Explore energy consumption distribution")
    radio3_names = ['Consumption and Generation', 'House Appliances', 'Weather Information']
    box5 = st.radio(
     "select which distribution should be plotted?", radio3_names)
    st.write("You've selected", box5, "distribution")
    dist()

#     st.subheader("Relation between apparent Temperature and Household overall energy consumption")
#     box4 = st.selectbox('select by?',
#      ('day', 'month'))
#     st.write("You've selected relation between apparent temperature and household overall energy consumption by", box4)
#     atem_vscon()

elif option == 'Usage by rooms and appliances':
    st.subheader("Total Energy Consumption Distribution")
    option1 = st.radio(
     "Plot distribution for",
     ('rooms', 'devices', 'all features'), index=2)
    
    st.write("You've selected Total Energy Consumption Distribution by", option1)
    energy_dist()
    
else:
    st.write('construction site, still on progress...!')
    st.image('baustelle.jpg')
