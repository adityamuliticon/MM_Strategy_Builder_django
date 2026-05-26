# Unified Strategy Builder – Chatbot Test Prompts
### 20 Comprehensive Prompts to Validate Strategy Generation

---

## PROMPT 1 — Basic Straddle (Core Basics)
**Tests:** Strategy Name, Underlying (Exchange/Segment/Symbol), Trading Type, Start Time, Sqroff Time, 2-leg ATM CE+PE, Master Target, Master SL

> "Create a BankNifty intraday straddle. Sell ATM CE and ATM PE at 9:20 with exit at 15:15. Set master target 2500 and master stoploss 1500. Use 1 lot per leg, weekly expiry."

**Expected Output Validation:**
- Main: Exchange=NFO, Segment=FUT, Symbol=BANKNIFTY, Trading Type=Intraday, Product=MIS, Start Time=09:20:00, Sqroff Time=15:15:00
- Leg 1: SELL, OPT, CE, ATM 0, Current Week, 1 lot, Idle=False
- Leg 2: SELL, OPT, PE, ATM 0, Current Week, 1 lot, Idle=False
- Advance: Master Target By=Combined Profit, Master Target Value=2500, Master SL By=Combined Loss, Master SL Value=1500

---

## PROMPT 2 — Strangle with ATM Offset + Leg-Level TP/SL
**Tests:** ATM Value offset strikes, individual leg Target By (Point), individual leg SL By (Point), different OTM offsets for CE vs PE

> "Build a Nifty strangle for current week. Sell CE at ATM+200 and Sell PE at ATM-200. Set per-leg target at 30 points and per-leg stoploss at 50 points. Start at 9:16, sqroff at 15:10. 2 lots each."

**Expected Output Validation:**
- Main: Symbol=NIFTY, Start Time=09:16:00, Sqroff Time=15:10:00
- Leg 1: SELL CE, Strike by ATM Value, ATM +200, 2 lots, Target By=Target by Point, Target Value=30, SL By=SL by Point, SL Value=50
- Leg 2: SELL PE, Strike by ATM Value, ATM -200, 2 lots, Target By=Target by Point, Target Value=30, SL By=SL by Point, SL Value=50
- No Master Target/SL (both 0)

---

## PROMPT 3 — Iron Condor (4 Legs + Hedging)
**Tests:** 4-leg structure, mixed BUY/SELL, different ATM offsets per leg, master-level target only, auto-hedge validation

> "Create an iron condor on BankNifty weekly. Sell CE ATM+300, Sell PE ATM-300, Buy CE ATM+500, Buy PE ATM-500. 1 lot each leg. Master target 3000, no stoploss. Intraday, start 9:20."

**Expected Output Validation:**
- 4 legs all OPT, Current Week, 1 lot each
- Leg 1: SELL CE ATM+300
- Leg 2: SELL PE ATM-300
- Leg 3: BUY CE ATM+500
- Leg 4: BUY PE ATM-500
- Master Target Value=3000, Master SL Value=0

---

## PROMPT 4 — Premium Range Strike Selection + Combined Premium Entry
**Tests:** Strike by Premium Range, Start Range, End Range, Direction (OTM), Combined Premium Entry, Total Premium

> "Sell BankNifty CE where premium is between 100 and 150, OTM only. Also sell PE in premium range 100 to 150 OTM. Enter only when combined premium of both legs reaches 220. Weekly expiry, intraday, 1 lot each. Master target 2000."

**Expected Output Validation:**
- Leg 1: SELL CE, Strike by Premium Range, Start Range=100, End Range=150, Direction=OTM
- Leg 2: SELL PE, Strike by Premium Range, Start Range=100, End Range=150, Direction=OTM
- Main: Combined Premium Entry=True, Total Premium=220
- Advance: Master Target Value=2000

---

## PROMPT 5 — Delta-Based Strike Selection
**Tests:** Strike by Nearest Delta, Condition (AboveEqual/BelowEqual), Direction (OTM), mixed with ATM for hedge leg

> "Create a Nifty strategy: Sell PE nearest delta 0.3, condition above-equal, OTM direction. Buy PE at ATM-500 as hedge. Current week expiry, 1 lot, intraday. Master SL 2000, no target."

**Expected Output Validation:**
- Leg 1: SELL PE, Strike by Nearest Delta, Value=0.3, Condition=AboveEqual (>=), Direction=OTM
- Leg 2: BUY PE, Strike by ATM Value, ATM -500
- Master SL Value=2000, Master Target Value=0

