# Indicator Signal Engine – Chatbot Test Prompts
### 20 Comprehensive Prompts to Validate ISE Strategy Generation

---

## PROMPT 1 — Basic SuperTrend FUT Strategy (Core Basics)
**Tests:** Strategy Name, Symbol, Exchange, Segment=FUT, Contract=NEAR, Expiry=MONTHLY, Intraday/MIS, Entry/Sqroff Time, Single SuperTrend indicator (default params), Signal=Both, Default weekDays

> "Create a BankNifty intraday strategy using SuperTrend indicator on 5 minute chart. Use 1 lot of BankNifty futures, near contract, monthly expiry. Entry at 9:15, sqroff at 15:15. Trade both BUY and SELL signals."

**Expected Output Validation:**
- Main: isIntraday=true, entryOrderProduct=MIS, exitOrderProduct=MIS, chartType=Candlestick, timeFrame=5Min, signal=Both, entryTime=09:15, sqroffTime=15:15
- Sub Leg 1: exchange=NFO, segment=FUT, symbol=BANKNIFTY, contract=NEAR, expiry=MONTHLY, atm=0, optionType="", lot=1, qty=30, isTrailSl=false, isReverseSignal=false
- Indicator 1: index=1, indicator_code=supertrend, length=10, factor=3

---

## PROMPT 2 — MA CrossOver Custom Params + OPT CE+PE Legs + Reverse Signal
**Tests:** MA CrossOver with custom short/long/type=EMA, OPT segment, CE normal + PE reverse signal, ATM=0, Weekly expiry, 2 lots, 15 min timeframe, custom entry/sqroff

> "Nifty options strategy on 15 minute chart using MA CrossOver. Short=5, Long=20, type EMA. Leg 1: Buy CE ATM weekly near 2 lots (normal signal). Leg 2: Buy PE ATM weekly near 2 lots with reverse signal. Entry at 9:30, sqroff 15:00. Intraday, signal=Both."

**Expected Output Validation:**
- Main: timeFrame=15Min, entryTime=09:30, sqroffTime=15:00, isIntraday=true
- Sub Leg 1: symbol=NIFTY, segment=OPT, optionType=CE, atm=0, expiry=WEEKLY, lot=2, isReverseSignal=false
- Sub Leg 2: segment=OPT, optionType=PE, atm=0, expiry=WEEKLY, lot=2, isReverseSignal=true
- Indicator 1: index=1, indicator_code=ma-cross-over, short=5, long=20, type=EMA

---

## PROMPT 3 — RSI Custom Bands + Leg-Level SL + Signal=BUY
**Tests:** RSI with custom length/bands, Leg SL (Money), signal=BUY only, FUT segment, WEEKLY expiry

> "BankNifty RSI strategy on 5 minute chart. RSI length 21, lower band 25, upper band 75. Trade only BUY signals. Use 1 lot BankNifty futures weekly near contract. Set leg stoploss 3000 rupees. Entry at 9:20, sqroff 15:15. Intraday."

**Expected Output Validation:**
- Main: signal=BUY, timeFrame=5Min, entryTime=09:20
- Sub Leg 1: segment=FUT, symbol=BANKNIFTY, expiry=WEEKLY, lot=1, qty=30, sl=3000, slBy=Money, target=0, isTrailSl=false
- Indicator 1: index=1, indicator_code=rsi, length=21, lower-band=25, upper-band=75

---

## PROMPT 4 — MACD All 6 Parameters + Leg Target + Leg SL + Signal=SELL
**Tests:** MACD with all 6 custom params, leg target (Money), leg SL (Money), signal=SELL, 10Min timeframe, ATM offsets CE/PE

> "Nifty MACD strategy on 10 minute chart. MACD fast=8, slow=21, source=High, signal length=5, oscillator type=SMA, signal line type=SMA. Trade only SELL signals. Leg 1: CE ATM+100 weekly near 1 lot, target 2000 rupees SL 1500 rupees. Leg 2: PE ATM-100 weekly near 1 lot, target 2000 rupees SL 1500 rupees. Entry 9:20. Intraday."

