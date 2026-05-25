# Inbound Signal Bridge – Chatbot Test Prompts
### 20 Comprehensive Prompts to Validate ISB Strategy Generation

---

## PROMPT 1 — BankNifty FUT Intraday MIS Fix Qty (Core Basics)
**Tests:** strategy_name, is_intraday=True, product_type=MIS, Fix qty, lot=1, qty=30, BankNifty FUT, NFO, NEAR, MONTHLY, intraday_exit_time_min=15, run_mon–fri defaults, option_type=""

> "Create an intraday TradingView signal strategy for BankNifty futures. Use MIS product, 1 fixed lot, near contract monthly expiry on NFO. Exit 15 minutes before market close. Trade Monday to Friday only."

**Expected Output Validation:**
- strategy_name: non-empty string
- is_intraday: True
- product_type: "MIS"
- Sub Leg 1: exchange="NFO", segment="FUT", symbol="BANKNIFTY", contract="NEAR", expiry="MONTHLY", qty_distribution="Fix", lot=1, qty=30, option_type="", atm=0
- intraday_exit_time_min: 15
- run_mon: True, run_tue: True, run_wed: True, run_thu: True, run_fri: True, run_sat: False, run_sun: False
- is_trail_sl: False

---

## PROMPT 2 — Positional NRML with Leg Target and Leg SL (No Trail)
**Tests:** is_intraday=False, product_type=NRML, leg target>0, target_by="Money", leg sl>0, sl_by="Money", is_trail_sl=False, Nifty FUT MONTHLY

> "Create a positional NRML signal strategy for Nifty futures. Fixed 1 lot, near monthly. Set leg target 5000 rupees and leg stoploss 3000 rupees. No trail SL. Exit 15 minutes before close."

**Expected Output Validation:**
- is_intraday: False
- product_type: "NRML"
- Sub Leg 1: segment="FUT", symbol="NIFTY", qty_distribution="Fix", lot=1, qty=25, target=5000, target_by="Money", sl=3000, sl_by="Money", is_trail_sl=False
- intraday_exit_time_min: 15

---

## PROMPT 3 — Capital(%) Qty Distribution with Required Margin
**Tests:** qty_distribution="Capital(%)", qty stores percentage, lot=1, required_margin=500000, positional NRML, BankNifty FUT

> "Create a positional signal strategy for BankNifty futures on NFO. Capital is 5 lakh rupees. Use Capital(%) distribution, allocate 3% of capital per trade. Fixed near monthly contract. NRML product."

**Expected Output Validation:**
- required_margin: 500000
- product_type: "NRML"
- is_intraday: False
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Capital(%)", qty=3, lot=1

---

## PROMPT 4 — Capital Risk(%) Qty Distribution with SL Required
**Tests:** qty_distribution="Capital Risk(%)", qty stores risk percentage, lot=1, required_margin set, sl>0 required, BankNifty FUT

> "Create a signal strategy for BankNifty futures. Capital 10 lakh. Risk 2% of capital per trade. Use Capital Risk(%) distribution. Leg stoploss 1500 rupees. Positional NRML, near monthly NFO."

**Expected Output Validation:**
- required_margin: 1000000
- product_type: "NRML"
- is_intraday: False
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Capital Risk(%)", qty=2, lot=1, sl=1500, sl_by="Money"

---

## PROMPT 5 — Allocation Method 1 Qty Distribution
**Tests:** qty_distribution="Allocation Method 1", lot=1, Nifty OPT CE WEEKLY ATM, positional NRML

> "Create a positional NRML signal strategy for Nifty weekly CE ATM options. Use Allocation Method 1 for quantity distribution — equally split capital across all open positions. Near contract."

**Expected Output Validation:**
- is_intraday: False
- product_type: "NRML"
- Sub Leg 1: segment="OPT", symbol="NIFTY", option_type="CE", atm=0, expiry="WEEKLY", contract="NEAR", qty_distribution="Allocation Method 1", lot=1

---

## PROMPT 6 — OPT Segment CE+PE Legs, ATM Offsets, Weekly Expiry
**Tests:** 2 OPT legs, option_type CE and PE, atm positive for CE, atm negative for PE, expiry=WEEKLY, Fix qty, NFO

> "Create an intraday MIS signal strategy with two Nifty option legs on NFO. Leg 1: CE 100 points OTM weekly near 1 lot. Leg 2: PE 100 points OTM weekly near 1 lot. Exit 15 minutes before close."