---

## PROMPT 6 — Profit Locking & Trailing (Master Level)
**Tests:** Master Profit Locking (If Profit Reaches, Lock Min, Increase By, Trail By, No of Time Trail), Master SL Trailing

> "BankNifty straddle, sell ATM CE and PE, 1 lot, weekly, intraday, start 9:20. Master target 5000. When overall profit reaches 3000, lock minimum profit at 1500. Then for every 500 increase, trail profit by 300, max 5 times. Also trail master SL: for every 1000 profit increase trail SL by 500, max 3 times. Master SL 2000."

**Expected Output Validation:**
- Master Profit Locking: If Profit Reaches=3000, Lock Min=1500, Increase By=500, Trail By=300, No of Time Trail=5
- Master SL Trailing: Increase Profit By=1000, Trail SL By=500, No of Time Trail=3
- Master Target=5000, Master SL=2000

---

## PROMPT 7 — Leg-Level Profit Locking + SL Trailing
**Tests:** Per-leg profit locking fields, per-leg SL trailing fields, different settings per leg

> "Nifty weekly strangle intraday. Sell CE ATM+100, Sell PE ATM-100, 1 lot each.
> For CE leg: if profit reaches 2000, lock 1000, trail by 200 for every 400 increase, max 4 trails. SL trail: for every 800 profit, trail SL by 300, unlimited times.
> For PE leg: if profit reaches 1500, lock 800, trail by 150 for every 300 increase, max 3 trails. No SL trailing."

**Expected Output Validation:**
- Leg 1 (CE): Profit Lock fields populated differently from Leg 2
- Leg 1 SL Trail: Increase=800, Trail=300, Times=0 (unlimited)
- Leg 2 (PE): Profit Lock fields with different values
- Leg 2 SL Trail: all zeros (disabled)

---

## PROMPT 8 — Idle Legs + Action on Target/SL Chaining
**Tests:** Idle leg, Action on Target (Execute Leg), Action on SL (Execute Leg), Leg No reference, Delay

> "BankNifty intraday weekly. Leg 1: Sell ATM CE, 1 lot, target 40 points, SL 60 points. Leg 2: idle, Sell ATM PE, 1 lot. Leg 3: idle, Buy CE ATM+500, 1 lot.
> When Leg 1 hits target, execute Leg 2 after 5 second delay. When Leg 1 hits SL, execute Leg 3 after 3 second delay."

**Expected Output Validation:**
- Leg 1: Idle=False, Target By=Point, Value=40, SL By=Point, Value=60
  - Action on Target=Execute Leg, Leg No=2, Delay=5
  - Action on SL=Execute Leg, Leg No=3, Delay=3
- Leg 2: Idle=True
- Leg 3: Idle=True

---

## PROMPT 9 — Action on Target: Reenter + Sqroff Leg
**Tests:** Reenter Leg action, Sqroff Leg action, mixed action types across legs

> "Nifty weekly intraday. Leg 1: Sell CE ATM, target 50 points, SL 70 points. Leg 2: Sell PE ATM, target 50 points, SL 70 points. Leg 3: idle, Buy CE ATM+400.
> When Leg 1 hits target → reenter Leg 1 with 10 sec delay. When Leg 2 hits SL → sqroff Leg 1 with 2 sec delay. When Leg 2 hits target → execute Leg 3."

**Expected Output Validation:**
- Leg 1: Action on Target=Reenter Leg, Leg No=1, Delay=10
- Leg 2: Action on SL=Sqroff Leg, Leg No=1, Delay=2; Action on Target=Execute Leg, Leg No=3, Delay=0
- Leg 3: Idle=True

---

## PROMPT 10 — Range Breakout + Wait & Trade
**Tests:** Range Breakout (Main), Range End Time, Execute on Range Breakout (Leg), Wait & Trade (direction, value)

> "BankNifty intraday. Enable range breakout, range end time 9:30. Leg 1: Sell CE ATM, execute on range breakout. Leg 2: Sell PE ATM, use wait and trade — enter after underlying moves down 0.5%. Weekly, 1 lot each. Master target 2000, master SL 1500."

**Expected Output Validation:**
- Main: Range Breakout=True, Range End Time=09:30:00
- Leg 1: Execute on Range Breakout=True, Wait & Trade=False
- Leg 2: Wait & Trade=True, Direction=Down %, Value=0.5, Execute on Range Breakout=False
- Master Target=2000, Master SL=1500

---