**Expected Output Validation:**
- Main: signal=SELL, timeFrame=10Min, entryTime=09:20
- Sub Leg 1: optionType=CE, atm=100, target=2000, targetBy=Money, sl=1500, slBy=Money
- Sub Leg 2: optionType=PE, atm=-100, target=2000, sl=1500
- Indicator 1: index=1, indicator_code=macd, fast-length=8, slow-length=21, source=High, signal-length=5, oscillator-ma-type=SMA, signal-line-ma-type=SMA

---

## PROMPT 5 — Stochastic + Bollinger Bands AND Logic (Same Index)
**Tests:** Two indicators in same row = AND logic (index=1 for both), Stochastic custom params, BB custom params, 30Min chart

> "BankNifty futures strategy: Entry only when Stochastic AND Bollinger Bands both signal together. Stochastic K=9, D=3, lower=25, upper=75. Bollinger Bands length=15, multiplier=3, source=Close. 30 minute chart, signal=Both, 1 lot near monthly. Entry 9:15. Intraday."

**Expected Output Validation:**
- Main: timeFrame=30Min
- Sub Leg 1: segment=FUT, symbol=BANKNIFTY, expiry=MONTHLY, lot=1
- Indicator 1: index=1, indicator_code=stochastic, k-length=9, d-length=3, lower-band=25, upper-band=75
- Indicator 2: index=1, indicator_code=bollinger-bands, length=15, multiplier=3 (SAME index=1 → AND logic)

---

## PROMPT 6 — SuperTrend OR RSI (Different Indexes = OR Logic) + Leg Trail SL
**Tests:** OR logic via different index values, leg-level trail SL (trailSlMarketMove, trailSlMove, noOfTimeTrailSl), 1Hour timeframe

> "Nifty futures strategy: Entry when SuperTrend signals OR RSI signals (either one triggers entry). SuperTrend default params. RSI default params. 1 hour chart, signal=Both. Leg-level trail SL: after every 500 profit move trail SL by 200, max 3 times. 1 lot near weekly. Entry 9:15. Intraday."

**Expected Output Validation:**
- Main: timeFrame=1Hour
- Indicator 1: index=1, indicator_code=supertrend (different index from RSI → OR logic)
- Indicator 2: index=2, indicator_code=rsi
- Sub Leg 1: isTrailSl=true, trailSlMarketMove=500, trailSlMove=200, noOfTimeTrailSl=3

---

## PROMPT 7 — Reverse Signal Hedge (CE Normal + PE Reverse) + Master Target
**Tests:** isReverseSignal=true on PE leg, isReverseSignal=false on CE, master target, signal=Both, OPT weekly

> "BankNifty hedge strategy using SuperTrend 5 min chart. Leg 1: CE ATM weekly near 1 lot, normal signal. Leg 2: PE ATM weekly near 1 lot, reverse signal (takes opposite of indicator direction). Signal=Both. Master target 4000 rupees. Entry 9:15, sqroff 15:15. Intraday."

**Expected Output Validation:**
- Sub Leg 1: optionType=CE, atm=0, isReverseSignal=false, callType=BUY
- Sub Leg 2: optionType=PE, atm=0, isReverseSignal=true, callType=BUY
- masterTarget=4000
- masterSl=0

---

## PROMPT 8 — Master Target + Master SL + Master Trail SL
**Tests:** masterTarget (non-zero), masterSl (non-zero), isTrailSl=true at master level, profitMove, slMove, noOfTrailSl

> "BankNifty futures SuperTrend 5 min strategy, 1 lot near weekly. Set master target 5000 rupees and master SL 3000 rupees. Enable master trail SL: every time combined profit increases by 2000 rupees, trail the master SL by 1000 rupees, max 5 times. Entry 9:20, sqroff 15:15. Intraday."

**Expected Output Validation:**
- masterTarget=5000
- masterSl=3000
- isTrailSl=true (master level)
- profitMove=2000
- slMove=1000
- noOfTrailSl=5

---

## PROMPT 9 — (SuperTrend AND MA CrossOver) OR RSI (3 Indicators Mixed)
**Tests:** 3 indicators, complex AND/OR: index=1 for SuperTrend+MACross (AND), index=2 for RSI (OR), custom params

