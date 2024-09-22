import pandas as pd


def google_sheets_to_df(sheet_url: str) -> pd.DataFrame:
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv'
    return pd.read_csv(csv_url)
