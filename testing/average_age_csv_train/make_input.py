import pandas as pd
import numpy as np

def minimal(n: int):
    ages = np.random.randint(18, 99, n)
    ids = [i for i in range(n)]

    data = zip(ids, ages)
    df = pd.DataFrame(
        data=data,
        columns=['id', 'age']
    )

    df.to_csv("minimal-input.csv", index=False)


def medium(n: int):
    ages = np.random.randint(18, 99, n)
    ids = [i for i in range(n)]

    cat_cols = [f"cat_{i}" for i in range(10)]
    num_cols = [f"num_{i}" for i in range(10)]

    cat_data = []
    num_data = []
    for i, cl in enumerate(cat_cols):
        cat_data.append(np.random.choice([f'a-{i}', f'b-{i}', f'c-{i}', f'd-{i}'], n))

    for nl in num_cols:
        base = np.random.randint(0, 10000)
        std = np.random.randint(1, 100)
        num_data.append(np.random.normal(base, std, n))

    cols = ['id', 'age'] + cat_cols + num_cols
    data = zip(ids, ages, *cat_data, *num_data)
    df = pd.DataFrame(
        data=data,
        columns=cols
    )

    df.to_csv("medium-input.csv", index=False)


if __name__ == '__main__':
    n_subjects = 1000
    medium(n_subjects)
