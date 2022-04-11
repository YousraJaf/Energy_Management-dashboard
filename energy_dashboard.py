import streamlit as st
import pandas as pd
import holoviews as hv
from holoviews import opts
hv.extension('bokeh')

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
    

# appliances = ['Home office', 'Wine cellar', 'Barn', 'Living room', 'Kitchen', 'Dishwasher', 'Furnace',  'Fridge', 'Garage door', 'Well', 'Microwave']
# app_colors = ["red", "orange", "blue", "yellow", "green", "grey", "purple", "pink", "skyblue", "lightgreen", "brown"]

def appl_ts():
    if box2 == 'by day': 
        dw = hv.Curve(df['Dishwasher'].resample('D').mean(),label="Dishwasher Time-Series by Day").opts(color="red")
        ho = hv.Curve(df['Home office'].resample('D').mean(),label="Home office Time-Series by Day").opts(color="blue")
        fr = hv.Curve(df['Fridge'].resample('D').mean(),label="Fridge Time-Series by Day").opts(color="orange")
        wc = hv.Curve(df['Wine cellar'].resample('D').mean(),label="Wine cellar Time-Series by Day").opts(color="green")
        gd = hv.Curve(df['Garage door'].resample('D').mean(),label="Garage door Time-Series by Day").opts(color="purple")
        ba = hv.Curve(df['Barn'].resample('D').mean(),label="Barn Time-Series by Day").opts(color="grey")
        we = hv.Curve(df['Well'].resample('D').mean(),label="Well Time-Series by Day").opts(color="coral")
        mcr = hv.Curve(df['Microwave'].resample('D').mean(),label="Microwave Time-Series by Day").opts(color="yellow")
        lr = hv.Curve(df['Living room'].resample('D').mean(),label="Living room Time-Series by Day").opts(color="brown")
        fu = hv.Curve(df['Furnace'].resample('D').mean(),label="Furnace Time-Series by Day").opts(color="skyblue")
        ki = hv.Curve(df['Kitchen'].resample('D').mean(),label="Kitchen Time-Series by Day").opts(color="lightgreen")
        xlab="Day"
    elif box2 == 'by month':
        dw = hv.Curve(groupbymonth('Dishwasher'),label="Dishwasher Time-Series by Month").opts(color="red")
        ho = hv.Curve(groupbymonth('Home office'),label="Home office Time-Series by Month").opts(color="blue")
        fr = hv.Curve(groupbymonth('Fridge'),label="Fridge Time-Series by Month").opts(color="orange")
        wc = hv.Curve(groupbymonth('Wine cellar'),label="Wine cellar Time-Series by Month").opts(color="green")
        gd = hv.Curve(groupbymonth('Garage door'),label="Garage door Time-Series by Month").opts(color="purple")
        ba = hv.Curve(groupbymonth('Barn'),label="Barn Time-Series by Month").opts(color="grey")
        we = hv.Curve(groupbymonth('Well'),label="Well Time-Series by Month").opts(color="pink")
        mcr = hv.Curve(groupbymonth('Microwave'),label="Microwave Time-Series by Month").opts(color="yellow")
        lr = hv.Curve(groupbymonth('Living room'),label="Living room Time-Series by Month").opts(color="brown")
        fu = hv.Curve(groupbymonth('Furnace'),label="Furnace Time-Series by Month").opts(color="skyblue")
        ki = hv.Curve(groupbymonth('Kitchen'),label="Kitchen Time-Series by Month").opts(color="lightgreen")
        xlab="Month"
    elif box2 == 'by weekdays':
        dw = hv.Curve(groupbyweekday('Dishwasher'),label="Dishwasher Time-Series by Weekday").opts(color="red")
        ho = hv.Curve(groupbyweekday('Home office'),label="Home office Time-Series by Weekday").opts(color="blue")
        fr = hv.Curve(groupbyweekday('Fridge'),label="FridgeTime-Series by Weekday").opts(color="orange")
        wc = hv.Curve(groupbyweekday('Wine cellar'),label="Wine cellar Time-Series by Weekday").opts(color="green")
        gd = hv.Curve(groupbyweekday('Garage door'),label="Garage door Time-Series by Weekday").opts(color="purple")
        ba = hv.Curve(groupbyweekday('Barn'),label="Barn Time-Series by Weekday").opts(color="grey")
        we = hv.Curve(groupbyweekday('Well'),label="Well Time-Series by Weekday").opts(color="pink")
        mcr = hv.Curve(groupbyweekday('Microwave'),label="Microwave Time-Series by Weekday").opts(color="yellow")
        lr = hv.Curve(groupbyweekday('Living room'),label="Living room Time-Series by Weekday").opts(color="brown")
        fu = hv.Curve(groupbyweekday('Furnace'),label="Furnace Time-Series by Weekday").opts(color="skyblue")
        ki = hv.Curve(groupbyweekday('Kitchen'),label="Kitchen Time-Series by Weekday").opts(color="lightgreen")
        xlab="Weekdays"
    else:
        dw = hv.Curve(groupbyperiods('Dishwasher'),label="Dishwasher Time-Series by Timing").opts(color="red")
        ho = hv.Curve(groupbyperiods('Home office'),label="Home office Time-Series by Timing").opts(color="blue")
        fr = hv.Curve(groupbyperiods('Fridge'),label="FridgeTime-Series by Timing").opts(color="orange")
        wc = hv.Curve(groupbyperiods('Wine cellar'),label="Wine cellar Time-Series by Timing").opts(color="green")
        gd = hv.Curve(groupbyperiods('Garage door'),label="Garage door Time-Series by Timing").opts(color="purple")
        ba = hv.Curve(groupbyperiods('Barn'),label="Barn Time-Series by Timing").opts(color="grey")
        we = hv.Curve(groupbyperiods('Well'),label="Well Time-Series by Timing").opts(color="pink")
        mcr = hv.Curve(groupbyperiods('Microwave'),label="Microwave Time-Series by Timing").opts(color="yellow")
        lr = hv.Curve(groupbyperiods('Living room'),label="Living room Time-Series by Timing").opts(color="brown")
        fu = hv.Curve(groupbyperiods('Furnace'),label="Furnace Time-Series by Timing").opts(color="skyblue")
        ki = hv.Curve(groupbyperiods('Kitchen'),label="Kitchen Time-Series by Timing").opts(color="lightgreen")
        xlab="Periods of day"
        
    appliances_timeseries = dw + ho + fr + wc + gd + ba + we + mcr + lr + fu + ki
    appliances_timeseries.opts(opts.Curve(xlabel=xlab, line_width=0.75, ylabel="Energy Consumption", yformatter='%.2fkw' ,
                                                                           width=600, height=400,tools=['hover'],show_grid=True)).cols(2)
    st.bokeh_chart(hv.render(appliances_timeseries, backend='bokeh'))
    
    