> "Nifty futures strategy. Entry condition: SuperTrend AND MA CrossOver must both agree (same row), OR RSI alone (different row). SuperTrend length=7, factor=2. MA CrossOver short=5, long=13, type=EMA. RSI default params. 5 min Candlestick, signal=Both, 1 lot near monthly. Entry 9:15. Intraday."

**Expected Output Validation:**
- Indicator 1: index=1, indicator_code=supertrend, length=7, factor=2
- Indicator 2: index=1, indicator_code=ma-cross-over, short=5, long=13, type=EMA (SAME index=1 → AND with supertrend)
- Indicator 3: index=2, indicator_code=rsi (DIFFERENT index=2 → OR with row 1)
- indicator_count=3

---

## PROMPT 10 — Heikin-Ashi Chart + 2Hour TimeFrame + Specific WeekDays
**Tests:** chartType=Heikin-Ashi, timeFrame=2Hour, weekDays restricted (Tue, Thu, Fri only)

> "BankNifty futures strategy using Heikin-Ashi 2 hour chart. Use default SuperTrend. Only trade on Tuesday, Thursday and Friday. 1 lot near monthly. Entry 9:15, sqroff 15:15. Signal Both. Intraday. Underlying type Future."

**Expected Output Validation:**
- Main: chartType=Heikin-Ashi, timeFrame=2Hour, underlyingType=Future
- weekDays contains TUE, THU, FRI (does NOT contain MON or WED)
- Indicator 1: indicator_code=supertrend, default params

---

## PROMPT 11 — Positional + NRML Products + Sqroff Before Expiry + 1Day Chart
**Tests:** isIntraday=false, entryOrderProduct=NRML, exitOrderProduct=NRML, timeFrame=1Day, sqroffBeforeExDays=2, monthly expiry

> "Create a positional Nifty strategy with NRML product. 1 lot Nifty futures near monthly expiry. Use MA CrossOver default settings on daily chart. Entry 9:15, sqroff 15:15. Square off 2 days before expiry. Signal Both. Underlying type Future."

**Expected Output Validation:**
- Main: isIntraday=false, entryOrderProduct=NRML, exitOrderProduct=NRML, timeFrame=1Day
- sqroffBeforeExDays=2
- Sub Leg 1: segment=FUT, symbol=NIFTY, expiry=MONTHLY
- Indicator 1: indicator_code=ma-cross-over (default: short=9, long=26, type=SMA)

---

## PROMPT 12 — BFO Exchange (SENSEX) + CE/PE ATM Offsets + Master SL
**Tests:** exchange=BFO, symbol=SENSEX, OPT segment, positive CE ATM offset, negative PE ATM offset, reverse signal on PE, masterSl

> "SENSEX BFO options strategy using SuperTrend 5 min. Leg 1: CE ATM+200 weekly near 1 lot normal signal. Leg 2: PE ATM-200 weekly near 1 lot reverse signal. Master SL 5000 rupees, no master target. Entry 9:15. Intraday. Signal=Both."

**Expected Output Validation:**
- Sub Leg 1: exchange=BFO, symbol=SENSEX, segment=OPT, optionType=CE, atm=200, isReverseSignal=false
- Sub Leg 2: exchange=BFO, symbol=SENSEX, segment=OPT, optionType=PE, atm=-200, isReverseSignal=true
- masterSl=5000
- masterTarget=0

---

## PROMPT 13 — 3 Legs Mixed Segments (OPT CE + OPT PE + FUT) + NEXT Contract
**Tests:** 3-leg structure, OPT + FUT mix, NEAR vs NEXT contract, WEEKLY vs MONTHLY expiry, different lots per leg

> "Nifty 3-leg strategy: Leg 1 — Buy CE ATM OPT near weekly 1 lot. Leg 2 — Buy PE ATM OPT near weekly 1 lot reverse signal. Leg 3 — Buy 2 lots Nifty futures NEXT contract monthly as hedge. RSI default on 5 min chart. Signal Both. Entry 9:15. Intraday."

**Expected Output Validation:**
- Sub Leg 1: segment=OPT, optionType=CE, contract=NEAR, expiry=WEEKLY, lot=1, isReverseSignal=false
- Sub Leg 2: segment=OPT, optionType=PE, contract=NEAR, expiry=WEEKLY, lot=1, isReverseSignal=true
- Sub Leg 3: segment=FUT, contract=NEXT, expiry=MONTHLY, lot=2
- sub_count=3