**Expected Output Validation:**
- is_intraday: True
- product_type: "MIS"
- Sub Leg 1: segment="OPT", symbol="NIFTY", option_type="CE", atm=1, expiry="WEEKLY", contract="NEAR", qty_distribution="Fix", lot=1
- Sub Leg 2: segment="OPT", symbol="NIFTY", option_type="PE", atm=-1, expiry="WEEKLY", contract="NEAR", qty_distribution="Fix", lot=1
- sub_count: 2

---

## PROMPT 7 — Stock Segment, NSE Exchange, CNC Product
**Tests:** segment="Stock", exchange="NSE", product_type="CNC", symbol=stock, option_type="", qty_distribution="Fix", lot=1, qty=1 (lot×1)

> "Create a signal strategy to trade Reliance stock on NSE. Use CNC product for delivery. Fixed 5 shares (5 lots) per signal. Positional. Exit 15 minutes before close."

**Expected Output Validation:**
- product_type: "CNC"
- is_intraday: False
- Sub Leg 1: exchange="NSE", segment="Stock", symbol="RELIANCE", qty_distribution="Fix", lot=5, qty=5, option_type="", atm=0

---

## PROMPT 8 — Fixed Strike Price (Non-Zero strike_price)
**Tests:** strike_price>0 (non-zero fixed strike), OPT segment, CE, WEEKLY, NFO, BankNifty, Fix qty

> "Create a positional NRML signal strategy for BankNifty weekly CE options on NFO. Use a fixed strike price of 52000 instead of ATM-relative selection. 1 lot near contract. Exit 15 min before close."

**Expected Output Validation:**
- is_intraday: False
- product_type: "NRML"
- Sub Leg 1: segment="OPT", symbol="BANKNIFTY", option_type="CE", expiry="WEEKLY", contract="NEAR", strike_price=52000, qty_distribution="Fix", lot=1

---

## PROMPT 9 — Leg Trail SL with Max Times (no_of_time_trail_sl=3)
**Tests:** is_trail_sl=True, trail_sl_market_move>0, trail_sl_move>0, no_of_time_trail_sl=3, Nifty FUT, Fix qty

> "Create a positional NRML signal strategy for Nifty futures, 1 lot near monthly NFO. Enable trail SL on the leg: after every 1000 rupees profit increase, trail the SL by 500 rupees. Maximum 3 trail steps."

**Expected Output Validation:**
- is_intraday: False
- Sub Leg 1: segment="FUT", symbol="NIFTY", qty_distribution="Fix", lot=1, qty=25, is_trail_sl=True, trail_sl_market_move=1000, trail_sl_move=500, no_of_time_trail_sl=3

---

## PROMPT 10 — Leg Trail SL Unlimited (no_of_time_trail_sl=0)
**Tests:** is_trail_sl=True, trail_sl_market_move>0, trail_sl_move>0, no_of_time_trail_sl=0 (unlimited), BankNifty FUT intraday

> "Create an intraday MIS signal strategy for BankNifty futures on NFO, 1 lot near monthly. Enable leg trail SL: trail after every 500 rupees profit move, trail SL by 250 rupees. Allow unlimited trail steps."

**Expected Output Validation:**
- is_intraday: True
- product_type: "MIS"
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Fix", lot=1, qty=30, is_trail_sl=True, trail_sl_market_move=500, trail_sl_move=250, no_of_time_trail_sl=0

---

## PROMPT 11 — Master Target + Master SL with 2 Legs
**Tests:** intraday_target>0, intraday_sl>0, target_by="Money", sl_by="Money", 2 sub legs, BankNifty FUT + NIFTY OPT CE, NRML positional

> "Create a positional NRML signal strategy. Leg 1: BankNifty futures 1 lot near monthly NFO. Leg 2: Nifty CE ATM weekly near 1 lot NFO. Set master target 8000 rupees and master stoploss 5000 rupees for combined portfolio."

**Expected Output Validation:**
- is_intraday: False
- product_type: "NRML"
- intraday_target: 8000
- target_by: "Money"
- intraday_sl: 5000
- sl_by: "Money"
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Fix", lot=1, qty=30
- Sub Leg 2: segment="OPT", symbol="NIFTY", option_type="CE", atm=0, expiry="WEEKLY"
- sub_count: 2

