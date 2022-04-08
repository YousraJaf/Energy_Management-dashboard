import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import holoviews as hv
from holoviews import opts
hv.extension('bokeh')
import ipywidgets as wg
from IPython.display import display

st.set_option('deprecation.showPyplotGlobalUse', False)
option = st.sidebar.selectbox("Which Dashboard?", ('Energy Management Dashboard', 'Machine Learning'))

#read data
df = pd.read_csv('df.csv')
df['Date & Time'] = pd.to_datetime(df['Date & Time'])

df['year'] = df['Date & Time'].dt.year # df['year'] = df['Date & Time'].apply(lambda x : x.year)
df['month'] = df['Date & Time'].dt.month
df['day'] = df['Date & Time'].dt.day
df['weekday'] = df['Date & Time'].dt.day_name()
df['weekofyear'] = df['Date & Time'].dt.isocalendar().week # df['Date & Time'].dt.isocalendar()[['week']]
df['hour'] = df['Date & Time'].dt.hour

df = df.set_index('Date & Time')
df_day = df.groupby(pd.Grouper(freq='1D')).mean()
df_month = df.groupby(pd.Grouper(freq='1M')).mean()
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

def avg_econ_t():
    if genre == 'per day':
        time = 'day'
        df_energy = df.filter(items=['HO_use']).resample('D').mean()
    else:
        time = 'month'
        df_energy = df.filter(items=['HO_use']).resample('M').mean()
    energy_cons = hv.Curve(df_energy).opts(width=800, height=500, xlabel= 'time', ylabel= 'House overall energy in [kW]', title=f'Average energy consumption per {time}', tools=['hover'])
    st.bokeh_chart(hv.render(energy_cons, backend='bokeh'))
    
def tsday_congen():
    use = df.filter(items=['HO_use']).resample('D').mean()
    line1 = hv.Curve(use).opts(title="Total Energy Consumption Time-Series by Day", color="red", ylabel="Energy Consumption")

    gen  = df.filter(items=['Sol_gen']).resample('D').mean()
    line2 = hv.Curve(gen).opts(title="Total Energy Generation Time-Series by Day", color="blue", ylabel="Energy Generation")
    
    mult_line_plot = line1 + line2
    mult_line_plot.opts(opts.Curve(xlabel="Time", yformatter='%.2fkw', width=500, height=300, line_width=0.60, tools=['hover'], show_grid=True,fontsize={'title':11}))
    st.bokeh_chart(hv.render(mult_line_plot, backend='bokeh'))
    
def groupbymonth(col):
    return df[[col, 'month']].groupby(by='month').agg({col:'mean'})[col]
    
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
    