---

## PROMPT 14 — Underlying Type=Spot/Index + Signal=SELL + Custom SuperTrend
**Tests:** underlyingType=Spot/Index, signal=SELL, custom SuperTrend params, 15Min timeframe

> "BankNifty futures strategy. Compute indicators on Spot/Index data (not futures). Trade only SELL signals. SuperTrend length=12, factor=2 on 15 minute chart. 1 lot near weekly. Entry 9:20, sqroff 15:15. Intraday."

**Expected Output Validation:**
- Main: underlyingType=Spot/Index, signal=SELL, timeFrame=15Min, entryTime=09:20
- Indicator 1: indicator_code=supertrend, length=12, factor=2

---

## PROMPT 15 — Candlestick Patterns (Hammer OR Evening Star) + OPT Legs
**Tests:** Candlestick patterns (no parameters), OR logic with patterns, hammer=BUY signal, evening-star=SELL signal

> "BankNifty options strategy using candlestick patterns. Entry when Hammer pattern fires (row 1) OR Evening Star pattern fires (row 2). Leg 1: CE ATM weekly near 1 lot normal signal. Leg 2: PE ATM weekly near 1 lot reverse signal. 5 min Candlestick, signal=Both. Entry 9:15, sqroff 15:15. Intraday."

**Expected Output Validation:**
- Indicator 1: index=1, indicator_code=hammer, parameter=[] (no parameters)
- Indicator 2: index=2, indicator_code=evening-star, parameter=[] (OR logic — different index)
- Sub Leg 1: optionType=CE, isReverseSignal=false
- Sub Leg 2: optionType=PE, isReverseSignal=true

---

## PROMPT 16 — Leg Trail SL Unlimited + Master SL Only (No Master Target)
**Tests:** noOfTimeTrailSl=0 (unlimited), master SL without master target, MACD indicator

> "Nifty futures weekly 5 min chart using MACD default settings. 1 lot near. Leg-level trail SL: for every 300 point profit move, trail SL by 150 points, unlimited trails. Master SL 4000 rupees, no master target. Entry 9:20, sqroff 15:15. Intraday."

**Expected Output Validation:**
- masterTarget=0
- masterSl=4000
- isTrailSl=false (master level, since no master trail SL specified)
- Sub Leg 1: isTrailSl=true, trailSlMarketMove=300, trailSlMove=150, noOfTimeTrailSl=0 (unlimited)
- Indicator 1: indicator_code=macd (default params)

---

## PROMPT 17 — 4 Legs Different Lots + Trail SL Per Leg + Master Target + WeekDays
**Tests:** 4 legs, different lots, per-leg trail SL on leg 1, weekDays restricted, master target, custom times

> "BankNifty 4-leg OPT strategy using SuperTrend 5 min. Leg 1: CE ATM weekly 2 lots, SL 2500, trail SL every 1000 profit trail by 500 max 3 times. Leg 2: PE ATM weekly 2 lots reverse signal, SL 2500. Leg 3: CE ATM+300 weekly 1 lot. Leg 4: PE ATM-300 weekly 1 lot reverse signal. Trade only Monday, Wednesday, Friday. Master target 6000 rupees. Entry 9:20, sqroff 15:10. Intraday."

**Expected Output Validation:**
- Sub Leg 1: optionType=CE, atm=0, lot=2, sl=2500, isTrailSl=true, trailSlMarketMove=1000, trailSlMove=500, noOfTimeTrailSl=3, isReverseSignal=false
- Sub Leg 2: optionType=PE, atm=0, lot=2, sl=2500, isReverseSignal=true
- Sub Leg 3: optionType=CE, atm=300, lot=1
- Sub Leg 4: optionType=PE, atm=-300, lot=1, isReverseSignal=true
- weekDays contains MON, WED, FRI (does NOT contain TUE or THU)
- masterTarget=6000
- entryTime=09:20, sqroffTime=15:10
- sub_count=4

---