---

## PROMPT 12 — Working Days Mon-Wed-Fri Only
**Tests:** run_mon=True, run_tue=False, run_wed=True, run_thu=False, run_fri=True, run_sat=False, run_sun=False, BankNifty FUT intraday MIS

> "Create an intraday MIS signal strategy for BankNifty futures, 1 lot near monthly NFO. Trade only on Monday, Wednesday, and Friday — do not trade on Tuesday, Thursday, Saturday, or Sunday."

**Expected Output Validation:**
- is_intraday: True
- product_type: "MIS"
- run_mon: True
- run_tue: False
- run_wed: True
- run_thu: False
- run_fri: True
- run_sat: False
- run_sun: False
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Fix", lot=1, qty=30

---

## PROMPT 13 — Saturday Enabled (MCX Exchange, GOLD Futures)
**Tests:** exchange="MCX", symbol="GOLD", run_sat=True, run_sun=False, FUT segment, intraday MIS

> "Create an intraday MIS signal strategy for GOLD futures on MCX exchange. 1 lot fixed, near monthly contract. Trade Monday through Saturday — enable Saturday trading for MCX commodity market. Do not trade on Sunday."

**Expected Output Validation:**
- is_intraday: True
- product_type: "MIS"
- Sub Leg 1: exchange="MCX", segment="FUT", symbol="GOLD", contract="NEAR", expiry="MONTHLY", qty_distribution="Fix", lot=1
- run_mon: True
- run_tue: True
- run_wed: True
- run_thu: True
- run_fri: True
- run_sat: True
- run_sun: False

---

## PROMPT 14 — Exit Minutes Non-Default (30 Minutes Before Close)
**Tests:** intraday_exit_time_min=30 (non-default), is_intraday=True, MIS, BankNifty FUT, Fix qty

> "Create an intraday MIS signal strategy for BankNifty futures, 1 lot near monthly NFO. Exit 30 minutes before market close (not the default 15 minutes). Trade all weekdays."

**Expected Output Validation:**
- is_intraday: True
- product_type: "MIS"
- intraday_exit_time_min: 30
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Fix", lot=1, qty=30
- run_mon: True, run_fri: True

---

## PROMPT 15 — Auto Sqroff on Contract Expiry Disabled
**Tests:** auto_sqroff_on_contract_exp=False, positional NRML, Nifty FUT MONTHLY

> "Create a positional NRML signal strategy for Nifty futures, 1 lot near monthly NFO. Disable auto square-off on contract expiry — I want to manage expiry manually."

**Expected Output Validation:**
- is_intraday: False
- product_type: "NRML"
- auto_sqroff_on_contract_exp: False
- Sub Leg 1: segment="FUT", symbol="NIFTY", expiry="MONTHLY", qty_distribution="Fix", lot=1, qty=25

---

## PROMPT 16 — Sqroff All Legs + Sqroff on Rejection (Safety Features)
**Tests:** sqroffAllLegs=True, pause_and_sqroff_trading_on_margin_exeed=True, 2 legs, BankNifty FUT + BankNifty CE OPT, NRML

> "Create a positional NRML signal strategy. Leg 1: BankNifty futures 1 lot near monthly NFO. Leg 2: BankNifty CE ATM weekly near 1 lot NFO. Enable Sqroff All Legs — if any one leg exits on target or SL, close all other legs. Also enable Sqroff on Rejection — if any order is rejected by broker, close all open legs immediately."

**Expected Output Validation:**
- sqroffAllLegs: True
- pause_and_sqroff_trading_on_margin_exeed: True
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Fix", lot=1, qty=30
- Sub Leg 2: segment="OPT", symbol="BANKNIFTY", option_type="CE", atm=0, expiry="WEEKLY"
- sub_count: 2

---

## PROMPT 17 — Max Position + Max Capital Allocation Percent
**Tests:** max_position>0, max_position_allocation_percent<100, Capital Risk(%) qty distribution, required_margin set, multiple legs

> "Create a positional NRML signal strategy for portfolio execution. Capital 20 lakh. Use Capital Risk(%) distribution, risk 5% per stock. Leg 1: RELIANCE stock on NSE, SL 2000. Leg 2: INFY stock on NSE, SL 1500. Set max 5 simultaneous positions. Cap each symbol allocation at 20% of total capital."