## PROMPT 11 — Positional + BTST/STBT + Pre-Expiry Sqroff
**Tests:** Trading Type=Positional, Product=NRML, BTST/STBT=True, Gap Days, Sqroff Before Expiry, No of Days, Sqroff Time

> "Create a positional BankNifty strategy with NRML product. Sell CE ATM and PE ATM, monthly expiry, 1 lot. Enable BTST with 2 gap days. Square off positions 1 day before expiry at 15:10. Master target 8000, master SL 5000."

**Expected Output Validation:**
- Main: Trading Type=Positional, Product=NRML, BTST/STBT=True, Gap Days=2
- Legs: Expiry=Current Month
- Advance: Sqroff Before Expiry=True, No of Days=1, Sqroff Time=15:10:00
- Master Target=8000, Master SL=5000

---

## PROMPT 12 — VIX Filter + Working Days
**Tests:** VIX Filter=True, VIX Start Range, VIX End Range, Working Days (specific days only)

> "Nifty weekly straddle, sell ATM CE+PE, intraday, 1 lot. Only trade on Monday, Wednesday and Friday. Enable VIX filter: trade only when VIX is between 12 and 20. Master target 1500, no SL. Start 9:20."

**Expected Output Validation:**
- Advance: VIX Filter=True, VIX Start=12, VIX End=20
- Working Days: MON=True, TUE=False, WED=True, THU=False, FRI=True, SAT=False
- Master Target=1500, Master SL=0

---

## PROMPT 13 — Master Reexecution (Target + SL) with Delays
**Tests:** Action on Master Target=Reexecute, No of Times Reexecute (target), Delay (target), Action on Master SL=Reexecute, No of Times Reexecute (SL), Delay (SL)

> "BankNifty straddle sell ATM CE PE weekly intraday 1 lot. Master target 2000, on target hit reexecute max 3 times with 15 second delay. Master SL 1200, on SL hit reexecute max 2 times with 20 second delay. Start 9:20."

**Expected Output Validation:**
- Action on Master Target=Reexecute, No of Times=3, Delay=15
- Action on Master SL=Reexecute, No of Times=2, Delay=20

---

## PROMPT 14 — Safety Switches (All 3) + Paused TP/SL
**Tests:** Sqroff all legs on any TP/SL, Sqroff on rejection, Enable TP/SL on paused strategy, Required Margin

> "BankNifty iron condor weekly intraday. Sell CE ATM+200, Sell PE ATM-200, Buy CE ATM+400, Buy PE ATM-400. 1 lot each. Enable: square off all legs if any single leg hits TP/SL, square off on order rejection, and keep TP/SL monitoring even when strategy is paused. Set required margin 125000. Master target 2500."

**Expected Output Validation:**
- Advance: Sqroff all legs=True, Sqroff on rejection=True, TP/SL on paused=True
- Required Margin=125000

---

## PROMPT 15 — Theta-Based Strike + Target by Percentage
**Tests:** Strike by Theta Range, Strike by Nearest Theta, Target by Point (%), SL by Point (%)

> "Sell BankNifty CE weekly where theta is between 5 and 15, OTM direction. Sell PE nearest theta 10, condition below-equal, OTM. Set leg target at 40% of entry price and leg SL at 60% of entry price. 1 lot each, intraday, start 9:25."

**Expected Output Validation:**
- Leg 1: Strike by Theta Range, Start=5, End=15, Direction=OTM
- Leg 2: Strike by Nearest Theta, Value=10, Condition=BelowEqual (<=), Direction=OTM
- Both legs: Target By=Target by Point (%), Value=40; SL By=SL by Point (%), Value=60

---

## PROMPT 16 — ATM% Strike + Delta-Based TP/SL + FUT Leg
**Tests:** Strike by ATM %, Target by Delta, SL by Theta, Segment=FUT mixed with OPT

> "Nifty strategy: Leg 1 — Sell CE at ATM% 0.50 OTM weekly, target by delta 0.2, SL by theta 8. Leg 2 — Buy 1 lot Nifty Futures current month as hedge. Intraday, 1 lot each. Master target 3000."

**Expected Output Validation:**
- Leg 1: OPT, CE, Strike by ATM %, ATM% 0.50, Target By=Target by Delta, Value=0.2, SL By=SL by Theta, Value=8
- Leg 2: Segment=FUT, Expiry=Current Month, BUY, 1 lot (no Option Type, no Strike Selection)
- Master Target=3000

---

## PROMPT 17 — Ratio Spread (Different Lots per Leg)
**Tests:** Different lot quantities across legs, ratio structure, combined with master trailing

