#! /usr/bin/env python
# Import Libraries

import os
import time
import yaml
import calendar

import numpy as np
import pandas as pd

from os.path import join
from glob import glob

from bokeh.themes import Theme

from bokeh.models import (
    ColumnDataSource,
    Button,
    CustomJS,
    DataTable,
    Slider,
    Dropdown,
    Select,
    PreText,
    Label,
    Slope,
    Band,
    NumberFormatter,
    RangeSlider,
    TableColumn,
)
from bokeh.layouts import row, column
from data_processing import read_data, extract_time_information, get_shaded_data
from bokeh.io import output_notebook, show, curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool

# -- only for running in the notebook:
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

# ----------------------------------

# default values: 
default_site = "ABBY"
default_freq = "Annual"
default_var = "SOILWATER_10CM"
default_ens = "Average"
default_var_desc = "Soil Moisture [kg/m²]"

vars_dict = {
        "TREFHTMN": "Minimum Temperature",
        "TREFHTMX": "Maximum Temperature",
        "PRECT": "Total  Precipitation",
        "SOILWATER_10CM": "Soil Moisture (Top 10 cm) ",
    }


input_file = "data/dummy.csv"

# Read and process data
df_all = read_data(input_file)
df_all = extract_time_information(df_all)


def shaded_tseries1(doc):
    """
    Generates interactive shaded time-series and scatter plots.

    Args:
        doc: A Bokeh document to which the Bokeh layout is added.
    """

    # Default parameters
    default_var = "SOILWATER_10CM"
    default_ens = "Average"
    default_freq = "Annual"

    df_new, df_monthly, df_monthly_selected = get_shaded_data(
        df_all, default_var, default_ens, default_freq
    )

    # ColumnDataSource initialization
    source = ColumnDataSource(df_new)
    source2 = ColumnDataSource(df_monthly)
    source3 = ColumnDataSource(df_monthly_selected)

    # Variables and frequencies
    freq_list = ["Monthly", "Annual", "Decadal"]
    plot_vars = ["TREFHTMN", "TREFHTMX", "PRECT", default_var]

    # Tool options
    tools_options = "pan, wheel_zoom, box_zoom, box_select, undo, save, reset"

    def configure_plot(p, y_axis_label):
        """
        Function to configure the given plot.

        Args:
            p: A Bokeh figure to be configured.
            y_axis_label: Label for the y-axis.
        """

        p.xaxis.major_label_text_color = "dimgray"
        p.xaxis.major_label_text_font_size = "18px"
        p.xaxis.axis_label_text_font = "Verdana"
        p.yaxis.axis_label_text_font = "Verdana"
        p.xaxis.axis_label_text_font_size = "15pt"
        p.xaxis.axis_label_text_font_style = "bold"
        p.yaxis.axis_label_text_font_size = "15pt"
        p.yaxis.axis_label_text_font_style = "bold"
        p.axis.axis_label_text_font_style = "bold"
        p.grid.grid_line_alpha = 0.5
        p.title.text_font_size = "21pt"
        p.xaxis.axis_label = "Time"
        p.yaxis.axis_label = y_axis_label
        p.title.text_font = "Verdana"
        p.title.text = "Willamette Valley (45°N, 123°W)"

    def tseries_plot(p):
        """
        Function to create a time-series plot.

        Args:
            p: A Bokeh figure on which the plot is drawn.
        """
        p.line("time", "var", source=source, alpha=0.8, line_width=4, color="navy")
        p.circle(
            "time", "var", size=7, source=source, color="navy", selection_color="navy"
        )
        p.line(
            "time", "var_lower", source=source, alpha=0.5, line_width=4, color="#6495ED"
        )
        p.line(
            "time", "var_upper", source=source, alpha=0.5, line_width=4, color="#6495ED"
        )

        band_plot = Band(
            base="time",
            lower="var_lower",
            upper="var_upper",
            source=source,
            level="underlay",
            fill_alpha=0.3,
            fill_color="#6495ED",
        )

        p.add_layout(band_plot)
        configure_plot(p, "Soil Moisture [kg/m²]")

    def scatter_plot(q):
        """
        Function to create a scatter plot.

        Args:
            q: A Bokeh figure on which the plot is drawn.
        """
        q.circle("month", "var", size=7, source=source2, color="navy")
        q.circle(
            "month",
            "var",
            size=10,
            source=source3,
            color="navy",
            selection_color="navy",
        )
        q.yaxis.axis_label = "Soil Moisture [kg/m²]"
        configure_plot(q, "Soil Moisture [kg/m²]")

    def update_variable(attr, old, new):
        """
        Function to update the variable for plotting.

        Args:
            attr: The changed attribute.
            old: The old value of the attribute.
            new: The new value of the attribute.
        """
        variable = vars_dict2[new]
        ens = menu_ens.value
        freq = menu_freq.value
        df_new, df_monthly, df_monthly_selected = get_shaded_data(
            df_all, variable, ens, freq
        )
        source.data = ColumnDataSource.from_df(df_new)
        source2.data = ColumnDataSource.from_df(df_monthly)
        source3.data = ColumnDataSource.from_df(df_monthly_selected)

    def update_yaxis(attr, old, new):
        """
        Function to update the y-axis label.

        Args:
            attr: The changed attribute.
            old: The old value of the attribute.
            new: The new value of the attribute.
        """
        variable = vars_dict2[new]
        y_axis_label = yaxis_dict[variable]
        p.yaxis.axis_label = y_axis_label
        q.yaxis.axis_label = y_axis_label

    def selection_change(attr, old, new):
        """
        Function to handle the change of selection.

        Args:
            attr: The changed attribute.
            old: The old value of the attribute.
            new: The new value of the attribute.
        """
        selected = source.selected.indices
        if selected:
            data = source.data
            selected_data = {key: [data[key][i] for i in selected] for key in data}
            df_selected = pd.DataFrame(selected_data)
            source3.data = ColumnDataSource.from_df(df_selected)
        else:
            source3.data = {"index": [], "time": [], "var": []}

    # Interactive elements
    p = figure(tools=tools_options, x_axis_type="datetime", active_drag="box_select")
    tseries_plot(p)

    q = figure(tools=tools_options, width=450, height=400, toolbar_location="right")
    scatter_plot(q)

    # Dropdown menus
    vars_dict = {
        "TREFHTMN": "Minimum Temperature",
        "TREFHTMX": "Maximum Temperature",
        "PRECT": "Total Precipitation",
        "SOILWATER_10CM": "Soil Moisture [kg/m²]",
    }
    vars_dict2 = {y: x for x, y in vars_dict.items()}

    menu = Select(options=list(vars_dict2.keys()), value=vars_dict[default_var], title="Variable")
    menu.on_change("value", update_variable)
    menu.on_change("value", update_yaxis)

    ens_list = ["Average"] + [str(x) for x in list(range(20))]
    menu_ens = Select(options=ens_list, value=default_ens, title="Ensemble #")
    menu_ens.on_change("value", update_variable)

    menu_freq = Select(options=freq_list, value=default_freq, title="Frequency")
    menu_freq.on_change("value", update_variable)

    source.selected.on_change("indices", selection_change)

    layout = row(p, column(menu, menu_freq, q, button))
    doc.add_root(layout)
    source.selected.on_change("indices", selection_change)
    source2.selected.on_change("indices", selection_change)

    # toolbar_location: above

    doc.theme = Theme(
        json=yaml.load(
            """
        global-styling:
          css:
            theme:
              https://fonts.googleapis.com/css?family=Quicksand: { type: external }

        attrs:
            Figure:
                background_fill_color: "#FFFFFF"
                outline_line_color: "grey"
                height: 700
                width: 1300
            Grid:
                grid_line_dash: [6, 4]
                grid_line_color: grey
            Title:
                text_color: "black"
            Axis:
                major_label_text_font: "Verdana"
                major_label_text_font_style: "normal"
                major_label_text_font_size: "18px"
    """,
            Loader=yaml.FullLoader,
        )
    )