**Expected Output Validation:**
- required_margin: 2000000
- is_intraday: False
- product_type: "NRML"
- max_position: 5
- max_position_allocation_percent: 20
- Sub Leg 1: exchange="NSE", segment="Stock", symbol="RELIANCE", qty_distribution="Capital Risk(%)", qty=5, lot=1, sl=2000
- Sub Leg 2: exchange="NSE", segment="Stock", symbol="INFY", qty_distribution="Capital Risk(%)", qty=5, lot=1, sl=1500
- sub_count: 2

---

## PROMPT 18 — 3-Leg Strategy: FUT + CE OPT + PE OPT Multi-Symbol
**Tests:** 3 sub legs, segment mix FUT+OPT+OPT, CE+PE, BankNifty FUT + Nifty CE + Nifty PE, different expiries, Fix qty, NRML positional

> "Create a positional NRML signal strategy with 3 legs. Leg 1: BankNifty futures 1 lot near monthly NFO. Leg 2: Nifty CE ATM weekly near 1 lot NFO. Leg 3: Nifty PE ATM weekly near 1 lot NFO. All legs execute on a single inbound signal."

**Expected Output Validation:**
- is_intraday: False
- product_type: "NRML"
- sub_count: 3
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", expiry="MONTHLY", qty_distribution="Fix", lot=1, qty=30, option_type=""
- Sub Leg 2: segment="OPT", symbol="NIFTY", option_type="CE", atm=0, expiry="WEEKLY", qty_distribution="Fix", lot=1
- Sub Leg 3: segment="OPT", symbol="NIFTY", option_type="PE", atm=0, expiry="WEEKLY", qty_distribution="Fix", lot=1

---

## PROMPT 19 — NEXT Contract + BFO Exchange SENSEX + Required Margin + Descriptions
**Tests:** contract="NEXT", exchange="BFO", symbol="SENSEX", required_margin>0, short_description, long_description, OPT CE WEEKLY, Fix qty

> "Create a positional NRML signal strategy for SENSEX options on BFO exchange. Leg 1: SENSEX CE ATM NEXT weekly 1 lot. Capital base is 3 lakh rupees. Short description: 'SENSEX BFO next-week CE signal bridge.' Long description: 'Receives TradingView alerts on SENSEX weekly CE options, NEXT contract on BFO exchange. Capital 3L, NRML positional. Exit 15 min before close.'"

**Expected Output Validation:**
- required_margin: 300000
- is_intraday: False
- product_type: "NRML"
- Sub Leg 1: exchange="BFO", segment="OPT", symbol="SENSEX", contract="NEXT", expiry="WEEKLY", option_type="CE", atm=0, qty_distribution="Fix", lot=1
- short_description: contains "SENSEX" or "BFO"
- long_description: contains "SENSEX" or "TradingView"

---

## PROMPT 20 — Maximum Complexity (ALL Parameters Together)
**Tests:** ALL parameters — positional NRML, required_margin, multi-leg 3+, Capital Risk(%), master target, master SL, trail SL on leg, sqroffAllLegs, pause_and_sqroff, max_position, max_position_allocation_percent, run days filter, intraday_exit_time_min non-default, auto_sqroff=False, margin settings, descriptions, strategy_type_id, is_intraday=False

> "Create a positional NRML signal strategy called 'ISB Full Param Test'. Capital 15 lakh.

Leg 1: BankNifty futures NFO, 1 lot fixed, near monthly. SL 4000 rupees. Trail SL: every 2000 rupees profit trail by 1000 rupees, max 5 trail steps.
Leg 2: Nifty CE ATM weekly near 1 lot NFO. Qty distribution Capital Risk(%), risk 3% of capital. SL 2500 rupees.
Leg 3: Nifty PE ATM weekly near 1 lot NFO. Qty distribution Capital Risk(%), risk 3% of capital. SL 2500 rupees.

Master target 10000 rupees. Master SL 6000 rupees. Max 8 simultaneous positions. Cap each symbol at 25% of capital. Enable Sqroff All Legs. Enable Sqroff on Rejection. Disable auto sqroff on contract expiry.

Trade only Monday, Tuesday, Wednesday, Thursday — disable Friday, Saturday, Sunday. Exit 20 minutes before market close.

Stock intraday margin 25%. Stock positional margin 80%. Future & Option margin 20%.

