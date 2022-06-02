import pandas as pd
from typing import Optional
from pandas.api.types import is_numeric_dtype, is_bool_dtype
import plotly.express as px
import plotly.io
from plotly.graph_objects import Figure
import json

from station.app.schemas.datasets import DataSetStatistics, DataSetFigure


def get_dataset_statistics(dataframe: pd.DataFrame) -> Optional[DataSetStatistics]:
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


def get_column_information(dataframe: pd.DataFrame, description: pd.DataFrame) -> dict:
    """
    Extract information out of dataframe and summarize it in a dictionary
    :param dataframe: Dataframe to summarize
    :param description: Dataframe description as dataframe object
    :return: Dictionary with column information
    """
    columns_inf = []
    columns = dataframe.columns.values.tolist()
    for i in range(len(columns)):
        title = columns[i]
        count = description[title]["count"]
        columns_inf.append({
            'title': title
        })
        nan_count = dataframe[title].isna().sum()
        if not(is_numeric_dtype(dataframe[title])) or is_bool_dtype(dataframe[title]):
            # extract information from categorical column
            columns_inf[i]['not_na_elements'] = count - nan_count
            columns_inf, chart_json = process_categorical_column(dataframe, columns_inf, i, description, title)
        else:
            # extract information from numerical column
            zero_count = dataframe[title][dataframe[title]==0].count()
            undefined_count = nan_count + zero_count
            columns_inf[i]['not_na_elements'] = count - undefined_count
            columns_inf, chart_json = process_numerical_column(dataframe, columns_inf, i, description, title)

        if chart_json is not None:
            columns_inf[i]['figure'] = chart_json

    return columns_inf


def process_numerical_column(dataframe: pd.DataFrame, columns_inf: dict, i: int, description: pd.DataFrame, title: str) -> tuple[dict, DataSetFigure]:
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
    # create boxplot for numerical data
    fig = px.box(dataframe, y=title)
    chart_json = create_figure(fig)
    return columns_inf, chart_json


def process_categorical_column(dataframe: pd.DataFrame, columns_inf:dict, i: int, description: pd.DataFrame, title: str) -> tuple[dict, DataSetFigure]:
    """
    Extract information from categorical column and create plot of column data
    :param dataframe: dataset as dataframe object
    :param columns_inf: array containing all information of different columns
    :param i: current column index
    :param description: description of all dataset columns
    :param title: title of column with index i
    :return: array with column information, key and json to save chart in cache
    """
    count = columns_inf[i]['not_na_elements']
    unique = description[title]["unique"]
    top = description[title]["top"]
    freq = description[title]["freq"]
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

            # pie chart if number of classes is below 6
            # value counts are provided if there are less then 6 classes
            if unique < 6:
                columns_inf[i]['value_counts'] = dict(dataframe[title].value_counts())
                fig = px.pie(dataframe, names=title, title=title)


            # histogram if number of classes is greater than 10
            elif unique >= 6:
                fig = px.histogram(dataframe, x=title, title=title)
                fig.update_layout(yaxis_title="Anzahl")

            if fig is not None:
                chart_json = create_figure(fig)

        columns_inf[i]['type'] = column_type

    return columns_inf, chart_json


def create_figure(fig: Figure) -> DataSetFigure:
    """
    Create DataSetFigure-Object of a plotly figure
    :param fig: Plotly figure
    :return: DataSetFigure-Object with JSON-representation of plotly figure
    """
    fig_json = plotly.io.to_json(fig)
    obj = json.loads(fig_json)
    figure = DataSetFigure(fig_data=obj)
    return figure