> "BankNifty ratio spread weekly intraday: Sell 2 lots ATM CE, Buy 1 lot CE ATM+300 as hedge. Sell 2 lots ATM PE, Buy 1 lot PE ATM-300 as hedge. Master target 4000, master SL 2500. Trail master SL: increase profit by 1500 trail SL by 700, max 4 times. Start 9:20."

**Expected Output Validation:**
- Leg 1: SELL CE ATM 0, 2 lots
- Leg 2: BUY CE ATM+300, 1 lot
- Leg 3: SELL PE ATM 0, 2 lots
- Leg 4: BUY PE ATM-300, 1 lot
- Master SL Trailing: Increase=1500, Trail=700, Times=4

---

## PROMPT 18 — Multi-Expiry Calendar Spread + Nearest Premium
**Tests:** Different expiry per leg (Current Week vs Month 1), Strike by Nearest Premium, Condition=Any, Direction=BOTH

> "Nifty calendar spread. Sell CE nearest premium 200 current week expiry, direction BOTH, condition any. Buy CE nearest premium 200 next month expiry, direction BOTH, condition any. 1 lot each, intraday, no master target or SL."

**Expected Output Validation:**
- Leg 1: SELL CE, Strike by Nearest Premium, Value=200, Direction=BOTH, Condition=Any, Expiry=Current Week
- Leg 2: BUY CE, Strike by Nearest Premium, Value=200, Direction=BOTH, Condition=Any, Expiry=Month 1
- Master Target=0, Master SL=0

---

## PROMPT 19 — Combined Premium (Master Target By) + Wait & Trade Points + BFO Exchange
**Tests:** Master Target By=Combined Premium, different exchange (BFO), Wait & Trade with Up pts, Sqroff Time override

> "Create strategy on BSE exchange (BFO), SENSEX symbol, weekly expiry. Sell CE ATM and PE ATM, 1 lot each. Leg 1 should wait for underlying to move up 100 points before entering. Master target by combined premium, target value 150. Master SL by combined loss, SL value 3000. Intraday, start 9:20, sqroff 15:00."

**Expected Output Validation:**
- Main: Exchange=BFO, Symbol=SENSEX, Sqroff Time=15:00:00
- Leg 1: Wait & Trade=True, Direction=Up pts, Value=100
- Advance: Master Target By=Combined Premium, Master Target Value=150
- Master SL By=Combined Loss, Master SL Value=3000

---

## PROMPT 20 — Maximum Complexity (Everything Together)
**Tests:** ALL major parameters in one prompt — 4 legs, idle, actions, range breakout, VIX, working days, profit locking (leg+master), SL trailing (leg+master), reexecution, pre-expiry, BTST, combined premium entry, descriptions

> "Create a positional BankNifty strategy called 'Full Hedge Machine' on NFO, NRML product, monthly expiry.
>
> Leg 1: Sell CE at premium range 120–180, OTM, 2 lots. Target 50 points, SL 80 points. Profit locking: if reaches 3000 lock 1500, trail by 200 every 500 increase, max 4 times. SL trailing: increase 1000 trail SL by 400, 3 times. On target → execute Leg 3 after 5 sec. On SL → sqroff Leg 2 after 2 sec.
>
> Leg 2: Sell PE at nearest delta 0.25, above-equal, OTM, 2 lots. Target 50 points, SL 80 points.
>
> Leg 3: idle, Buy CE ATM+500, 1 lot. No TP/SL.
>
> Leg 4: idle, Buy PE ATM-500, 1 lot. No TP/SL.
>
> Entry only when combined premium reaches 280. Enable range breakout with range end time 9:25. Enable VIX filter 11 to 19. Trade only Mon, Tue, Wed, Thu. Start 9:20.
>
> Master target 6000 (combined profit), reexecute 2 times with 10 sec delay. Master SL 4000, reexecute 1 time with 15 sec delay. Master profit locking: if reaches 4000 lock 2000, trail 300 every 600, max 5. Master SL trailing: increase 2000 trail SL 800, max 3.
>
> Enable BTST 3 gap days. Pre-expiry sqroff 2 days before at 15:00. Enable sqroff all legs on any TP/SL. Enable sqroff on rejection. Enable TP/SL monitoring on pause. Required margin 200000.
>
> Short description: 'Full hedge positional BNF with premium + VIX control.' Detailed description: 'Multi-leg positional BankNifty hedge using premium range + delta strikes, idle leg execution chaining, master MTM control with profit locking and SL trailing, VIX and day filtering, pre-expiry exit.'"

