import pandas as pd

INPUT_CSV = "/opt/train_data/input.csv"

STORAGE_PATH = "/opt/pht_results/age.csv"

if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV)
    age_sum = df["age"].describe()
    age_sum.to_csv(STORAGE_PATH)