## PROMPT 18 — NEXT Contract + WEEKLY Expiry + 4Hour Chart + Positional + Sqroff Before Expiry
**Tests:** contract=NEXT, expiry=WEEKLY, timeFrame=4Hour, positional/NRML, sqroffBeforeExDays, Stochastic custom params

> "Nifty positional NRML strategy using Stochastic on 4 hour chart. K=12, D=4, lower=25, upper=75. Leg 1: CE ATM NEXT weekly 1 lot. Leg 2: PE ATM NEXT weekly 1 lot reverse signal. Sqroff 1 day before expiry. Signal=Both. Entry 9:15."

**Expected Output Validation:**
- Main: isIntraday=false, entryOrderProduct=NRML, exitOrderProduct=NRML, timeFrame=4Hour
- sqroffBeforeExDays=1
- Sub Leg 1: contract=NEXT, expiry=WEEKLY, optionType=CE, isReverseSignal=false
- Sub Leg 2: contract=NEXT, expiry=WEEKLY, optionType=PE, isReverseSignal=true
- Indicator 1: indicator_code=stochastic, k-length=12, d-length=4, lower-band=25, upper-band=75

---

## PROMPT 19 — Multiple Candlestick Patterns (AND + OR) + Descriptions
**Tests:** Three White Soldiers AND Hammer in same row (AND), Morning Star in separate row (OR), shortDescription, longDescription

> "BankNifty CE ATM weekly 1 lot strategy. Entry when (Three White Soldiers AND Hammer both fire) OR Morning Star fires alone. 5 min Candlestick, signal=BUY. Entry 9:30, sqroff 15:15. Intraday. Short description: 'BNF bullish pattern combo strategy.' Long description: 'Uses Three White Soldiers and Hammer patterns in AND logic for strong bullish confirmation on BankNifty weekly CE options.'"

**Expected Output Validation:**
- Indicator 1: index=1, indicator_code=three-white-soldiers, parameter=[]
- Indicator 2: index=1, indicator_code=hammer, parameter=[] (SAME index=1 → AND with three-white-soldiers)
- Indicator 3: index=2, indicator_code=morning-star, parameter=[] (DIFFERENT index=2 → OR)
- signal=BUY
- entryTime=09:30
- shortDescription contains "BNF" or "bullish" or "pattern"
- longDescription contains "Three White Soldiers" or "BankNifty"

---

## PROMPT 20 — Maximum Complexity (ALL Parameters)
**Tests:** ALL parameters — 4 legs mixed OPT+FUT, multiple indicators AND+OR, leg trail SL, master target+SL+trail SL, reverse signal, Heikin-Ashi, 30Min, custom weekDays, positional, sqroffBeforeExDays, custom entry/sqroff, descriptions

> "Create a positional BankNifty strategy called 'ISE Full Combo', NRML product.
>
> Leg 1: CE ATM OPT weekly near 2 lots, reverse signal OFF. SL 3000 rupees. Trail SL: every 1500 profit trail by 600, max 4 times.
>
> Leg 2: PE ATM OPT weekly near 2 lots, reverse signal ON. SL 3000 rupees.
>
> Leg 3: CE ATM+200 OPT weekly near 1 lot, normal signal.
>
> Leg 4: BankNifty futures near monthly 1 lot as hedge, normal signal.
>
> Entry condition: (SuperTrend length=10 factor=3 AND MA CrossOver short=9 long=26 type=SMA — same row) OR (RSI length=14 all defaults — separate row) OR (MACD all defaults — separate row).
>
> Heikin-Ashi chart, 30 minute timeframe. Signal=Both. Only trade Monday, Tuesday, Wednesday. Underlying type=Spot/Index. Entry 9:20, sqroff 15:15.
>
> Master target 8000, master SL 5000. Master trail SL: every 3000 profit trail master SL by 1500, max 4 times. Sqroff 2 days before expiry.
>
> Short description: 'ISE max param BNF strategy.' Long description: 'Full-parameter ISE strategy with SuperTrend+MACross AND RSI OR MACD, Heikin-Ashi 30min, positional NRML, master trail SL.'"