def shaded_tseries(doc):


    df_new, df_monthly, df_monthly_selected = get_shaded_data(
        df_all, default_var, default_ens, default_freq
    )
    print("~~~~~~~~")

    print("~~~~~~~~")
    print(df_monthly)
    print(df_monthly_selected)
    print("~~~~~~~~")
    print("~~~~~~~~")

    source = ColumnDataSource(df_new)
    source2 = ColumnDataSource(df_monthly)
    source3 = ColumnDataSource(df_monthly_selected)

    freq_list = ["Monthly", "Annual", "Decadal"]
    plot_vars = ["TREFHTMN", "TREFHTMX", "PRECT", "SOILWATER_10CM"]

    # -- what are tools options
    p_tools = "pan, wheel_zoom, box_zoom, box_select, undo, save, reset"
    q_tools = ""

    def tseries_plot(p):
        p.line("time", "var", source=source, alpha=0.8, line_width=4, color="navy")
        p.circle(
            "time", "var", size=7, source=source, color="navy", selection_color="navy"
        )
        p.line(
            "time", "var_lower", source=source, alpha=0.5, line_width=4, color="#6495ED"
        )
        p.line(
            "time", "var_upper", source=source, alpha=0.5, line_width=4, color="#6495ED"
        )

        band_plot = Band(
            base="time",
            lower="var_lower",
            upper="var_upper",
            source=source,
            level="underlay",
            fill_alpha=0.3,
            fill_color="#6495ED",
        )

        p.add_layout(band_plot)

        p.xaxis.major_label_text_color = "dimgray"
        p.xaxis.major_label_text_font_size = "18px"
        # p.xaxis.major_label_text_font_style = "bold"

        # p.yaxis.major_label_text_color = 'dimgray'
        # p.yaxis.major_label_text_font_size = '18px'
        # p.yaxis.major_label_text_font_style = "bold"

        p.xaxis.axis_label_text_font = "Verdana"
        p.yaxis.axis_label_text_font = "Verdana"
        p.xaxis.axis_label_text_font_size = "15pt"
        p.xaxis.axis_label_text_font_style = "bold"

        p.yaxis.axis_label_text_font_size = "15pt"
        p.yaxis.axis_label_text_font_style = "bold"

        p.axis.axis_label_text_font_style = "bold"

        p.grid.grid_line_alpha = 0.5
        p.title.text_font_size = "21pt"
        p.xaxis.axis_label = "Time"
        p.yaxis.axis_label = "Soil Moisture [kg/m²]"
        p.title.text_font = "Verdana"
        p.title.text = "Willamette Valley (45°N, 123°W)"

        # p.legend.location = "top_right"
        # p.legend.label_text_font_size = "13pt"
        # p.legend.label_text_font_style = "bold"

        # p.legend.label_text_font = "times"
        # p.legend.label_text_color = "dimgray"

    def scatter_plot(q):
        q.line(
            "month",
            "var",
            source=source3,
            alpha=0.8,
            line_width=4,
            color="gray",
            line_dash="dashed",
            legend_label="2000-2020",
        )
        q.circle("month", "var", source=source3, alpha=0.8, size=2, color="dimgray")

        q.xaxis.major_label_text_color = "dimgray"
        q.xaxis.major_label_text_font_size = "15px"
        # q.xaxis.major_label_text_font_style = "bold"

        q.yaxis.major_label_text_color = "dimgray"
        q.yaxis.major_label_text_font_size = "15px"
        # q.yaxis.major_label_text_font_style = "bold"

        q.xaxis.axis_label_text_font_size = "13pt"
        q.yaxis.axis_label_text_font_size = "13pt"
        q.xaxis.axis_label_text_font = "Verdana"
        q.yaxis.axis_label_text_font = "Verdana"

        q.title.text_font = "Verdana"
        q.axis.axis_label_text_font_style = "bold"
        q.grid.grid_line_alpha = 0.5
        q.title.text_font_size = "15pt"
        q.xaxis.axis_label = "Month"
        q.yaxis.axis_label = "Soil Moisture [kg/m²]"

        # q.xaxis.major_label_orientation = "vertical"
        q.xaxis.major_label_orientation = np.pi / 4
        q.title.text = "Seasonal Cycle for 1850-2100"
        month_dict = dict(enumerate(calendar.month_abbr))

        q.xaxis.major_label_overrides = month_dict
        q.legend.location = "top_right"
        # x = range(0,500)
        # y = range(0,500)

        # q.line(x, y,alpha=0.8, line_width=4, color="gray")

    p = figure(
        tools=p_tools,
        x_axis_type="datetime",
        title="Williamette Time-Series ",
        active_drag="box_select",
        toolbar_location="above",
    )
    tseries_plot(p)

    vars_dict = {
        "TREFHTMN": "Minimum Temperature",
        "TREFHTMX": "Maximum Temperature",
        "PRECT": "Total  Precipitation",
        "SOILWATER_10CM": "Soil Moisture (Top 10 cm) ",
    }

    a = list(range(0, 19 + 1))
    ens_list = [str(x) for x in a]
    ens_list = ["Average"] + ens_list
    vars_dict2 = {y: x for x, y in vars_dict.items()}

    menu = Select(
        options=list(vars_dict2.keys()),
        value=vars_dict[default_var],
        title="Variable",
        css_classes=["custom_select"],
    )
    # menu = Select(options=plot_vars,value='Average', title='Variable')

    menu_ens = Select(options=ens_list, value=default_ens, title="Ensemble #")
    # menu_ens = Dropdown(menu=ens_list, label='Ensemble #')
    menu_freq = Select(
        options=freq_list,
        value=default_freq,
        title="Frequency",
        css_classes=["custom_select"],
    )

    q_width = 450
    q_height = 400
    q = figure(tools=q_tools, width=q_width, height=q_height, toolbar_location="right")

    # q = figure(tools=q_tools,width=350, height=350)
    scatter_plot(q)
    qpoints = q.circle("month", "var", source=source2, alpha=0.7, size=2, color="red")
    qlines = q.line(
        "month", "var", source=source2, alpha=0.7, line_width=4, color="red"
    )

    # q.add_tools(
    #    HoverTool(
    #        tooltips=[
    #                  ("Month", "$x"),
    #                  ("Value", "$y")]
    #    )
    # )

    p.add_tools(
        HoverTool(
            tooltips=[
                # ("Time", "@year"),
                ("value", "@var"),
            ],
            # formatters={'datetime': 'datetime'}
        )
    )

    def update_variable(attr, old, new):
        print("updating plot for:")
        print(" - var  : ", menu.value)
        print(" - ens : ", menu_ens.value)

        new_var = vars_dict2[menu.value]
        print(" - var2 : ", new_var)

        df_new, df_monthly, df_monthly_selected = get_shaded_data(
            df_all, new_var, menu_ens.value, menu_freq.value
        )

        # q.add_layout(mytext)
        # q.add_layout(regression_line)

        # source = ColumnDataSource(df_new)
        source.data = df_new
        source2.data = df_monthly
        source3.data = df_monthly_selected
        # source.stream(df_new)

    def update_yaxis(attr, old, new):
        if vars_dict2[menu.value] == "TREFHTMN":
            p.yaxis.axis_label = "Minimum Temperature [°F]"
            q.yaxis.axis_label = "Minimum Temperature [°F]"

        elif vars_dict2[menu.value] == "TREFHTMX":
            p.yaxis.axis_label = "Maximum Temperature [°F]"
            q.yaxis.axis_label = "Maximum Temperature [°F]"

        elif vars_dict2[menu.value] == "PRECT":
            p.yaxis.axis_label = "Total  Precipitation [inch/month]"
            q.yaxis.axis_label = "Total  Precipitation [inch/month]"

        elif vars_dict2[menu.value] == "SOILWATER_10CM":
            p.yaxis.axis_label = "Soil Moisture [kg/m2] "
            q.yaxis.axis_label = "Soil Moisture [kg/m2] "

    def handler(event):
        print(event.item)

    menu.on_change("value", update_variable)
    menu.on_change("value", update_yaxis)

    # menu_ens.on_click(handler)
    # menu_ens.on_click(update_variable)
    menu_ens.on_change("value", update_variable)
    menu_freq.on_change("value", update_variable)

    def selection_change(attrname, old, new):
        # print ("calling dsjkghkjasdhgkjads")
        df_new, df_monthly, df_monthly_selected = get_shaded_data(
            df_all, vars_dict2[menu.value], menu_ens.value, menu_freq.value
        )
        selected = source.selected.indices
        # print ('selected:', selected)
        # print (type (selected))
        if selected:
            # print ('selected is')
            df_new = df_new.iloc[selected, :]
            df_new["year"] = pd.DatetimeIndex(df_new["time"]).year
            year_min = df_new["year"].min()
            year_max = df_new["year"].max()
            # print (year_min)
            # print (year_max)
            print(df_new)
            this_df = df_all.loc[
                (df_all["year"] >= year_min) & (df_all["year"] <= year_max)
            ]
            df_new2, df_monthly, df_monthly_selected = get_shaded_data(
                this_df, vars_dict2[menu.value], menu_ens.value, menu_freq.value
            )
        else:
            print("selected is empty")

        if year_min == year_max:
            q.title.text = "Seasonal Cycle for " + str(year_min)
        else:
            q.title.text = "Seasonal Cycle for " + str(year_min) + "-" + str(year_max)
        # update_stats(df_new)
        # print (qpoints.data_source.data )
        print(df_monthly)
        source2.data = df_monthly
        qpoints.data_source.data = df_monthly
        qlines.data_source.data = df_monthly

    source.selected.on_change("indices", selection_change)
    source.selected.on_change("indices", selection_change)
    source2.selected.on_change("indices", selection_change)
    source2.selected.on_change("indices", selection_change)

    # button = Button(label="Download", button_type="success", css_classes=['btn_style'])
    button = Button(label="Download", css_classes=["btn_style"])
    button.js_on_event(
        "button_click",
        CustomJS(args=dict(source=source), code=open(join(".", "download.js")).read()),
    )

    # layout = row(column(menu, menu_freq, menu_site, q),  p)
    layout = row(p, column(menu, menu_freq, q, button))

    # menu.on_change('value', update_variable)
    # menu.on_change('value', update_yaxis)

    # menu_freq.on_change('value', update_variable)

    # menu_site.on_change('value', update_variable)
    # menu_site.on_change('value', update_site)

    # layout = row(column(menu, menu_freq, menu_site, q),  p)
    # layout = row(p)

    doc.add_root(layout)
    source.selected.on_change("indices", selection_change)
    source2.selected.on_change("indices", selection_change)

    # toolbar_location: above

    doc.theme = Theme(
        json=yaml.load(
            """
        global-styling:
          css:
            theme:
              https://fonts.googleapis.com/css?family=Quicksand: { type: external }

        attrs:
            Figure:
                background_fill_color: "#FFFFFF"
                outline_line_color: "grey"
                height: 700
                width: 1300
            Grid:
                grid_line_dash: [6, 4]
                grid_line_color: grey
            Title:
                text_color: "black"
            Axis:
                major_label_text_font: "Verdana"
                major_label_text_font_style: "normal"
                major_label_text_font_size: "18px"
    """,
            Loader=yaml.FullLoader,
        )
    )



if ShowWebpage:
    shaded_tseries(curdoc())
else:
    # show(bkapp)
    show(shaded_tseries)