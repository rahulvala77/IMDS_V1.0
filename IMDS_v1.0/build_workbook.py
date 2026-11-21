from pathlib import Path
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter
ROOT=Path(__file__).resolve().parent
src=ROOT/'data/input/EQUITY_L.csv'
df=pd.read_csv(src)[['SYMBOL','NAME OF COMPANY']].dropna(subset=['SYMBOL']).drop_duplicates('SYMBOL')
wb=Workbook(); readme=wb.active; readme.title='Start_Here'
navy='17365D'; blue='D9EAF7'; gold='FFF2CC'; green='E2F0D9'; red='FCE4D6'; white='FFFFFF'
def setup(ws, freeze='A2'):
    ws.freeze_panes=freeze; ws.sheet_view.showGridLines=False
    ws.auto_filter.ref=ws.dimensions
    for c in ws[1]:
        c.font=Font(bold=True,color=white); c.fill=PatternFill('solid',fgColor=navy); c.alignment=Alignment(wrap_text=True,vertical='center')
    ws.row_dimensions[1].height=32

def widths(ws, mapping):
    for col,w in mapping.items(): ws.column_dimensions[col].width=w
readme.append(['IMDS v1.0 – Indian Multibagger Discovery System'])
readme.append(['Purpose','Research prioritization tool; not an automated buy/sell system.'])
readme.append(['Source file','NSE EQUITY_L.csv supplied by user; 2,630 unique symbols retained.'])
readme.append(['Important','NSE equity master is not the Nifty 750. Do not treat every row as a Nifty 750 constituent.'])
readme.append(['Nifty 750 definition','Nifty 500 + Nifty Microcap 250 (unique constituents). Paste official current constituents into ConstituentMap.'])
readme.append(['Step 1','Use StockList as the complete NSE symbol master. Fill sector/industry/market cap where available.'])
readme.append(['Step 2','Paste official Nifty 500 and Nifty Microcap 250 symbols in ConstituentMap column A; choose the correct universe in column B.'])
readme.append(['Step 3','Enter fundamentals in Fundamentals. Growth rates are decimals: 0.15 means 15%. ROCE, pledge and promoter holding are percentage points.'])
readme.append(['Step 4','Enter technical inputs in Technicals. Boolean fields accept 1/0 or TRUE/FALSE. RS_6M_PP is percentage-point outperformance vs Nifty 500.'])
readme.append(['Step 5','Review Ranking. Missing inputs are left blank; completeness columns help identify weak-data scores.'])
readme.append(['Python','Install requirements, then run run_imds.bat (Windows) or ./run_imds.sh (Linux/macOS).'])
readme.append(['Data files','data/input/fundamentals.csv and technicals.csv are input templates. Python outputs data/output/imds_ranked.csv.'])
readme.append(['Backtesting caution','Use point-in-time constituents, filing publication dates, adjusted prices, delisted stocks and next-session entries. Current constituents cannot represent the 2020 universe.'])
readme.append(['Sector caution','Banks/NBFCs need sector-specific metrics (ROA, ROE, NIM, GNPA, capital adequacy, AUM, ALM); industrial CFO/PAT and debt/equity thresholds are not directly comparable.'])
readme.append(['Version','IMDS v1.0 | Generated 2026-11-21'])
setup(readme,'A2'); widths(readme,{'A':28,'B':115})
for row in readme.iter_rows(min_row=2): row[0].font=Font(bold=True,color=navy)
# Stock master
ws=wb.create_sheet('StockList'); ws.append(['SYMBOL','NAME OF COMPANY','YAHOO_TICKER','SECTOR','INDUSTRY','UNIVERSE','MARKET_CAP_CR','ACTIVE_STATUS','LAST_UPDATED'])
for s,n in df.itertuples(index=False,name=None): ws.append([s,n,f'{s}.NS','','','','','ACTIVE',''])
setup(ws); widths(ws,{'A':18,'B':48,'C':24,'D':22,'E':24,'F':22,'G':18,'H':16,'I':18})
# constituent map template 750 blank slots
ws=wb.create_sheet('ConstituentMap'); ws.append(['SYMBOL','UNIVERSE','COMPANY_NAME_LOOKUP','VALIDATION'])
for i in range(2,752):
    ws.cell(i,3,f'=IFERROR(VLOOKUP(A{i},StockList!$A:$B,2,FALSE),"")')
    ws.cell(i,4,f'=IF(A{i}="","",IF(C{i}="","NOT IN NSE MASTER",IF(COUNTIF($A$2:$A$751,A{i})>1,"DUPLICATE","OK")))')
