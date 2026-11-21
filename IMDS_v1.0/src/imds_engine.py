#!/usr/bin/env python3
"""IMDS v1.0 - Indian Multibagger Discovery System.
Runs on user-supplied price/fundamental CSVs; no unsupported live-data scraping.
"""
from __future__ import annotations
import argparse, math
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data' / 'input'
OUTPUT = ROOT / 'data' / 'output'


def read_csv_optional(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def score_sales(x):
    if pd.isna(x): return np.nan
    return 0 if x < 0 else 2 if x < .10 else 4 if x < .15 else 6 if x < .20 else 8 if x < .30 else 10

def score_pat(x):
    if pd.isna(x): return np.nan
    return 0 if x < 0 else 2 if x < .10 else 4 if x < .20 else 7 if x < .30 else 9 if x < .40 else 12

def score_roce(x):
    if pd.isna(x): return np.nan
    return 0 if x < 8 else 3 if x < 12 else 5 if x < 15 else 8 if x < 20 else 10 if x < 25 else 12

def score_cash_conversion(x):
    if pd.isna(x): return np.nan
    return 0 if x < .4 else 3 if x < .6 else 6 if x < .8 else 8 if x < 1 else 10

def score_debt_equity(x):
    if pd.isna(x): return np.nan
    return 8 if x <= .25 else 6 if x <= .5 else 4 if x <= 1 else 2 if x <= 2 else 0

def score_pledge(x):
    if pd.isna(x): return np.nan
    return 8 if x == 0 else 6 if x <= 5 else 3 if x <= 20 else 0

def score_relative_strength(x):
    if pd.isna(x): return np.nan
    return 15 if x >= 20 else 12 if x >= 10 else 9 if x >= 5 else 5 if x >= 0 else 0

def score_volume(x):
    if pd.isna(x): return np.nan
    return 0 if x < 1 else 5 if x < 1.3 else 10 if x < 1.5 else 15 if x < 2 else 20

def score_valuation(pe, sector_pe=np.nan):
    if pd.isna(pe) or pe <= 0: return np.nan
    if pd.notna(sector_pe) and sector_pe > 0:
        ratio = pe / sector_pe
        return 10 if ratio <= .8 else 8 if ratio <= 1 else 5 if ratio <= 1.25 else 2 if ratio <= 1.6 else 0
    return 10 if pe <= 15 else 8 if pe <= 25 else 5 if pe <= 40 else 2 if pe <= 60 else 0

def weighted_available_score(row, cols, maxima, target=100):
    vals=[]
    for c,m in zip(cols,maxima):
        v=row.get(c, np.nan)
        if pd.notna(v): vals.append((float(v),m))
    if not vals: return np.nan, 0.0
    available=sum(m for _,m in vals)
    # Normalize only against available metrics, but expose completeness separately.
    raw=sum(v for v,_ in vals)
    max_raw=available
    return (raw/max_raw*target if max_raw else np.nan), available/target

def main():
    ap=argparse.ArgumentParser(description='Build IMDS ranked discovery report')
    ap.add_argument('--universe', default=str(INPUT/'stock_universe.csv'))
    ap.add_argument('--fundamentals', default=str(INPUT/'fundamentals.csv'))
    ap.add_argument('--technicals', default=str(INPUT/'technicals.csv'))
    ap.add_argument('--out', default=str(OUTPUT/'imds_ranked.csv'))
    args=ap.parse_args()
    uni=pd.read_csv(args.universe)
    if 'SYMBOL' not in uni: raise SystemExit('stock_universe.csv must contain SYMBOL')
    df=uni[['SYMBOL'] + (['NAME OF COMPANY'] if 'NAME OF COMPANY' in uni else [])].drop_duplicates('SYMBOL')
    f=read_csv_optional(Path(args.fundamentals)); t=read_csv_optional(Path(args.technicals))
    for frame,label in [(f,'fundamentals'),(t,'technicals')]:
        if not frame.empty and 'SYMBOL' not in frame: raise SystemExit(f'{label}.csv must contain SYMBOL')
    if not f.empty: df=df.merge(f,on='SYMBOL',how='left',suffixes=('','_fund'))
    if not t.empty: df=df.merge(t,on='SYMBOL',how='left',suffixes=('','_tech'))
    # Fundamentals input units: CAGR/growth in decimal (0.15 = 15%); ROCE, pledge in percent points.
    for col,fn in [('SALES_CAGR_3Y',score_sales),('PAT_CAGR_3Y',score_pat),('ROCE',score_roce),('CFO_PAT',score_cash_conversion),('DEBT_EQUITY',score_debt_equity),('PROMOTER_PLEDGE_PCT',score_pledge)]:
        df[col+'_SCORE']=df[col].apply(fn) if col in df else np.nan
    if {'LATEST_SALES_GROWTH_YOY','PREVIOUS_SALES_GROWTH_YOY'}.issubset(df.columns):
        df['ACCELERATION_SCORE']=np.where(df.LATEST_SALES_GROWTH_YOY>df.PREVIOUS_SALES_GROWTH_YOY,3,0)
    else: df['ACCELERATION_SCORE']=np.nan
    if {'LATEST_PAT_GROWTH_YOY','PREVIOUS_PAT_GROWTH_YOY'}.issubset(df.columns):
        add=np.where(df.LATEST_PAT_GROWTH_YOY>df.PREVIOUS_PAT_GROWTH_YOY,3,0)
        df['ACCELERATION_SCORE']=df['ACCELERATION_SCORE'].fillna(0)+add
    fund_cols=['SALES_CAGR_3Y_SCORE','PAT_CAGR_3Y_SCORE','ROCE_SCORE','CFO_PAT_SCORE','DEBT_EQUITY_SCORE','PROMOTER_PLEDGE_PCT_SCORE','ACCELERATION_SCORE']
    fund_max=[10,12,12,10,8,8,6]
    # Scale known fundamentals into a transparent 100-point available-data score.
    def calc_fund(r):
        present=[(r[c],m) for c,m in zip(fund_cols,fund_max) if pd.notna(r.get(c))]
        if not present:return pd.Series([np.nan,0.0])
        return pd.Series([sum(v for v,_ in present)/sum(m for _,m in present)*100, sum(m for _,m in present)/sum(fund_max)])
    df[['FUNDAMENTAL_SCORE','FUNDAMENTAL_COMPLETENESS']]=df.apply(calc_fund,axis=1)
    # Technical CSV columns: CLOSE_ABOVE_200DMA, DMA50_ABOVE_200DMA, DMA200_RISING,
    # RS_6M_PP (percentage points), NEAR_6M_RESISTANCE, BREAKOUT_VOLUME_RATIO,
    # TIGHT_CONSOLIDATION, WEEKLY_CONFIRMATION, CLOSE_ABOVE_50DMA.
    points=[]
    specs=[('CLOSE_ABOVE_200DMA',10),('DMA50_ABOVE_200DMA',10),('DMA200_RISING',10),('RS_6M_PP',15),('NEAR_6M_RESISTANCE',10),('BREAKOUT_VOLUME_RATIO',20),('TIGHT_CONSOLIDATION',10),('WEEKLY_CONFIRMATION',10),('CLOSE_ABOVE_50DMA',5)]
    for c,m in specs:
        if c in df:
            if c=='RS_6M_PP': s=df[c].apply(score_relative_strength)
            elif c=='BREAKOUT_VOLUME_RATIO': s=df[c].apply(score_volume)
            else: s=pd.to_numeric(df[c],errors='coerce').apply(lambda x: np.nan if pd.isna(x) else m if bool(x) else 0)
        else:s=pd.Series(np.nan,index=df.index)
        df[c+'_PTS']=s
        points.append(c+'_PTS')
    def calc_tech(r):
        p=[r[c] for c in points if pd.notna(r[c])]
        if not p:return pd.Series([np.nan,0.0])
        maxp=sum(dict(specs)[c.replace('_PTS','')] for c in points if pd.notna(r[c]))
        return pd.Series([sum(p)/maxp*100 if maxp else np.nan,maxp/100])
    df[['TECHNICAL_SCORE','TECHNICAL_COMPLETENESS']]=df.apply(calc_tech,axis=1)
    df['COMBINED_SCORE']=df.apply(lambda r: .6*r.FUNDAMENTAL_SCORE+.4*r.TECHNICAL_SCORE if pd.notna(r.FUNDAMENTAL_SCORE) and pd.notna(r.TECHNICAL_SCORE) else np.nan,axis=1)
    df['RISK_FLAG']='AMBER'
    if 'PROMOTER_PLEDGE_PCT' in df: df.loc[df.PROMOTER_PLEDGE_PCT>20,'RISK_FLAG']='RED'
    if 'DEBT_EQUITY' in df: df.loc[df.DEBT_EQUITY>2,'RISK_FLAG']='RED'
    if 'PROMOTER_PLEDGE_PCT' in df: df.loc[(df.PROMOTER_PLEDGE_PCT==0)&(df.RISK_FLAG=='AMBER'),'RISK_FLAG']='GREEN'
    df['CLASSIFICATION']=np.select([df.RISK_FLAG.eq('RED'),df.COMBINED_SCORE.ge(85),df.COMBINED_SCORE.ge(75),df.COMBINED_SCORE.ge(65),df.COMBINED_SCORE.ge(50)],['REVIEW / BLOCK','ELITE','HIGH PRIORITY','DEVELOPING','MONITOR'],default='LOW PRIORITY')
    if 'UNIVERSE' in df: df.loc[df.UNIVERSE.isna(),'CLASSIFICATION']='UNIVERSE NOT MAPPED'
    df['RANK']=df.COMBINED_SCORE.rank(method='min',ascending=False).astype('Int64')
    df['DATA_QUALITY']='INCOMPLETE'
    df.loc[(df.FUNDAMENTAL_COMPLETENESS>=.7)&(df.TECHNICAL_COMPLETENESS>=.7),'DATA_QUALITY']='USABLE (>=70% inputs)'
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    df.sort_values(['RANK','SYMBOL'],na_position='last').to_csv(args.out,index=False)
    print(f'IMDS complete: {len(df)} symbols -> {args.out}')
    print('Reminder: scores are research prioritization, not buy/sell advice. Validate source dates, sector rules, liquidity and point-in-time universe before backtesting.')

if __name__=='__main__': main()