**Expected Output Validation:**
- Main: isIntraday=false, entryOrderProduct=NRML, exitOrderProduct=NRML
- Main: chartType=Heikin-Ashi, timeFrame=30Min, signal=Both, underlyingType=Spot/Index
- Main: entryTime=09:20, sqroffTime=15:15
- weekDays: contains MON, TUE, WED — does NOT contain THU or FRI
- sqroffBeforeExDays=2
- masterTarget=8000, masterSl=5000
- isTrailSl=true (master), profitMove=3000, slMove=1500, noOfTrailSl=4
- Sub Leg 1: optionType=CE, atm=0, lot=2, sl=3000, isReverseSignal=false, isTrailSl=true, trailSlMarketMove=1500, trailSlMove=600, noOfTimeTrailSl=4
- Sub Leg 2: optionType=PE, atm=0, lot=2, sl=3000, isReverseSignal=true
- Sub Leg 3: optionType=CE, atm=200, lot=1, isReverseSignal=false, segment=OPT
- Sub Leg 4: segment=FUT, optionType="", lot=1, isReverseSignal=false
- sub_count=4
- Indicator 1: index=1, indicator_code=supertrend, length=10, factor=3
- Indicator 2: index=1, indicator_code=ma-cross-over, short=9, long=26, type=SMA (AND with supertrend)
- Indicator 3: index=2, indicator_code=rsi (OR)
- Indicator 4: index=3, indicator_code=macd (OR)
- indicator_count=4
- shortDescription contains "ISE" or "BNF" or "max"
- longDescription contains "SuperTrend" or "Heikin"

---

## TEST COVERAGE MATRIX

