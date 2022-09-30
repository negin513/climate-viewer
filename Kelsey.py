#! /usr/bin/env python
## TODO: clean up imports
#Import Libraries
##%matplotlib inline

import os
import sys
import glob
import argparse
import requests
import time

import numpy as np
import pandas as pd
import xarray as xr
import yaml 

#import plotly.graph_objects as go

from os.path import join, expanduser
from glob import glob

import matplotlib
import matplotlib.pyplot as plt
from scipy import stats

#time-series with Dropdown menu for values

#import yaml
from bokeh.themes import Theme
from bokeh.models import ColumnDataSource, Slider , Dropdown, Select, PreText, Label, Slope, Band
from bokeh.models import (Button, ColumnDataSource, CustomJS, DataTable,
                          NumberFormatter, RangeSlider, TableColumn)
from bokeh.layouts import row,column
# make a simple plot time-series

def in_notebook():
    from IPython import get_ipython
    if get_ipython():
        return True
    else:
        return False  

ShowWebpage = True

if in_notebook():
    ShowWebpage = False

if ShowWebpage:
    pass
else:
    output_notebook()
    
    
df = pd.read_csv('dummy.csv')
col_names = df.columns[df.columns.str.contains(pat = 'TREF')]

for col in col_names:
    df[col] = (df[col]-273.15)*1.8 +32
    
col_names = df.columns[df.columns.str.contains(pat = 'PREC')]

for col in col_names:
    df[col] = (df[col])*1242399685.04

df_all = df

df['time'] =  pd.to_datetime(df['time'], infer_datetime_format=True)
#-- extract year, month, day, hour information from time
df_all['year'] = df_all['time'].dt.year
df_all['month'] = df_all['time'].dt.month
df_all['day'] = df_all['time'].dt.day
df_all['hour'] = df_all['time'].dt.hour

