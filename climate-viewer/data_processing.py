# Author: Negin Sobhani
# Email: negins@ucar.edu

import pandas as pd
import calendar


def convert_temperature(df, col_names):
    """
    Convert temperature from Kelvin to Fahrenheit.
    
    :param df: DataFrame containing temperature columns
    :param col_names: List of column names containing temperature data
    :return: DataFrame with converted temperature values
    """
    for col in col_names:
        df[col] = (df[col] - 273.15) * 1.8 + 32
    return df


def convert_precipitation(df, col_names):
    """
    Convert precipitation to inches per year.
    
    :param df: DataFrame containing precipitation columns
    :param col_names: List of column names containing precipitation data
    :return: DataFrame with converted precipitation values
    """
    for col in col_names:
        df[col] = (df[col]) * 1242399685.04 / 12
    return df


def read_data(file_name="dummy.csv"):
    """
    Read and process data from a CSV file.
    
    :param file_name: Path to the CSV file
    :return: DataFrame with processed data
    """
    df = pd.read_csv(file_name)
    col_names = df.columns[df.columns.str.contains(pat="TREF")]
    df = convert_temperature(df, col_names)
    col_names = df.columns[df.columns.str.contains(pat="PREC")]
    df = convert_precipitation(df, col_names)
    df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)
    return df


def extract_time_information(df):
    """
    Extract time-related information from the DataFrame.
    
    :param df: DataFrame containing a 'time' column
    :return: DataFrame with extracted time information
    """
    # -- extract year, month, day, hour information from time
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    df["hour"] = df["time"].dt.hour
    return df


def get_shaded_data(df_all, var, ens, freq="Monthly"):
    """
    Calculate shaded data based on the provided variable and frequency.
    
    :param df_all: DataFrame containing all data
    :param var: Variable to be used for calculations
    :param ens: Ensemble for the variable
    :param freq: Frequency for calculations, one of "Monthly", "Annual", or "Decadal"
    :return: Tuple with data output, monthly data, and selected monthly data
    """
    print(f"Calculating {freq} average for {var}...")

        # Extract columns with variable name.
    col_names = df_all.columns[df_all.columns.str.contains(pat=var)]

    # Average all columns with this variable name.
    this = df_all[col_names].mean(axis=1)
    this_std = df_all[col_names].std(axis=1)

    # Create a DataFrame with average ensemble for that variable.
    df_this = pd.DataFrame(
        {"time": df_all["time"], "year": df_all["year"], "month": df_all["month"], "var": this}
    )

    # Add ensemble min and max.
    df_this["var_lower"] = df_all[col_names].min(axis=1)
    df_this["var_upper"] = df_all[col_names].max(axis=1)

    # Group by month and calculate mean.
    df_monthly = df_this.groupby("month").mean()

    # Select data from 2000 to 2020.
    mask = (df_this["year"] > 1999) & (df_this["year"] < 2021)
    df_selected = df_this.loc[mask]
    df_monthly_selected = df_selected.groupby("month").mean()

     # Calculate shaded data based on frequency.
    if freq == "Monthly":
        df_out = df_this
    elif freq == "Annual":
        # Group by year and calculate mean/min/max based on variable.
        if var == "TREFHTMN":
            df_annual = df_all.groupby("year").min().reset_index()
        elif var == "TREFHTMX":
            df_annual = df_all.groupby("year").max().reset_index()
        else:
            df_annual = df_all.groupby("year").mean().reset_index()

        # Add month and day columns.
        df_annual["month"] = 6
        df_annual["day"] = 30
        # Convert year/month/day to datetime format.
        df_annual["time"] = pd.to_datetime(df_annual[["year", "month", "day"]])

        # Calculate mean/min/max for variable and create DataFrame.
        this = df_annual[col_names].mean(axis=1)
        df_out = pd.DataFrame(
            {"time": df_annual["time"], "month": df_annual["month"], "var": this}
        )
        df_out["var_lower"] = df_annual[col_names].min(axis=1)
        df_out["var_upper"] = df_annual[col_names].max(axis=1)

    elif freq == "Decadal":
        # Group by decade and calculate mean/min/max based on variable.
        df_all['decade'] = df_all['time'].dt.year.floordiv(10).mul(10)
        if var == "TREFHTMN":
            df_tmp = df_all.groupby("decade").min().reset_index()
        elif var == "TREFHTMX":
            df_tmp = df_all.groupby("decade").max().reset_index()
        else:
            df_tmp = df_all.groupby([(df_all.time.dt.year // 10 * 10)]).mean().reset_index()

        # Create a dummy DataFrame to calculate time values.
        df_dumb = df_all.groupby([(df_all.time.dt.year // 10 * 10)]).mean().reset_index()

        # Add year, month, and day columns.
        df_tmp["year"] = pd.DatetimeIndex(df_dumb["time"]).year
        df_tmp["month"] = 6
        df_tmp["day"] = 30

        # Convert year/month/day to datetime format.
        df_tmp["time"] = pd.to_datetime(df_tmp[["year", "month", "day"]])

        # Calculate mean/min/max for variable and create DataFrame.
        this = df_tmp[col_names].mean(axis=1)
        this_std = df_tmp[col_names].std(axis=1)
        #this_std.iloc[-1] = this_std.iloc[-2]
        df_out = pd.DataFrame(
            {"time": df_tmp["time"], "month": df_tmp["month"], "var": this}
        )
        df_out["var_lower"] = df_tmp[col_names].min(axis=1)
        df_out["var_upper"] = df_tmp[col_names].max(axis=1)
        df_out = df_out[:-1]

    # Add month names to DataFrame.
    month_dict = dict(enumerate(calendar.month_abbr))
    df_monthly["Month"] = df_monthly.index.map(month_dict)
    df_monthly_selected["Month"] = df_monthly_selected.index.map(month_dict)

    # Return shaded data and average data.
    return df_out, df_monthly, df_monthly_selected