| # | Parameter Category | Prompts Covering It |
|---|---|---|
| 1 | Strategy Name | All |
| 2 | isIntraday (Intraday) | 1,2,3,4,5,6,7,8,9,10,12,13,14,15,16,17,19 |
| 3 | isIntraday (Positional) | 11, 18, 20 |
| 4 | entryOrderProduct / exitOrderProduct MIS | 1–10, 12–17, 19 |
| 5 | entryOrderProduct / exitOrderProduct NRML | 11, 18, 20 |
| 6 | chartType=Candlestick | 1–9, 11–17, 19 |
| 7 | chartType=Heikin-Ashi | 10, 20 |
| 8 | timeFrame=5Min | 1, 3, 4, 6, 7, 8, 9, 12, 14, 15, 16, 17, 19 |
| 9 | timeFrame=10Min | 4 |
| 10 | timeFrame=15Min | 2, 14 |
| 11 | timeFrame=30Min | 5, 20 |
| 12 | timeFrame=1Hour | 6 |
| 13 | timeFrame=2Hour | 10 |
| 14 | timeFrame=4Hour | 18 |
| 15 | timeFrame=1Day | 11 |
| 16 | signal=Both | 1, 2, 5, 7, 8, 9, 10, 11, 13, 18, 20 |
| 17 | signal=BUY | 3, 15, 19 |
| 18 | signal=SELL | 4, 14 |
| 19 | entryTime (custom) | 2,3,4,5,6,7,8,9,10,12,14,17,19,20 |
| 20 | sqroffTime (custom) | 2, 17 |
| 21 | weekDays (default Mon-Fri) | 1,2,3,4,7,8,9,11,12,13,14,15,16 |
| 22 | weekDays (restricted) | 10, 17, 20 |
| 23 | underlyingType=Future | 1, 2, 10, 11 |
| 24 | underlyingType=Spot/Index | 14, 20 |
| 25 | exchange=NFO | 1,2,3,5,6,7,8,9,13,14,15,16,17,18,19,20 |
| 26 | exchange=BFO (SENSEX) | 12 |
| 27 | segment=FUT | 1, 3, 6, 8, 11, 13, 14, 16 |
| 28 | segment=OPT | 2,4,5,7,9,10,12,13,15,17,18,19,20 |
| 29 | contract=NEAR | 1,2,3,5,6,7,8,9,11,12,13,14,15,16,17,19,20 |
| 30 | contract=NEXT | 13, 18 |
| 31 | expiry=MONTHLY | 1, 5, 8, 11, 13 |
| 32 | expiry=WEEKLY | 2,3,4,6,7,9,10,12,13,14,15,16,17,18,19,20 |
| 33 | atm=0 (ATM strike) | 1,2,3,5,6,7,8,9,10,12,13,14,15,16,17,19,20 |
| 34 | atm positive (CE OTM offset) | 4, 12, 13, 17 |
| 35 | atm negative (PE OTM offset) | 4, 12, 17, 20 |
| 36 | optionType=CE | 2,4,7,9,12,13,15,17,19,20 |
| 37 | optionType=PE | 2,4,7,12,13,15,17,18,20 |
| 38 | optionType="" (FUT/Stock) | 1,3,6,8,11,13,14,16 |
| 39 | lot=1 (single lot) | 1,2,3,6,7,8,9,11,12,13,14,15,16,18,19 |
| 40 | lot>1 (multiple lots) | 2, 13, 17, 20 |
| 41 | qty validation (lot × lot_size) | All |
| 42 | callType=BUY (always) | All |
| 43 | target=0 (no target) | 1,6,7,8,9,12,14,16 |
| 44 | target>0 + targetBy=Money | 4, 7, 17 |
| 45 | sl=0 (no SL) | 1,6,7,9,11,13,14 |
| 46 | sl>0 + slBy=Money | 3,4,8,12,17,20 |
| 47 | isTrailSl=false (leg) | 1,2,3,4,5,7,8,9,10,11,12,14,15,18,19 |
| 48 | isTrailSl=true (leg) | 6, 16, 17, 20 |
| 49 | trailSlMarketMove + trailSlMove + noOfTimeTrailSl | 6, 17, 20 |
| 50 | noOfTimeTrailSl=0 (unlimited) | 16 |
| 51 | isReverseSignal=false | 1,2,3,4,5,6,8,9,10,11,13,14,16,17 |
| 52 | isReverseSignal=true | 2,7,12,13,15,17,18,19,20 |
| 53 | masterTarget=0 (disabled) | 3, 12, 16 |
| 54 | masterTarget>0 | 7, 8, 17, 20 |
| 55 | masterSl=0 (disabled) | 1, 7, 11 |
| 56 | masterSl>0 | 3, 8, 12, 16, 20 |
| 57 | isTrailSl=false (master) | 1,2,3,4,5,6,7,9,10,11,12,13,14,15,16,17,18,19 |
| 58 | isTrailSl=true (master) | 8, 20 |
| 59 | profitMove + slMove + noOfTrailSl | 8, 20 |
| 60 | sqroffBeforeExDays=0 | 1–10, 12–17, 19 |
| 61 | sqroffBeforeExDays>0 | 11, 18, 20 |
| 62 | shortDescription | 19, 20 |
| 63 | longDescription | 19, 20 |
| 64 | Indicator: supertrend (default) | 1, 7, 10 |
| 65 | Indicator: supertrend (custom) | 9, 14, 20 |
| 66 | Indicator: ma-cross-over (default) | 11, 20 |
| 67 | Indicator: ma-cross-over (custom) | 2, 9 |
| 68 | Indicator: rsi (default) | 13, 16 |
| 69 | Indicator: rsi (custom bands) | 3, 6, 9 |
| 70 | Indicator: macd (custom) | 4 |
| 71 | Indicator: macd (default) | 16, 20 |
| 72 | Indicator: stochastic (custom) | 5, 18 |
| 73 | Indicator: bollinger-bands (custom) | 5 |
| 74 | Indicator: hammer (candlestick) | 15, 19 |
| 75 | Indicator: evening-star (candlestick) | 15 |
| 76 | Indicator: three-white-soldiers (candlestick) | 19 |
| 77 | Indicator: morning-star (candlestick) | 19 |
| 78 | AND logic (same index) | 5, 9, 19, 20 |
| 79 | OR logic (different index) | 6, 9, 15, 19, 20 |
| 80 | Mixed AND+OR | 9, 19, 20 |
| 81 | 1 indicator | 1,2,3,4,6,7,8,10,11,12,14,16,17 |
| 82 | 2 indicators | 5, 13, 15, 18 |
| 83 | 3 indicators | 9, 19 |
| 84 | 4 indicators | 20 |
| 85 | 1 leg | 3, 4, 6, 8, 11, 14, 16 |
| 86 | 2 legs | 1,2,5,7,9,10,12,15,17,18,19 |
| 87 | 3 legs | 13 |
| 88 | 4 legs | 17, 20 |