print (df_all)
def get_data (df_all, var, ens, freq='Monthly'):
    df = df_all
    #df_new = df_all
    var_name = var+'_'+ens
    #df_new = pd.DataFrame({'time':df['time'],'var':df[var_name]})
    if ens =='Average'or 'average':
        col_names = df.columns[df.columns.str.contains(pat = var)]
        print (col_names)
        this =  df[col_names].mean(axis=1) 
        df_new = pd.DataFrame({'time':df['time'],'month': df['month'], 'var':this})
    else:
        col_names = df.columns[df.columns.str.contains(pat = var)]
        print (col_names)
        this =  df[col_names].mean(axis=1) 
        df_new = pd.DataFrame({'time':df['time'],'month': df['month'], 'var':this})
        
    print(df_new)
    
    df_monthly = df_new.groupby('month').mean()
    
    if freq =='Monthly':
        df_out = df_new
    elif freq =='Annual':
        print ("Calculating annual average")
        df_new['year'] = pd.DatetimeIndex(df_new['time']).year
        df_dumb = df_new.groupby('year').mean().reset_index()
        print (df_dumb)
        df_dumb_std = df_new.groupby('year').std().reset_index()
        df_dumb["month"] =6
        df_dumb["day"]=30
        print (df_dumb)
        df_dumb['time']=pd.to_datetime(df_dumb[["year", "month","day"]])
        print(df_dumb)
        
        
        df_out = pd.DataFrame({'time':df_dumb['time'],'month': df_dumb['month'], 'var':df_dumb['var']})
        
        df_out['var_lower'] = df_dumb['var']-df_dumb_std['var']
        df_out['var_upper'] = df_dumb['var']+df_dumb_std['var']
        
        
    elif freq =='Decadal':
        
        print ("Calculating decadal average")
        df_new['year'] = pd.DatetimeIndex(df_new['time']).year
        print (df_new)

        df_dumb = df_new.groupby([(df_new.time.dt.year // 10 * 10)]).mean().reset_index()
        df_dumb_std = df_new.groupby([(df_new.time.dt.year // 10 * 10)]).mean().reset_index()

        df_dumb["day"]=1
        df_dumb["month"]=1
        df_dumb["year"]= df_dumb["time"]
        print(df_dumb)

        df_dumb['time']=pd.to_datetime(df_dumb[["year", "month","day"]])
        print ('----')
        df_out = pd.DataFrame({'time':df_dumb['time'],'month': df_dumb['month'], 'var':df_dumb['var']})
        df_out['var_lower'] = df_dumb['var']-df_dumb_std['var']
        df_out['var_upper'] = df_dumb['var']+df_dumb_std['var']
    return df_out, df_monthly 

def get_shaded_data(df_all, var, ens, freq='Monthly'):
    df = df_all
    #df_new = df_all
    df_dumb2 = df
    col_names = df.columns[df.columns.str.contains(pat = var)]

    this =  df[col_names].mean(axis=1) 
    this_std = df[col_names].std(axis=1)
        
    df_out2 = pd.DataFrame({'time':df['time'],'month': df['month'], 'var':this})
        
    df_out2['var_lower'] = this-this_std
    df_out2['var_upper'] = this+this_std
    df_monthly = df_out2.groupby('month').mean()
    
    if freq == 'Monthly':
        df_out = df_out2
    elif freq =='Annual':
        #print ("Calculating annual average")
        #df['year'] = pd.DatetimeIndex(df_new['time']).year
        df_dumb = df.groupby('year').mean().reset_index()
        df_dumb["month"] =6
        df_dumb["day"]=30
        df_dumb['time']=pd.to_datetime(df_dumb[["year", "month","day"]])
        col_names = df.columns[df.columns.str.contains(pat = var)]
        #print (col_names)
        this =  df_dumb[col_names].mean(axis=1) 
        this_std = df_dumb[col_names].std(axis=1)
        
        
        df_out = pd.DataFrame({'time':df_dumb['time'],'month': df_dumb['month'], 'var':this})
        
        df_out['var_lower'] = this-this_std
        df_out['var_upper'] = this+this_std
        
    elif freq =='Decadal':
        
        #print ("Calculating decadal average")

        df_dumb = df.groupby([(df.time.dt.year // 10 * 10)]).mean().reset_index()
        df_dumb['year'] = pd.DatetimeIndex(df_dumb['time']).year

        df_dumb["month"] =6
        df_dumb["day"]=30
        df_dumb["year"]= df_dumb["time"]
        df_dumb['time']=pd.to_datetime(df_dumb[["year", "month","day"]])
        col_names = df.columns[df.columns.str.contains(pat = var)]
        #print (col_names)
        this =  df_dumb[col_names].mean(axis=1) 
        this_std = df_dumb[col_names].std(axis=1)
        
        df_out = pd.DataFrame({'time':df_dumb['time'],'month': df_dumb['month'], 'var':this})
        
        df_out['var_lower'] = this-this_std
        df_out['var_upper'] = this+this_std
        
    #print('=-====')
    #print(df_out)
    print (df_monthly)

    return df_out, df_monthly 


from bokeh.models import ColumnDataSource, Slider , Dropdown, Select, PreText, Label, Slope, Band



def shaded_tseries(doc):
    default_site = 'ABBY'
    default_freq = 'Annual'
    defualt_var = 'SOILWATER_10CM'
    default_ens = 'Average'
    default_var_desc = "Latent Heat Flux [W/m2]"
    df_new, df_monthly = get_shaded_data(df_all, defualt_var,default_ens, default_freq)
    
    #print ('@@@@@@@@@@@@@@@@')
    #print ('this is df_new:')
    #print (df_new)
    source = ColumnDataSource(df_new)
    source2 = ColumnDataSource(df_monthly)
 
    #-- what are tools options
    #tools = "pan,xwheel_zoom, wheel_zoom, box_zoom, undo, redo, save, reset,  hover, crosshair"

    #tools = "pan, wheel_zoom, box_zoom,  undo, redo, save, reset, crosshair,xbox_select"
    p_tools = "pan, wheel_zoom, box_zoom, box_select, undo, redo, save, reset, crosshair"
    q_tools = "pan,  box_zoom, box_select, lasso_select, undo, redo, reset, crosshair"


    def tseries_plot(p):
        p.line('time', 'var', source=source, alpha=0.8, line_width=4, color="navy")
        p.circle('time', 'var', size=7, source=source, color="navy", selection_color="navy")
        p.line('time', 'var_lower',source=source , alpha=0.5, line_width=4, color="#6495ED")
        p.line('time', 'var_upper',source=source , alpha=0.5, line_width=4, color="#6495ED")

        band_plot = Band(base='time', lower='var_lower', upper='var_upper', source=source,level='underlay',
                fill_alpha=0.3,fill_color='#6495ED')
    

    
        p.add_layout(band_plot)        
        
        p.xaxis.major_label_text_color = 'dimgray'
        p.xaxis.major_label_text_font_size = '18px'
        p.xaxis.major_label_text_font_style = "bold"

        p.yaxis.major_label_text_color = 'dimgray'
        p.yaxis.major_label_text_font_size = '18px'
        p.yaxis.major_label_text_font_style = "bold"


        p.xaxis.axis_label_text_font_size = "15pt"
        p.xaxis.axis_label_text_font_style = "bold"
        
        p.yaxis.axis_label_text_font_size = "15pt"
        p.yaxis.axis_label_text_font_style = "bold"
        
        p.axis.axis_label_text_font_style = "bold"
        
        p.grid.grid_line_alpha = 0.5
        p.title.text_font_size = '18pt'
        p.xaxis.axis_label = 'Time'
        p.yaxis.axis_label = 'Soil liquid water [kg/m²]'

        p.title.text = "Willamette Valley (45 N, 123 W)"
        
        #p.legend.location = "top_right"
        #p.legend.label_text_font_size = "13pt"
        #p.legend.label_text_font_style = "bold"

        #p.legend.label_text_font = "times"
        #p.legend.label_text_color = "dimgray"


    def scatter_plot(q):
        #q.line('month', 'var', source=source2, alpha=0.8, line_width=12, color="black")
        #q.circle('month', 'var', source=source2, alpha=0.8, size=2, color="black")

        q.xaxis.major_label_text_color = 'dimgray'
        q.xaxis.major_label_text_font_size = '15px'
        q.xaxis.major_label_text_font_style = "bold"

        q.yaxis.major_label_text_color = 'dimgray'
        q.yaxis.major_label_text_font_size = '15px'
        q.yaxis.major_label_text_font_style = "bold"

        q.xaxis.axis_label_text_font_size = "13pt"
        q.yaxis.axis_label_text_font_size = "13pt"

        q.axis.axis_label_text_font_style = "bold"
        q.grid.grid_line_alpha = 0.5
        q.title.text_font_size = '15pt'
        q.xaxis.axis_label = 'Month'
        q.yaxis.axis_label = 'Soil liquid water [kg/m²]'
        
        #q.xaxis.major_label_orientation = "vertical"
        q.xaxis.major_label_orientation = np.pi/4
        q.title.text = "Seasonal Cycle for 1850-2100"

        #x = range(0,500)
        #y = range(0,500)

        #q.line(x, y,alpha=0.8, line_width=4, color="gray")
        

    
    
    
    p = figure(tools=p_tools, x_axis_type="datetime", title= "Williamette Time-Series ")
    tseries_plot(p)
    freq_list = ['Monthly','Annual','Decadal']
    plot_vars = ['TREFHTMN', 'TREFHTMX','PRECT','SOILWATER_10CM']
    
    vars_dict = {'TREFHTMN': 'Minimum Temperature', 'TREFHTMX': 'Maximum Temperature',\
     'PRECT': 'Total  Precipitation','SOILWATER_10CM': 'Soil liquid water [kg/m²] '}

    a = list(range(0,19+1))
    ens_list=[str(x) for x in a]
    ens_list = ['Average']+ens_list
    vars_dict2 = {y: x for x, y in vars_dict.items()}

    menu = Select(options=list(vars_dict2.keys()),value=vars_dict[defualt_var], title='Variable') 
    #menu = Select(options=plot_vars,value='Average', title='Variable') 

    menu_ens = Select(options=ens_list,value=default_ens, title='Ensemble #') 
    #menu_ens = Dropdown(menu=ens_list, label='Ensemble #') 
    menu_freq = Select(options=freq_list,value=default_freq, title='Frequency') 


    q_width = 550
    q_height = 350
    q = figure(tools=q_tools,width=q_width, height=q_height)

    #q = figure(tools=q_tools,width=350, height=350)
    scatter_plot(q)
    qpoints = q.circle('month', 'var', source=source2, alpha=0.8, size=2, color="red")
    qlines = q.line('month', 'var', source=source2, alpha=0.8, line_width=4, color="red")
    
    q.add_tools(
        HoverTool(
            tooltips=[
                      ("NEON", "$x"),
                      ("CLM", "$y")]
        )
    )
    
        
    def update_variable (attr, old, new):
        print ('updating plot for:')
        print (' - var  : ', menu.value)
        print (' - ens : ', menu_ens.value)
        
        new_var = vars_dict2[menu.value]
        print (' - var2 : ', new_var)

        df_new, df_monthly = get_shaded_data(df_all, new_var, menu_ens.value, menu_freq.value)

        #q.add_layout(mytext)
        #q.add_layout(regression_line)
        
        #source = ColumnDataSource(df_new)
        source.data =df_new
        source2.data = df_monthly
        #source.stream(df_new)


    def update_yaxis (attr, old, new):
        if (vars_dict2[menu.value]=='TREFHTMN'):
            p.yaxis.axis_label = 'Minimum Temperature [°F]'
            q.yaxis.axis_label = 'Minimum Temperature [°F]'

        elif (vars_dict2[menu.value]=='TREFHTMX'):
            p.yaxis.axis_label = 'Maximum Temperature [°F]'
            q.yaxis.axis_label = 'Maximum Temperature [°F]'

        elif (vars_dict2[menu.value]=='PRECT'):
            p.yaxis.axis_label = 'Total  Precipitation [inch/year]'
            q.yaxis.axis_label = 'Total  Precipitation [inch/year]'

        elif (vars_dict2[menu.value]=='SOILWATER_10CM'):
            p.yaxis.axis_label = 'Soil liquid water [kg/m2] '
            q.yaxis.axis_label = 'Soil liquid water [kg/m2] '


    def handler(event):
        print(event.item)        
            
    menu.on_change('value', update_variable)
    menu.on_change('value', update_yaxis)

    #menu_ens.on_click(handler)
    #menu_ens.on_click(update_variable)
    menu_ens.on_change('value', update_variable)
    menu_freq.on_change('value', update_variable)
    
    def selection_change(attrname, old, new):
        #print ("calling dsjkghkjasdhgkjads")
        df_new, df_monthly = get_shaded_data(df_all, vars_dict2[menu.value], menu_ens.value, menu_freq.value)
        selected = source.selected.indices
        #print ('selected:', selected)
        #print (type (selected))
        if selected:
            #print ('selected is')
            df_new = df_new.iloc[selected, :]
            df_new['year'] = pd.DatetimeIndex(df_new['time']).year
            year_min = df_new['year'].min()
            year_max = df_new['year'].max()
            #print (year_min)
            #print (year_max)
            print (df_new)
            this_df = df_all.loc[(df_all['year']>=year_min) & (df_all['year']<=year_max)]
            df_new2, df_monthly = get_shaded_data(this_df, vars_dict2[menu.value], menu_ens.value, menu_freq.value)
        else:
            print ('selected is empty')
        
        if year_min ==year_max: 
            q.title.text ="Seasonal Cycle for "+str(year_min)
        else:
            q.title.text ="Seasonal Cycle for "+str(year_min)+"-"+ str(year_max)
        #update_stats(df_new)
        #print (qpoints.data_source.data )
        print (df_monthly)
        source2.data = df_monthly
        qpoints.data_source.data  =  df_monthly
        qlines.data_source.data  =  df_monthly


    source.selected.on_change('indices', selection_change)
    source.selected.on_change('indices', selection_change)
    source2.selected.on_change('indices', selection_change)
    source2.selected.on_change('indices', selection_change)
    
    button = Button(label="Download", button_type="success")
    button.js_on_event("button_click", CustomJS(args=dict(source=source),
                    code=open(join('.', "download.js")).read()))
    
    #layout = row(column(menu, menu_freq, menu_site, q),  p)
    layout = row(p, column( menu, menu_freq, q, button))
    


    
  
            



    #menu.on_change('value', update_variable)
    #menu.on_change('value', update_yaxis)

    #menu_freq.on_change('value', update_variable)
    
    #menu_site.on_change('value', update_variable)
    #menu_site.on_change('value', update_site)

    
    #layout = row(column(menu, menu_freq, menu_site, q),  p)
    #layout = row(p)
    
    p.add_tools(
        HoverTool(
            tooltips=[
                      #("Time", "$index"),
                      ("Value", "@var"),

                      ]
        )
    )
    doc.add_root(layout)
    source.selected.on_change('indices', selection_change)
    source2.selected.on_change('indices', selection_change)


    doc.theme = Theme(json=yaml.load("""
        attrs:
            Figure:
                background_fill_color: "#FFFFFF"
                outline_line_color: grey
                toolbar_location: above
                height: 700
                width: 1300
            Grid:
                grid_line_dash: [6, 4]
                grid_line_color: grey
    """, Loader=yaml.FullLoader))
    

from bokeh.io import output_notebook, show, curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool

#output_notebook()

if ShowWebpage:
    shaded_tseries(curdoc())
else:
    #show(bkapp)
    show(shaded_tseries)

from bokeh.plotting import figure, output_file, save