Short description: 'ISB max complexity test — 3 legs, Capital Risk(%), all safety features.' Long description: 'Full-parameter ISB strategy with BankNifty FUT Fix SL trail, Nifty CE+PE Capital Risk(%), master target/SL, all safety switches, restricted working days, non-default margins and exit time.'"

**Expected Output Validation:**
- strategy_name: non-empty (ideally contains "ISB" or "Full")
- is_intraday: False
- product_type: "NRML"
- required_margin: 1500000
- intraday_target: 10000
- target_by: "Money"
- intraday_sl: 6000
- sl_by: "Money"
- max_position: 8
- max_position_allocation_percent: 25
- sqroffAllLegs: True
- pause_and_sqroff_trading_on_margin_exeed: True
- auto_sqroff_on_contract_exp: False
- run_mon: True, run_tue: True, run_wed: True, run_thu: True
- run_fri: False, run_sat: False, run_sun: False
- intraday_exit_time_min: 20
- margin_stock_intraday: 25
- margin_stock_positional: 80
- margin_futopt_positional: 20
- sub_count: 3
- Sub Leg 1: segment="FUT", symbol="BANKNIFTY", qty_distribution="Fix", lot=1, qty=30, sl=4000, is_trail_sl=True, trail_sl_market_move=2000, trail_sl_move=1000, no_of_time_trail_sl=5
- Sub Leg 2: segment="OPT", symbol="NIFTY", option_type="CE", atm=0, expiry="WEEKLY", qty_distribution="Capital Risk(%)", qty=3, lot=1, sl=2500
- Sub Leg 3: segment="OPT", symbol="NIFTY", option_type="PE", atm=0, expiry="WEEKLY", qty_distribution="Capital Risk(%)", qty=3, lot=1, sl=2500
- strategy_type_id: "XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$"
- short_description: contains "ISB" or "legs" or "Capital Risk"
- long_description: contains "BankNifty" or "FUT" or "Capital Risk"

---

## TEST COVERAGE MATRIX

