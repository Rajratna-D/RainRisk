"""
RainRisk: chronological split. Random splits leak future info into
training via rolling/lag features, so splits must be by year, not row.
"""
import pandas as pd


def chronological_split(df, year_col="YEAR", train_end=2000, val_end=2010):
    if train_end >= val_end:
        raise ValueError(f"train_end ({train_end}) must be strictly less than val_end ({val_end})")
    if year_col not in df.columns:
        raise KeyError(f"Column '{year_col}' not found in DataFrame")
    train = df[df[year_col] <= train_end].copy()
    val = df[(df[year_col] > train_end) & (df[year_col] <= val_end)].copy()
    test = df[df[year_col] > val_end].copy()
    return train, val, test