def ts_congen():
    if box1 == 'by day':
        tsday_congen()
    elif box1 == 'by month':
        use = hv.Curve(groupbymonth('HO_use')).opts(title="Total Energy Consumption Time-Series by Month", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(groupbymonth('Sol_gen')).opts(title="Total Energy Generation Time-Series by Month", color="blue", ylabel="Energy Generation")
        xlab = "Month"
    elif box1 == 'by weekdays':
        use = hv.Curve(groupbyweekday('HO_use')).opts(title="Total Energy Consumption Time-Series by Month", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(groupbyweekday('Sol_gen')).opts(title="Total Energy Generation Time-Series by Month", color="blue", ylabel="Energy Generation")
        xlab = "Weekdays"
    else:
        use = hv.Curve(groupbyperiods('HO_use')).opts(title="Total Energy Consumption Time-Series by Periods of day", color="red", ylabel="Energy Consumption")
        gen = hv.Curve(groupbyperiods('Sol_gen')).opts(title="Total Energy Generation Time-Series by Periods of day", color="blue", ylabel="Energy Generation")
        xlab = "Periods of day"
    line = use + gen
    line.opts(opts.Curve(xrotation = 90, xlabel=xlab, yformatter='%.2fkw', width=400, height=300,tools=['hover'],show_grid=True,fontsize={'title':10}))
    st.bokeh_chart(hv.render(line, backend='bokeh'))
    

appliances = ['Home office', 'Wine cellar', 'Barn', 'Living room', 'Kitchen', 'Dishwasher', 'Furnace',  'Fridge', 'Garage door', 'Well', 'Microwave']
app_colors = ["red", "orange", "blue", "yellow", "green", "grey", "purple", "pink", "skyblue", "lightgreen", "brown"]

def appl_ts():
    for index in range(len(appliances)):
        e = appliances[index] 
        c = app_colors[index] 
        t = f'{appliances[index]} timeseries'
        if e == box2:
            element = e
            color = c
            title = t
            if box2 == 'by day':
                appliances_timeseries = hv.Curve(df[element].resample('D').mean(),label=f'{title} by Day').opts(color=color)
                xlab = 'Day'
            elif box2 == 'by month':
                appliances_timeseries = hv.Curve(groupbymonth(element),label=f'{title} by Month').opts(color=color)
                xlab = 'Month'
            elif box2 == 'by weekdays':
                appliances_timeseries = hv.Curve(groupbyweekday(element),label=f'{title} by Weekdays').opts(color=color)
                xlab = 'Weekdays'  
            else:
                appliances_timeseries = hv.Curve(groupbyperiods(element),label=f'{title} by Periods of Day').opts(color=color)
                xlab = 'Periods of day'   
        
    appliances_timeseries.opts(opts.Curve(xrotation=30, xlabel=xlab, ylabel="Energy Consumption", line_width=0.75, yformatter='%.2fkw' , width=600, height=400, tools=['hover'], show_grid=True))   
    st.bokeh_chart(hv.render(appliances_timeseriesopts, backend='bokeh'))    
    
    
def dist_appl():
    hopd = hv.Distribution(df[df['Home office']<1.1]['Home office'], label="Home office").opts(color="blue")
    wcpd = hv.Distribution(df[df['Wine cellar']<1.1]['Wine cellar'], label="Wine cellar").opts(color="green")
    bpd = hv.Distribution(df[df['Barn']<1.1]['Barn'], label="Barn").opts(color="grey")
    lrpd = hv.Distribution(df[df['Living room']<1.1]['Living room'], label="Living room").opts(color="brown")
    kpd = hv.Distribution(df[df['Kitchen']<1.1]['Kitchen'], label="Kitchen").opts(color="lightgreen")
    dwpd = hv.Distribution(df[df['Dishwasher']<1.1]['Dishwasher'], label="Dishwasher").opts(color="red")
    fpd = hv.Distribution(df[df['Furnace']<1.1]['Furnace'], label="Furnace").opts(color="skyblue")
    frpd = hv.Distribution(df[df['Fridge']<1.1]['Fridge'], label="Fridge Distribution").opts(color="orange")
    gdpd = hv.Distribution(df[df['Garage door']<1.1]['Garage door'], label="Garage door").opts(color="purple")
    wpd = hv.Distribution(df[df['Well']<1.1]['Well'], label="Well").opts(color="pink")
    mcrpd = hv.Distribution(df[df['Microwave']<1.1]['Microwave'], label="Microwave").opts(color="yellow")
    
    distribution = (hopd * wcpd * bpd * lrpd * kpd * dwpd * fpd * frpd * gdpd * wpd * mcrpd)
    distribution.opts(opts.Distribution(xlabel="Energy Consumption", ylabel="Density", xformatter='%.2fkw',title='Energy Consumption of Appliances Distribution', width=800, height=350,tools=['hover'],show_grid=True))
    st.bokeh_chart(hv.render(distribution, backend='bokeh'))


def energy_dist():
    if option1 == 'rooms':
        df_sub = df.filter(items=['Home office', 'Wine cellar', 'Barn', 'Living room', 'Kitchen'])
    elif option1 == 'devices':    
        df_sub = df.filter(items=['Dishwasher', 'Furnace',  'Fridge', 'Garage door', 'Well', 'Microwave'])
    else:
        df_sub = df.filter(items=['Home office', 'Wine cellar', 'Barn', 'Living room', 'Kitchen', 'Dishwasher', 'Furnace',  'Fridge', 'Garage door', 'Well', 'Microwave'])

    sub_sum = pd.DataFrame(df_sub.sum(axis=0), columns=['total_energy_consumption'])
    bar_chart = hv.Bars(sub_sum)
    bar_chart.opts(xrotation=90, width=600, height=400, xlabel=f'{option}', ylabel='Consumption [kWh]', title=f'Total Consumption by all {option} in [kWh] from 2014-2016' )    
    st.bokeh_chart(hv.render(bar_chart, backend='bokeh'))

prox = [df_day, df_month]
def atem_vscon():
    if box4 == 'day':
        data = prox[0]
    else:
        data = prox[1]
        
    scatter = hv.Scatter(data, kdims='apparentTemperature_Celsius', vdims='HO_use')
    scatter.opts(width=800, height=500, title='Relation between apparent Temperature and Household overall energy consumption', xlabel='apparent Temperature in [°C]', ylabel='Consumption in [kWh]')
    st.bokeh_chart(hv.render(scatter, backend='bokeh')) 
    
    
weather_elements = ['humidity','visibility', 'pressure', 'windspeed', 'windbearing', 'precipitation_intensity', 'dewpoint', 'precipitation_probability', 
                    'apparent_temperature', 'temperature']
colors = ["red", "orange", "blue", "yellow", "green", "grey", "purple", "pink", "skyblue", "lightgreen"]
def weat_dist():
    for index in range(len(weather_elements)):
        e = weather_elements[index] 
        c = colors[index] 
        t = f'{weather_elements[index]} distribution'
        if e == box5:
            element = e
            color = c
            title = t
        
    weatherelement_dist = hv.Distribution(df[element]).opts(color=color, title=title)
    weatherelement_dist.opts(opts.Distribution(xlabel="Values", ylabel="Density", width=600, height=400, tools=['hover'],show_grid=True))   
    st.bokeh_chart(hv.render(weatherelement_dist, backend='bokeh'))


######################################################################################################################################################


st.header(option)
if option == 'Energy Management Dashboard':
    st.subheader("Missing timestamp?")
    """
    To ensure that there is no temporal gaps in the data, i.e. there is no abrupt time jump or missing timestamp, the timestamp v/s index is plotted.
    """
    st.image("timestamp.jpg")
    
             
    st.subheader("Here's how our dataframe (for hourly redaing) looks like after cleaning:")
    st.dataframe(df)
    
    st.subheader("Average energy consumption")
    genre = st.radio(
     "Plot average energy consumption",
     ('per day', 'per month'))
    avg_econ_t()
    #st.expander

    st.subheader("Total Energy Consumption and Generation Time-Series")
    box1 = st.selectbox(
     'select options?',
     ('by day', 'by month', 'by weekdays', 'by periods of day'))

    st.write("You've selected total energy consumption and generation time-series", box1) 
    ts_congen()
    
    st.subheader("Rooms and Appliances Time-Series")
    st.write("select rooms and appliances Time-Series by day, month, weekdays or periods of day")
    box2 = st.selectbox(
     'select items',
     ('by day', 'by month', 'by weekdays', 'by periods of day'))
    st.write('You selected:', box2)
    appl_ts()
    
    st.subheader("Weather Information Time-Series")
    box3 = st.radio(
     "select which weather element should be distributed?",
     ('temperature', 'apparent_temperature', 'humidity', 'visibility', 'pressure', 
          'windspeed', 'windbearing', 'precipitation_intensity', 'dewpoint', 'precipitation_probability'))
    st.write("You've selected", box3, "time-series")    
        
    st.subheader("Energy Consumption of Appliances Distribution")
    dist_appl()
    
    st.subheader("Relation between apparent Temperature and Household overall energy consumption")
    box4 = st.selectbox('select by?',
     ('day', 'month'))
    st.write("You've selected relation between apparent temperature and household overall energy consumption by", box4)
    atem_vscon()
    
    st.subheader("Weather element distribution")
    box5 = st.radio(
     "select which weather element should be distributed?",
     ('temperature', 'apparent_temperature', 'humidity', 'visibility', 'pressure', 
          'windspeed', 'windbearing', 'precipitation_intensity', 'dewpoint', 'precipitation_probability'))
    st.write("You've selected", box5, "distribution")
    weat_dist()
    
#     options = st.multiselect(
#      'What are your favorite colors',
#      ['Green', 'Yellow', 'Red', 'Blue'],
#      ['Yellow', 'Red'])

#     st.write('You selected:', options)
    
    st.subheader("Total Energy Consumption Distribution")
    option1 = st.radio(
     "Plot distribution for",
     ('rooms', 'devices', 'all'))
    
    st.write("You've selected Total Energy Consumption Distribution by", option1)
    energy_dist()
        
   
   

    