| # | Parameter Category | Prompts Covering It |
|---|---|---|
| 1 | strategy_name | All |
| 2 | is_intraday=True (Intraday) | 1, 6, 10, 12, 13, 14 |
| 3 | is_intraday=False (Positional) | 2, 3, 4, 5, 7, 8, 9, 11, 15, 16, 17, 18, 19, 20 |
| 4 | product_type=MIS | 1, 6, 10, 12, 13, 14 |
| 5 | product_type=NRML | 2, 3, 4, 5, 8, 9, 11, 15, 16, 17, 18, 19, 20 |
| 6 | product_type=CNC | 7 |
| 7 | required_margin=0 (default / live account) | 1, 2, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18 |
| 8 | required_margin>0 (capital base set) | 3, 4, 11, 17, 19, 20 |
| 9 | intraday_target>0 (master target) | 11, 20 |
| 10 | intraday_target=0 (disabled) | 1–10, 12–19 |
| 11 | intraday_sl>0 (master SL) | 11, 20 |
| 12 | intraday_sl=0 (disabled) | 1–10, 12–19 |
| 13 | target_by="Money" | 2, 11, 20 |
| 14 | sl_by="Money" | 2, 4, 9, 11, 17, 20 |
| 15 | max_position>0 | 17, 20 |
| 16 | max_position=0 (no limit) | 1–16, 18, 19 |
| 17 | max_position_allocation_percent<100 | 17, 20 |
| 18 | max_position_allocation_percent=100 (default) | 1–16, 18, 19 |
| 19 | exchange=NFO | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20 |
| 20 | exchange=NSE (Stock) | 7, 17 |
| 21 | exchange=MCX | 13 |
| 22 | exchange=BFO (SENSEX) | 19 |
| 23 | segment=FUT | 1, 2, 3, 4, 10, 11, 13, 14, 15, 18, 20 |
| 24 | segment=OPT | 5, 6, 8, 9, 11, 12, 16, 18, 19, 20 |
| 25 | segment=Stock | 7, 17 |
| 26 | contract=NEAR | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20 |
| 27 | contract=NEXT | 19 |
| 28 | expiry=MONTHLY | 1, 2, 3, 4, 10, 13, 14, 15, 18, 20 |
| 29 | expiry=WEEKLY | 5, 6, 8, 9, 11, 12, 16, 18, 19, 20 |
| 30 | atm=0 (ATM strike) | 5, 6, 9, 11, 12, 16, 18, 19, 20 |
| 31 | atm>0 (CE OTM / PE ITM offset) | 6 |
| 32 | atm<0 (CE ITM / PE OTM offset) | 6 |
| 33 | option_type=CE | 5, 6, 8, 9, 11, 12, 16, 18, 19, 20 |
| 34 | option_type=PE | 6, 12, 18, 20 |
| 35 | option_type="" (FUT/Stock) | 1, 2, 3, 4, 7, 10, 11, 13, 14, 15, 17, 18, 20 |
| 36 | strike_price=0 (use ATM) | 1–9, 11–20 |
| 37 | strike_price>0 (fixed strike) | 8 |
| 38 | qty_distribution=Fix | 1, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20 (leg 1) |
| 39 | qty_distribution=Capital(%) | 3 |
| 40 | qty_distribution=Capital Risk(%) | 4, 17, 20 (legs 2,3) |
| 41 | qty_distribution=Allocation Method 1 | 5 |
| 42 | lot=1 (Fix, single lot) | 1, 2, 8, 9, 10, 11, 13, 14, 15, 16, 18, 19, 20 |
| 43 | lot=5 (Fix, multiple lots) | 7 |
| 44 | qty=30 (BankNifty lot size ×1) | 1, 10, 12, 14, 16, 20 |
| 45 | qty=25 (Nifty lot size ×1) | 2, 9, 11, 15 |
| 46 | qty=5 (Stock lot size ×5) | 7 |
| 47 | qty=percentage value (Capital%) | 3, 4, 17, 20 |
| 48 | target=0 (no leg target) | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20 |
| 49 | target>0 (leg target) | 2 |
| 50 | sl=0 (no leg SL) | 1, 3, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 18, 19 |
| 51 | sl>0 (leg SL set) | 2, 4, 9, 10, 17, 20 |
| 52 | is_trail_sl=False | 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19 |
| 53 | is_trail_sl=True | 9, 10, 20 |
| 54 | trail_sl_market_move>0 | 9, 10, 20 |
| 55 | trail_sl_move>0 | 9, 10, 20 |
| 56 | no_of_time_trail_sl>0 (max times) | 9, 20 |
| 57 | no_of_time_trail_sl=0 (unlimited) | 10 |
| 58 | run_mon–fri=True (default working days) | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19 |
| 59 | run_sat=False (default) | 1–19 |
| 60 | run_sun=False (default) | 1–19 |
| 61 | run_sat=True (Saturday enabled) | 13 |
| 62 | run_tue=False / run_thu=False (restricted days) | 12 |
| 63 | run_fri=False (Friday disabled) | 20 |
| 64 | intraday_exit_time_min=15 (default) | 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 16, 17, 18, 19 |
| 65 | intraday_exit_time_min=30 (non-default) | 14 |
| 66 | intraday_exit_time_min=20 (non-default) | 20 |
| 67 | auto_sqroff_on_contract_exp=True (default) | 1–14, 16–19 |
| 68 | auto_sqroff_on_contract_exp=False | 15, 20 |
| 69 | margin_stock_intraday=30 (default) | 1–19 |
| 70 | margin_stock_intraday non-default | 20 |
| 71 | margin_stock_positional=100 (default) | 1–19 |
| 72 | margin_stock_positional non-default | 20 |
| 73 | margin_futopt_positional=30 (default) | 1–19 |
| 74 | margin_futopt_positional non-default | 20 |
| 75 | sqroffAllLegs=False (default) | 1–15, 17–19 |
| 76 | sqroffAllLegs=True | 16, 20 |
| 77 | pause_and_sqroff_trading_on_margin_exeed=False (default) | 1–15, 17–19 |
| 78 | pause_and_sqroff_trading_on_margin_exeed=True | 16, 20 |
| 79 | short_description set | 19, 20 |
| 80 | long_description set | 19, 20 |
| 81 | strategy_type_id check | 20 |
| 82 | 1 leg | 1, 2, 3, 4, 5, 7, 8, 9, 10, 13, 14, 15, 19 |
| 83 | 2 legs | 6, 11, 12, 16, 17 |
| 84 | 3 legs | 18, 20 |
| 85 | No indicators / No chartType / No timeFrame | All (ISB has no internal signal engine) |