# def dist_appl():
#     hopd = hv.Distribution(df[df['Home office']<1.1]['Home office'], label="Home office").opts(color="blue")
#     wcpd = hv.Distribution(df[df['Wine cellar']<1.1]['Wine cellar'], label="Wine cellar").opts(color="green")
#     bpd = hv.Distribution(df[df['Barn']<1.1]['Barn'], label="Barn").opts(color="grey")
#     lrpd = hv.Distribution(df[df['Living room']<1.1]['Living room'], label="Living room").opts(color="brown")
#     kpd = hv.Distribution(df[df['Kitchen']<1.1]['Kitchen'], label="Kitchen").opts(color="lightgreen")
#     dwpd = hv.Distribution(df[df['Dishwasher']<1.1]['Dishwasher'], label="Dishwasher").opts(color="red")
#     fpd = hv.Distribution(df[df['Furnace']<1.1]['Furnace'], label="Furnace").opts(color="skyblue")
#     frpd = hv.Distribution(df[df['Fridge']<1.1]['Fridge'], label="Fridge Distribution").opts(color="orange")
#     gdpd = hv.Distribution(df[df['Garage door']<1.1]['Garage door'], label="Garage door").opts(color="purple")
#     wpd = hv.Distribution(df[df['Well']<1.1]['Well'], label="Well").opts(color="pink")
#     mcrpd = hv.Distribution(df[df['Microwave']<1.1]['Microwave'], label="Microwave").opts(color="yellow")
    