**Expected Output Validation:**
- ALL Main tab fields populated (Strategy Name, Exchange=NFO, Segment=FUT, Symbol=BANKNIFTY, Positional, NRML, Start=09:20, Range Breakout=True, Range End=09:25, BTST=True, Gap Days=3, Combined Premium Entry=True, Total Premium=280)
- 4 legs with correct Idle flags, strike methods, lots, TP/SL, profit locking, SL trailing, actions, leg references, delays
- ALL Advance tab fields (Master Target+SL, both profit locking groups, both SL trailing groups, reexecution counts+delays, VIX filter, working days, pre-expiry, safety switches, margin)
- Description tab populated with both short and detailed text

---

## TEST COVERAGE MATRIX

| # | Parameter Category | Prompts Covering It |
|---|---|---|
| 1 | Strategy Name | 20 |
| 2 | Exchange / Segment / Symbol | 1, 2, 5, 16, 19, 20 |
| 3 | Trading Type (Intraday/Positional) | 1, 11, 20 |
| 4 | Product (MIS/NRML) | 11, 20 |
| 5 | Start Time / Sqroff Time | 1, 2, 15, 19, 20 |
| 6 | Range Breakout + Range End Time | 10, 20 |
| 7 | BTST/STBT + Gap Days | 11, 20 |
| 8 | Combined Premium Entry + Total Premium | 4, 20 |
| 9 | Idle Legs | 8, 9, 20 |
| 10 | Trade Side (BUY/SELL mix) | 3, 5, 16, 17, 20 |
| 11 | Lots (different per leg) | 17, 20 |
| 12 | Segment (OPT/FUT/Stock mix) | 16 |
| 13 | Expiry (Week/Month/multi) | 2, 11, 18, 20 |
| 14 | Option Type (CE/PE) | All |
| 15 | Strike by ATM Value | 1, 2, 3, 8, 9, 12, 13, 17 |
| 16 | Strike by ATM % | 16 |
| 17 | Strike by Premium Range | 4, 20 |
| 18 | Strike by Nearest Premium | 18 |
| 19 | Strike by Delta Range / Nearest Delta | 5, 20 |
| 20 | Strike by Theta Range / Nearest Theta | 15 |
| 21 | Direction (ITM/OTM/BOTH) | 4, 5, 15, 18, 20 |
| 22 | Condition (Any/AboveEqual/BelowEqual) | 5, 15, 18, 20 |
| 23 | Target By (Money/Point/Point%/Delta/Theta) | 2, 8, 15, 16 |
| 24 | SL By (Money/Point/Point%/Delta/Theta) | 2, 8, 15, 16 |
| 25 | Leg Profit Locking & Trailing | 7, 20 |
| 26 | Leg SL Trailing | 7, 20 |
| 27 | Action on Target (Execute/Reenter/Sqroff) | 8, 9, 20 |
| 28 | Action on SL (Execute/Reenter/Sqroff) | 8, 9, 20 |
| 29 | Leg No + Delay | 8, 9, 20 |
| 30 | Wait & Trade (direction + value) | 10, 19 |
| 31 | Execute on Range Breakout (leg) | 10 |
| 32 | Master Target By (Profit/Premium) | 1, 6, 19 |
| 33 | Master Target Value | 1, 3, 6, 12, 13, 17, 20 |
| 34 | Master SL By (Loss/Premium) | 1, 6, 19 |
| 35 | Master SL Value | 1, 6, 13, 17, 20 |
| 36 | Master Profit Locking & Trailing | 6, 20 |
| 37 | Master SL Trailing | 6, 17, 20 |
| 38 | Reexecution (Target) — count + delay | 13, 20 |
| 39 | Reexecution (SL) — count + delay | 13, 20 |
| 40 | Sqroff Before Expiry + Days + Time | 11, 20 |
| 41 | Working Days | 12, 20 |
| 42 | VIX Filter + Start/End Range | 12, 20 |
| 43 | TP/SL on Paused Strategy | 14, 20 |
| 44 | Sqroff All Legs on Any TP/SL | 14, 20 |
| 45 | Sqroff on Rejection | 14, 20 |
| 46 | Required Margin | 14, 20 |
| 47 | Short Description | 20 |
| 48 | Detailed Description | 20 |
| 49 | 4-leg structure (Iron Condor) | 3, 14, 17 |
| 50 | Multi-expiry (Calendar) | 18 |