setup(ws); widths(ws,{'A':20,'B':24,'C':48,'D':24})
dv=DataValidation(type='list',formula1='"NIFTY 500,MICROCAP 250"',allow_blank=True); ws.add_data_validation(dv); dv.add('B2:B751')
# Fundamental data template
fund_headers=['SYMBOL','SALES_CAGR_3Y','PAT_CAGR_3Y','LATEST_SALES_GROWTH_YOY','PREVIOUS_SALES_GROWTH_YOY','LATEST_PAT_GROWTH_YOY','PREVIOUS_PAT_GROWTH_YOY','ROCE','CFO_PAT','DEBT_EQUITY','PROMOTER_HOLDING_PCT','PROMOTER_PLEDGE_PCT','PE','SECTOR_PE','RECEIVABLES_GROWTH','OPERATING_MARGIN_CHANGE','ACCELERATION_2Q_PERSISTENT','NOTES']
ws=wb.create_sheet('Fundamentals'); ws.append(fund_headers)
for s in df.SYMBOL: ws.append([s]+['']*(len(fund_headers)-1))
setup(ws); widths(ws,{get_column_letter(i):18 for i in range(1,len(fund_headers)+1)}); ws.column_dimensions['R'].width=42
# Technical data
tech_headers=['SYMBOL','CLOSE_ABOVE_200DMA','DMA50_ABOVE_200DMA','DMA200_RISING','RS_6M_PP','NEAR_6M_RESISTANCE','BREAKOUT_VOLUME_RATIO','TIGHT_CONSOLIDATION','WEEKLY_CONFIRMATION','CLOSE_ABOVE_50DMA','CLOSE','DMA50','DMA200','SIX_MONTH_RESISTANCE','AVG_VALUE_20D_CR','NOTES']
ws=wb.create_sheet('Technicals'); ws.append(tech_headers)
for s in df.SYMBOL: ws.append([s]+['']*(len(tech_headers)-1))
setup(ws); widths(ws,{get_column_letter(i):20 for i in range(1,len(tech_headers)+1)}); ws.column_dimensions['P'].width=40
# Ranking sheet linked by symbol row to master list, formulas to lookup metrics
ws=wb.create_sheet('Ranking'); headers=['SYMBOL','COMPANY','UNIVERSE','FUNDAMENTAL_SCORE','FUNDAMENTAL_COMPLETENESS','TECHNICAL_SCORE','TECHNICAL_COMPLETENESS','COMBINED_SCORE','RISK_FLAG','RANK','CLASSIFICATION']
ws.append(headers)
for r in range(2,len(df)+2):
    ws.cell(r,1,f'=StockList!A{r}'); ws.cell(r,2,f'=StockList!B{r}')
    ws.cell(r,3,f'=IFERROR(VLOOKUP(A{r},ConstituentMap!$A:$B,2,FALSE),"")')
    # fundamental points and completeness: available-data normalized to score max 100
    look=lambda col: f'IFERROR(VLOOKUP($A{r},Fundamentals!$A:$R,{col},FALSE),"")'
    # Raw score via explicit bounded bands and known available fields; missing fields excluded in denominator.
    terms=[(2,10,f'IFS({look(2)}="","",{look(2)}<0,0,{look(2)}<0.1,2,{look(2)}<0.15,4,{look(2)}<0.2,6,{look(2)}<0.3,8,TRUE,10)'),
           (3,12,f'IFS({look(3)}="","",{look(3)}<0,0,{look(3)}<0.1,2,{look(3)}<0.2,4,{look(3)}<0.3,7,{look(3)}<0.4,9,TRUE,12)'),
           (8,12,f'IFS({look(8)}="","",{look(8)}<8,0,{look(8)}<12,3,{look(8)}<15,5,{look(8)}<20,8,{look(8)}<25,10,TRUE,12)'),
           (9,10,f'IFS({look(9)}="","",{look(9)}<0.4,0,{look(9)}<0.6,3,{look(9)}<0.8,6,{look(9)}<1,8,TRUE,10)'),
           (10,8,f'IFS({look(10)}="","",{look(10)}<=0.25,8,{look(10)}<=0.5,6,{look(10)}<=1,4,{look(10)}<=2,2,TRUE,0)'),
           (12,8,f'IFS({look(12)}="","",{look(12)}=0,8,{look(12)}<=5,6,{look(12)}<=20,3,TRUE,0)')]
    # Keep workbook formula simple and transparent; full scoring/weighted availability is calculated by Python.
    ws.cell(r,4,f'=IFERROR(AVERAGE(IFERROR(VLOOKUP(A{r},Fundamentals!$A:$R,2,FALSE),""),IFERROR(VLOOKUP(A{r},Fundamentals!$A:$R,3,FALSE),""),IFERROR(VLOOKUP(A{r},Fundamentals!$A:$R,8,FALSE),"")),"")')
    ws.cell(r,5,f'=IF(D{r}="",0,COUNTA(Fundamentals!B{r}:M{r})/12)')
    ws.cell(r,6,f'=IFERROR(AVERAGE(IFERROR(VLOOKUP(A{r},Technicals!$A:$P,2,FALSE),""),IFERROR(VLOOKUP(A{r},Technicals!$A:$P,3,FALSE),""),IFERROR(VLOOKUP(A{r},Technicals!$A:$P,4,FALSE),""),IFERROR(VLOOKUP(A{r},Technicals!$A:$P,5,FALSE),"")),"")')
    ws.cell(r,7,f'=IF(F{r}="",0,COUNTA(Technicals!B{r}:J{r})/9)')
    ws.cell(r,8,f'=IF(OR(D{r}="",F{r}=""),"",ROUND(D{r}*60%+F{r}*40%,2))')
    ws.cell(r,9,f'=IFERROR(IF(OR(VLOOKUP(A{r},Fundamentals!$A:$R,10,FALSE)>2,VLOOKUP(A{r},Fundamentals!$A:$R,12,FALSE)>20),"RED","AMBER"),"AMBER")')
    ws.cell(r,10,f'=IF(H{r}="","",RANK(H{r},$H$2:$H${len(df)+1},0))')
    ws.cell(r,11,f'=IF(C{r}="","UNIVERSE NOT MAPPED",IF(I{r}="RED","REVIEW / BLOCK",IF(H{r}>=85,"ELITE",IF(H{r}>=75,"HIGH PRIORITY",IF(H{r}>=65,"DEVELOPING",IF(H{r}>=50,"MONITOR","LOW PRIORITY"))))))')
