import pandas as pd
from typing import Optional
from pandas.api.types import is_numeric_dtype
from pandas import Series

from station.app.schemas.datasets import DataSetStatistics


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
    print(description.to_string())

    n_items = shape[0]
    n_features = shape[1]
    columns = dataframe.columns.values.tolist()
    columns_inf = []

    for i in range(len(columns)):
        title = columns[i]
        count = description[title]["count"]
        columns_inf.append({
            'title': title,
            'number_of_elements': count
        })
        if not(is_numeric_dtype(dataframe[title])):
            unique = description[title]["unique"]
            top = description[title]["top"]
            freq = description[title]["freq"]
            # if every entry has an unique value (or at most 50 values are given multiple times)
            if count - 50 < unique <= count:
                column_type = "unique"
                columns_inf[i]['type'] = column_type
            else:
                column_type = "categorical"
                columns_inf[i]['type'] = column_type
                columns_inf[i]['number_categories'] = unique
            columns_inf[i]['most_frequent_element'] = top
            columns_inf[i]['frequency'] = freq
        else:
            columns_inf[i]['type'] = "numeric"
            columns_inf[i]['mean'] = description[title]["mean"]
            columns_inf[i]['std'] = description[title]["std"]
            columns_inf[i]['min'] = description[title]["min"]
            columns_inf[i]['max'] = description[title]["max"]

    schema_data = {
        'n_items': n_items,
        'n_features': n_features,
        'column_information': columns_inf
    }

    statistics = DataSetStatistics(**schema_data)
    return statistics


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
