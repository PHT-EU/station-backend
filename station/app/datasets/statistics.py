import pandas as pd
from typing import Optional
from pandas.api.types import is_numeric_dtype
from pandas import Series
import plotly.express as px
import plotly.io
import json

from station.app.schemas.datasets import DataSetStatistics, DataSetFigure
from station.app.cache import redis_cache


def get_dataset_statistics(dataframe) -> Optional[DataSetStatistics]:
    """
    Computes statistical information of a dataset
    :param dataframe: Dataset as dataframe object
    :return: Dataset statistics
    """
    if not (isinstance(dataframe, pd.DataFrame)):
        raise TypeError
    shape = dataframe.shape
    description = dataframe.describe(include='all')

    n_items = shape[0]
    n_features = shape[1]
    columns_inf = get_column_information(dataframe, description)

    schema_data = {
        'n_items': n_items,
        'n_features': n_features,
        'column_information': columns_inf
    }

    statistics = DataSetStatistics(**schema_data)
    return statistics


def get_column_information(dataframe, description):
    columns_inf = []
    columns = dataframe.columns.values.tolist()
    for i in range(len(columns)):
        title = columns[i]
        count = description[title]["count"]
        columns_inf.append({
            'title': title,
            'number_of_elements': count
        })
        if not(is_numeric_dtype(dataframe[title])):
            # extract information from categorical column
            columns_inf, chart_key, chart_json = process_categorical_column(dataframe, columns_inf, i, description, title)
        else:
            # extract information from numerical column
            columns_inf, chart_key, chart_json = process_numerical_column(dataframe, columns_inf, i, description, title)

        if chart_json is not None:
            save_to_cache(chart_key, chart_json)
            # get chart for test
            # chart_get = redis_cache.get(chart_key)
            # fig = plotly.io.from_json(chart_get)
            # fig.show()
    return columns_inf


def process_numerical_column(dataframe, columns_inf, i, description, title):
    """
    Extract information from numerical column and create plot of column data
    :param dataframe: dataset as dataframe object
    :param columns_inf: array containing all information of different columns
    :param i: current column index
    :param description: description of all dataset columns
    :param title: title of column with index i
    :return: array with column information, key and json to save chart in cache
    """
    columns_inf[i]['type'] = "numeric"
    columns_inf[i]['mean'] = description[title]["mean"]
    columns_inf[i]['std'] = description[title]["std"]
    columns_inf[i]['min'] = description[title]["min"]
    columns_inf[i]['max'] = description[title]["max"]
    chart_key = title + "_boxplot"
    chart_json = create_boxplot(dataframe, title)
    return columns_inf, chart_key, chart_json


def process_categorical_column(dataframe, columns_inf, i, description, title):
    """
    Extract information from categorical column and create plot of column data
    :param dataframe: dataset as dataframe object
    :param columns_inf: array containing all information of different columns
    :param i: current column index
    :param description: description of all dataset columns
    :param title: title of column with index i
    :return: array with column information, key and json to save chart in cache
    """
    count = columns_inf[i]['number_of_elements']
    unique = description[title]["unique"]
    top = description[title]["top"]
    freq = description[title]["freq"]
    chart_key = None
    chart_json = None

    # if every entry has an unique value (or at most 50 values are given multiple times)
    if count - 50 < unique <= count:
        column_type = "unique"
        columns_inf[i]['type'] = column_type
        if unique != count:
            columns_inf[i]['number_of_duplicates'] = count - unique
    else:
        # all elements of column have the same value
        if unique == 1:
            column_type = "equal"
            columns_inf[i]['value'] = top
            # if column has just one equal value, no plot is created

        else:
            column_type = "categorical"
            columns_inf[i]['number_categories'] = unique
            columns_inf[i]['most_frequent_element'] = top
            columns_inf[i]['frequency'] = freq

            # pie chart if number of classes is below 10
            if unique < 10:
                chart_key = title + "_pie"
                chart_json = create_pie_chart(dataframe, title)

            # histogram if number of classes is greater than 10
            elif unique >= 10:
                chart_key = title + "_histogram"
                chart_json = create_histogram(dataframe, title)

        columns_inf[i]['type'] = column_type

    return columns_inf, chart_key, chart_json


def save_to_cache(chart_key: str, chart_json: DataSetFigure):
    """
    Save json of plot to the redis cache
    :param chart_key: key for saving the plot json
    :param chart_json: plot data in json format
    :return:
    """
    save_json = json.loads(json.dumps(chart_json.fig_data.json()))
    redis_cache.set(chart_key, str(save_json))


def get_class_distribution(dataframe, target_field) -> Series:
    """
    Get class distribution of specific column in dataframe
    :param dataframe: Dataset as dataframe object
    :param target_field: Column which should be analyzed
    :return: Class distribution of specific column
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError
    n_items = dataframe.shape[0]
    class_distribution = (dataframe[target_field].value_counts() / n_items)
    return class_distribution


def create_histogram(df, title) -> DataSetFigure:
    fig = px.histogram(df, x=title, title=title)
    fig.update_layout(yaxis_title="Anzahl")
    fig_json = plotly.io.to_json(fig)
    obj = json.loads(fig_json)
    figure = DataSetFigure(fig_data=obj)
    return figure


def create_pie_chart(df, title) -> DataSetFigure:
    fig = px.pie(df, names=title, title=title)
    fig_json = plotly.io.to_json(fig)
    obj = json.loads(fig_json)
    figure = DataSetFigure(fig_data=obj)
    return figure


def create_boxplot(df, title) -> DataSetFigure:
    fig = px.box(df, y=title)
    fig_json = plotly.io.to_json(fig)
    obj = json.loads(fig_json)
    figure = DataSetFigure(fig_data=obj)
    return figure
