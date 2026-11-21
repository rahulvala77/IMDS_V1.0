#!/usr/bin/env python3
"""Normalize NSE EQUITY_L.csv into the IMDS stock master and input template."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'data/input/EQUITY_L.csv'
df=pd.read_csv(src)
df=df[['SYMBOL','NAME OF COMPANY']].dropna(subset=['SYMBOL']).drop_duplicates('SYMBOL')
df['YAHOO_TICKER']=df['SYMBOL'].astype(str)+'.NS'
df['SECTOR']=''; df['INDUSTRY']=''; df['UNIVERSE']=''; df['MARKET_CAP_CR']=''; df['ACTIVE_STATUS']='ACTIVE'; df['LAST_UPDATED']=''
out=ROOT/'data/input/stock_universe.csv'; df.to_csv(out,index=False)
print(f'Created {out} with {len(df)} unique NSE symbols. UNIVERSE remains blank until official constituents are mapped.')