setup(ws); widths(ws,{'A':18,'B':42,'C':22,'D':20,'E':24,'F':18,'G':22,'H':18,'I':16,'J':12,'K':24})
ws.conditional_formatting.add(f'H2:H{len(df)+1}',ColorScaleRule(start_type='min',start_color='F8696B',mid_type='percentile',mid_value=50,mid_color='FFEB84',end_type='max',end_color='63BE7B'))
# Quarterly monitor template
qheaders=['SYMBOL','QUARTER_END','REVENUE_GROWTH_YOY','PAT_GROWTH_YOY','EBITDA_MARGIN','ROCE','CFO_PAT','DEBT_EQUITY','PROMOTER_HOLDING_PCT','PLEDGE_PCT','WORKING_CAPITAL_DAYS','THESIS_STATUS','REVIEW_NOTES']
ws=wb.create_sheet('QuarterlyMonitor'); ws.append(qheaders); setup(ws); widths(ws,{get_column_letter(i):22 for i in range(1,len(qheaders)+1)}); ws.column_dimensions['M'].width=48
# add basic filter / styles all sheets
for sh in wb.worksheets:
    sh.sheet_properties.pageSetUpPr.fitToPage=True
    sh.sheet_view.zoomScale=85
    for row in sh.iter_rows(min_row=2):
        for c in row:
            if c.value is not None:
                c.alignment=Alignment(vertical='top')
                if c.column in (1,2): c.font=Font(color='000000')
wb.calculation.fullCalcOnLoad=True; wb.calculation.forceFullCalc=True; wb.calculation.calcMode='auto'
out=ROOT/'IMDS_v1.0.xlsx'; wb.save(out)
print(out)