#     distribution = hopd * wcpd * bpd * lrpd * kpd * dwpd * fpd * frpd * gdpd * wpd * mcrpd
#     distribution.opts(opts.Distribution(xlabel="Energy Consumption", ylabel="Density", xformatter='%.2fkw',title='Energy Consumption of Appliances Distribution', width=800, height=350,tools=['hover'],show_grid=True))
#     st.bokeh_chart(hv.render(distribution, backend='bokeh'))


prox = [df_day, df_month]
def atem_vscon():
    if box4 == 'day':
        data = prox[0]
    else:
        data = prox[1]
        
    scatter = hv.Scatter(data, kdims='apparentTemperature_Celsius', vdims='HO_use')
    scatter.opts(width=800, height=500, title='Relation between apparent Temperature and Household overall energy consumption', xlabel='apparent Temperature in [°C]', ylabel='Consumption in [kWh]')
    st.bokeh_chart(hv.render(scatter, backend='bokeh')) 
    
    
# weather_elements = ['humidity','visibility', 'pressure', 'windspeed', 'windbearing', 'precipitation_intensity', 'dewpoint', 'precipitation_probability', 
#                     'apparent_temperature', 'temperature']
# colors = ["red", "orange", "blue", "yellow", "green", "grey", "purple", "pink", "skyblue", "lightgreen"]
# def weat_dist():
#     for index in range(len(weather_elements)):
#         e = weather_elements[index] 
#         c = colors[index] 
#         t = f'{weather_elements[index]} distribution'
#         if e == box5:
#             element = e
#             color = c
#             title = t
        
#     weatherelement_dist = hv.Distribution(df[element]).opts(color=color, title=title)
#     weatherelement_dist.opts(opts.Distribution(xlabel="Values", ylabel="Density", width=600, height=400, tools=['hover'],show_grid=True))   
#     st.bokeh_chart(hv.render(weatherelement_dist, backend='bokeh'))
    
    

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
    
    st.subheader("Distribution")
    radio3_names = ['Consumption and Generation', 'House Appliances', 'Weather Information']
    box5 = st.radio(
     "select which distribution should be plotted?", radio3_names)
    st.write("You've selected", box5, "distribution")
    dist()
    
    st.subheader("Average energy consumption")
    radio1_names = ['per day', 'per month']
    genre = st.radio(
     "Plot average energy consumption", radio1_names, index=0)
    avg_econ_t()
    #st.expander

    st.subheader("Total Energy Consumption and Generation Time-Series")
    box1 = st.selectbox(
     'select options?',
     ('by day', 'by month', 'by weekdays', 'by periods of day'))

    st.write("You've selected total energy consumption and generation time-series", box1) 
    ts_congen()
    
    st.subheader("Rooms and Appliances Time-Series")
    st.write("select rooms and appliances Time-Series by day, month, weekdays or periods of day:")
    box2 = st.selectbox(
     'select items',
     ('by day', 'by month', 'by weekdays', 'by periods of day'))
    st.write('You selected:', box2)
    appl_ts()
    
#     st.subheader("Weather Information Time-Series")
#     radio2_names = ['temperature', 'apparent_temperature', 'humidity', 'visibility', 'pressure', 
#           'windspeed', 'windbearing', 'precipitation_intensity', 'dewpoint', 'precipitation_probability']
#     box3 = st.radio(
#      "select which weather element should be distributed?", radio2_names, index=0)
#     st.write("You've selected", box3, "time-series")    
        
#     st.subheader("Energy Consumption of Appliances Distribution")
#     dist_appl()
    
    st.subheader("Relation between apparent Temperature and Household overall energy consumption")
    box4 = st.selectbox('select by?',
     ('day', 'month'))
    st.write("You've selected relation between apparent temperature and household overall energy consumption by", box4)
    atem_vscon()
    
#     st.subheader("Total Energy Consumption Distribution")
#     option1 = st.radio(
#      "Plot distribution for",
#      ('rooms', 'devices', 'all'))
    
#     st.write("You've selected Total Energy Consumption Distribution by", option1)
#     energy_dist()
        
   
   

    
