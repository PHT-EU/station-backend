import pandas as pd
import numpy as np


if __name__ == '__main__':
    n_subjects = 1000
    ages = np.random.randint(18, 99, n_subjects)
    ids = [i for i in range(n_subjects)]

    data = zip(ids, ages)
    df = pd.DataFrame(
        data=data,
        columns=['id', 'age']
    )

    df.to_csv("input.csv")
    age_sum = df["age"].describe()
    age_sum.to_csv("age_sum.csv")