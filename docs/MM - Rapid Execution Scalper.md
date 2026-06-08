# Overview

**MM \- Rapid Execution Scalper**  
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date: 02-06-2026  
Prepared By: Paresh Bhatiya

# PLUGIN SUMMARY

# **✅ 1\. BRD VERSION (Formal, Precise, Functional Definition)**

## **Rapid Execution Scalper Plugin – Product Overview**

**Rapid Execution Scalper** is a high-frequency, step-based automated jobbing and averaging strategy engine designed for traders who want to systematically build positions at defined price intervals and close each step independently when its profit target is achieved. The plugin continuously monitors price movement and opens a new averaging position each time the market moves against the last open position by a configured **Average** distance — in Points or Percentage.

Unlike hedging or indicator-driven plugins, Rapid Execution Scalper is built around a **step-ladder model**: each step is opened at a fixed interval below (BUY) or above (SELL) the previous entry, and each step carries its own independent target. When price reaches a step's target, only that step is closed — all other open steps continue to run. This enables parallel profit-taking across multiple open positions while new averages continue to build.

The plugin supports both **Intraday and Positional** trading modes. In Intraday mode, all open positions are force-squared off at Jobbing End Time. In Positional mode, positions can be carried across sessions and rolled over automatically before contract expiry using the **Auto Rollover** feature.

Advanced controls include **dynamic quantity scaling** (increase or multiply quantity at each averaging step), **market gap handling** (Calculate Qty on Market Jump), **master-level target and stoploss** (Sqroff by Master TP SL with optional Trail SL), **step limits** (Maximum Avg. Steps, Maximum Target Steps), **cycle auto-reset** on positive MTM, and an optional **Add Hedge Leg** for attaching a secondary protective instrument that executes alongside the main strategy.

The plugin also supports **Opening Qty/Lot** to define a distinct quantity for the first entry step, separate from subsequent averaging steps.

---

## **Key Capabilities**

* Build averaging positions step-by-step at defined **Average** intervals (Points or %).
* Close each step **independently** when its per-step **Target** is reached.
* Configure **Jobbing Side** (BUY/SELL) to average down on BUY or average up on SELL.
* Define **Jobbing Start Price** and **Jobbing End Price** to control the price zone for entries.
* Limit depth with **Maximum Avg. Steps** and breadth with **Maximum Target Steps**.
* Scale position size dynamically using **Increase** or **Multiply** quantity logic.
* Handle overnight or session gap openings with **Calculate Qty on Market Jump**.
* Protect the entire strategy using **Sqroff by Master TP SL** (Master Target + Master SL in Money) with **Trail SL** on master-level profit.
* Auto-reset jobbing cycle when steps equal a configured count and MTM is positive (**Reset Cycle after Steps on Positive MTM**).
* Automatically transfer open positions to the next contract using **Auto Rollover** (Positional only).
* Attach a **Hedge Leg** instrument that executes in sync with the main strategy.
* Use **Templates** and **Import Template** for fast strategy replication.
* Supports all major exchanges: NSE, NFO, BFO, BSE, MCX, CDS.
* Supports Futures, Options, and Stock segments.

The plugin supports a wide range of use cases including:

* Intraday BUY/SELL jobbing on index futures
* Positional averaging with auto rollover on commodity futures
* Currency pair scalping on CDS
* Premium decay averaging on options
* Hedged averaging with secondary protective leg

---

## **Primary Objective**

To provide a **fully automated, price-interval-driven** position-building engine that opens averaging steps systematically, closes each step independently on target, and manages overall strategy risk through master TP/SL, step limits, and cycle controls — with complete flexibility for intraday and positional trading.

---

# **✅ 2\. COPILOT VERSION (AI-Optimized, Natural Language, Training Input)**

**Rapid Execution Scalper is a step-based automated averaging and jobbing plugin** that opens positions at a fixed Average interval and closes each step individually when its per-step Target is reached. It does not use indicators or external signals — entry is purely price-movement driven.

Copilot should understand that:

* The strategy opens a new position each time price moves against the last open position by the **Average** distance.
* Each step has its own independent target — when a step hits its target, only that step closes. Other steps remain open.
* The Average field **cannot be 0**. It must always be a positive number (Points or %).
* Master-level Target and SL (under "Sqroff by Master TP SL") control the entire strategy's combined MTM.
* Trail SL is a nested sub-feature inside "Sqroff by Master TP SL" — it trails the master stoploss as the combined profit grows.
* Auto Rollover works only in Positional mode — not in Intraday.
* The Hedge Leg has no independent TP/SL — it is dependent on the main symbol leg's exit logic.
* Lot/Qty supports both lot-based and quantity-based input. Inputting 1 lot equals the contract's lot size (e.g., 30 qty for BANKNIFTY FUT).
* Opening Qty/Lot sets a separate quantity for the very first entry step only.

When a user asks Copilot to "create a scalping strategy," Copilot should:

1. Identify the underlying symbol (exchange, segment, symbol, contract, expiry).
2. Determine the jobbing side (BUY or SELL).
3. Configure the Average distance (Points or %) and per-step Target.
4. Set Jobbing Start Time and End Time.
5. Configure Maximum Avg. Steps and other Advance controls as mentioned.
6. Enable Sqroff by Master TP SL if combined profit/loss control is needed.
7. Enable Auto Rollover if positional and rollover is mentioned.
8. Add Hedge Leg if a secondary protective instrument is mentioned.
9. Map everything into valid plugin fields.

Copilot should treat Rapid Execution Scalper as the plugin for **automated averaging, jobbing, and step-ladder position-building strategies**.

---

# **✅ 3\. SHORT PLUGIN CARD SUMMARY (To display on homepage)**

### **Rapid Execution Scalper**

Automate high-frequency jobbing and averaging with step-by-step position building.  
Configure Average intervals, per-step Targets, maximum steps, dynamic quantity scaling, Master TP/SL with Trail SL, Auto Rollover, and Hedge Leg — for intraday or positional scalping across all exchanges.

---

# Parameter Description

# Main Parameters

### **1\. Strategy Name**

**Description:** User-defined name of the strategy. Shown in UI and used for identification.  
**Logic:** Does not affect execution. Used only for listing, search, copy/duplicate, and Copilot reference.  
**Type:** String  
**Default Value:** Blank ("")  
**Validation:**

- Required  
- Must be unique per user  
- Minimum length 3, maximum 100 characters  
- Cannot include unsupported special characters

**Example:** "BANKNIFTY BUY Jobbing – Intraday"  
**DB Field Name:** strategy\_name  
**Execution Context:** Used only by UI and Copilot to reference the strategy. Trading Server ignores this value.  
---

### **2\. Symbol**

**Description:** The primary trading instrument for this strategy. Clicking the Symbol field opens the "Select Symbol" dialog where full instrument details are configured.  
**Logic:** The resolved symbol is displayed as a concatenated string (e.g., "BANKNIFTY FUT NEAR MONTHLY" or "360ONE OPT NEAR WEEKLY 0 CE"). The resolved Trading Symbol and Expiry Date are shown at the bottom of the dialog before confirming.  
**Type:** Composite field (opens dialog)  
**Default Value:** Blank (required)  
**Validation:** Required. A fully resolved symbol must be selected.  
**Example:** BANKNIFTY FUT NEAR MONTHLY  
**DB Field Name:** main\_exchange, main\_segment, main\_symbol, main\_contract, main\_expiry, atm, option\_type, strike\_price (all stored as separate fields)  
**Execution Context:** Trading Server uses these fields to identify the exact instrument contract for all averaging and target order placement.  
---

#### **2.1 Exchange**

**Description:** The exchange for the main trading instrument.  
**Logic:** Controls which segments and symbols are available.  
**Type:** String (Dropdown)  
**Default Value:** NFO  
**Validation:** Allowed Values: NSE, NFO, BFO, BSE, MCX, CDS  
**Example:** NFO  
**DB Field Name:** main\_exchange  
**Execution Context:** Determines which market feed and instrument master is used.  
---

#### **2.2 Segment**

**Description:** Segment of the main instrument.  
**Logic:** Determines instrument type. Option Type and ATM fields become active only for OPT segment.  
**Type:** String (Dropdown)  
**Default Value:** FUT  
**Validation:** Allowed Values:

- FUT  
- OPT  
- Stock

**Example:** FUT  
**DB Field Name:** main\_segment  
**Execution Context:** Determines contract type used during instrument resolution.  
---

#### **2.3 Symbol**

**Description:** The underlying instrument symbol.  
**Logic:** All available symbols are filtered based on selected Exchange and Segment.  
**Type:** String (Dropdown / Searchable)  
**Default Value:** BANKNIFTY  
**Validation:** Must be a valid symbol for the selected exchange and segment.  
**Example:** BANKNIFTY, NIFTY, RELIANCE, SILVER  
**DB Field Name:** main\_symbol  
**Execution Context:** Instrument master lookup key used to resolve exact contract for order placement.  
---

#### **2.4 Contract**

**Description:** Select the contract series for this strategy.  
**Logic:** Determines which contract in the expiry sequence is traded.  
**Type:** String (Dropdown)  
**Default Value:** NEAR  
**Validation:** Allowed Values:

- NEAR (nearest/current contract)  
- NEXT (next contract in sequence)  
- FAR (far/distant contract)

**Example:** NEAR  
**DB Field Name:** main\_contract  
**Execution Context:** Used with Expiry to resolve the exact contract date at execution time.  
---

#### **2.5 Expiry**

**Description:** Select the expiry type for this strategy's contract.  
**Logic:** Resolved dynamically at execution time using the symbol's expiry calendar combined with Contract selection.  
**Type:** String (Dropdown)  
**Default Value:** MONTHLY  
**Validation:** Allowed Values:

- MONTHLY  
- WEEKLY (shown only if symbol supports weekly expiry contracts)

**Example:** MONTHLY  
**DB Field Name:** main\_expiry  
**Execution Context:** Trading Server resolves to the actual contract expiry date at execution time.  
---

#### **2.6 ATM**

**Description:** Strike offset from At-The-Money for option instruments.  
**Logic:** Used only when Segment = OPT. Defines how many strikes above or below ATM the strategy should trade. 0 = exactly ATM. Positive values move toward OTM for CE / ITM for PE. Negative values move toward ITM for CE / OTM for PE.  
**Type:** Integer  
**Default Value:** 0  
**Validation:**

- Applicable only when Segment = OPT  
- Must be an integer (positive, negative, or zero)  
- Ignored for FUT and Stock segments

**Example:** 0 (ATM), 1 (one strike OTM for CE), \-1 (one strike ITM for CE)  
**DB Field Name:** atm  
**Execution Context:** Strike resolution engine selects the correct option strike based on this offset at each entry.  
---

#### **2.7 Option Type**

**Description:** Select CE (Call) or PE (Put) for option instruments.  
**Logic:** Active only when Segment = OPT. Blank and ignored for FUT and Stock.  
**Type:** String (Dropdown)  
**Default Value:** CE  
**Validation:** Allowed Values:

- CE  
- PE  
  Valid only when Segment = OPT

**Example:** CE  
**DB Field Name:** option\_type  
**Execution Context:** Determines which side of the option chain is used for strike selection at each step entry.  
---

#### **2.8 Strike Price**

**Description:** Fixed absolute strike price for options when a specific strike is required instead of ATM-relative selection.  
**Logic:** When set to 0, strike selection uses the ATM offset (field 2.6). When set to an actual strike price (e.g., 48000), the system trades that exact strike regardless of ATM position.  
**Type:** Number  
**Default Value:** 0  
**Validation:**

- Must be 0 or a valid positive strike price  
- 0 means use ATM-relative selection  
- Applicable primarily for OPT segment

**Example:** 0 (use ATM offset), 48000 (fixed strike)  
**DB Field Name:** strike\_price  
**Execution Context:** When non-zero, Trading Server uses this exact strike for all step orders. When 0, ATM-relative resolution applies.  
---

### **3\. Lot/Qty**

**Description:** Base lot or quantity for all averaging step orders. The user can input either lots or actual quantity — both refer to the same position size.  
**Logic:** Supports two input modes controlled by `qty_type`:

* **Lot mode:** User enters number of lots (e.g., 1 lot). System multiplies by contract lot size to derive actual qty. For example, 1 lot of BANKNIFTY FUT = 30 qty.  
* **Qty mode:** User enters actual quantity directly (e.g., 30 qty). System treats this as the raw order quantity.

Both modes result in the same position size — they are two ways to express the same value. Every new averaging step uses this as the base quantity (unless Increase/Multiply Qty on Average is enabled in Advance tab).

**Type:** Number  
**Default Value:** 1  
**Validation:**

- Must be a positive integer  
- **Cannot be 0**

**Example:** 1 (lot) = 30 qty for BANKNIFTY FUT  
**DB Field Name:** lot (number of lots), qty (computed or entered quantity), qty\_type ("Lot" or "Qty")  
**Execution Context:** Trading Server uses the resolved quantity when placing each step order.  
---

### **4\. Trading Type**

**Description:** Select whether the strategy runs in Intraday or Positional mode.  
**Logic:**

* Intraday → All open positions are automatically squared off at Jobbing End Time. No new entries after this time.  
* Positional → Positions are carried forward across sessions and managed by SL/Target, Auto Rollover, or manual exit. Jobbing End Time still defines the daily entry cutoff.

**Type:** String (Dropdown)  
**Default Value:** Intraday  
**Validation:** Must be "Intraday" or "Positional"  
**Example:** Intraday  
**DB Field Name:** is\_intraday (true = Intraday, false = Positional)  
**Execution Context:** Controls when and how open positions are force-squared off at end of session.  
---

### **5\. Product**

**Description:** Select the order product type for all entry orders in this strategy.  
**Logic:** This product type is included in every entry order sent to the broker.  
**Type:** String (Dropdown)  
**Default Value:** MIS  
**Validation:** Allowed Values:

- MIS  
- NRML  
- CNC  
- MTF

**Example:** MIS  
**DB Field Name:** product\_type  
**Execution Context:** Trading Server uses this product type when placing all averaging step entry orders.  
---

### **6\. Jobbing Start Time**

**Description:** Define the time from which the strategy is allowed to begin opening positions.  
**Logic:** No new step entries are placed before this time, even if Average conditions are met. Strategy monitoring begins from this time onward.  
**Type:** Time (HH:MM)  
**Default Value:** 09:20  
**Validation:** Must be within exchange trading hours.  
**Example:** 09:20  
**DB Field Name:** intraday\_entry\_time  
**Execution Context:** Trading Server ignores all price triggers before this time and begins opening steps only from Jobbing Start Time onward.  
---

### **7\. Jobbing End Time**

**Description:** Define the time at which the strategy stops accepting new entries.  
**Logic:**

* In Intraday mode: All open positions are force-squared off at this time and no new steps are taken after.  
* In Positional mode: No new averaging steps are opened after this time, but open positions continue to be managed by their targets and Master TP/SL.

**Type:** Time (HH:MM)  
**Default Value:** 15:00  
**Validation:**

- Must be within market hours  
- Must be greater than Jobbing Start Time

**Example:** 15:00  
**DB Field Name:** intraday\_exit\_time  
**Execution Context:** Triggers force square-off for Intraday mode at this time. Blocks new entries for both modes after this time.  
---

### **8\. Jobbing Side**

**Description:** Select the direction of the averaging strategy.  
**Logic:**

* BUY → Strategy opens BUY positions and adds new averaging steps as price falls. Each new step is opened when price drops by the Average distance below the last open position.  
* SELL → Strategy opens SELL positions and adds new averaging steps as price rises. Each new step is opened when price rises by the Average distance above the last open position.

**Type:** String (Dropdown)  
**Default Value:** BUY  
**Validation:** Allowed Values:

- BUY  
- SELL

**Example:** BUY  
**DB Field Name:** jobbing\_side  
**Execution Context:** Trading Server determines the direction of all step entries and target calculations based on this setting.  
---

### **9\. Average By**

**Description:** Select whether the Average distance between steps is measured in Points or Percentage.  
**Logic:**

* Point (P) → Average distance is an absolute price gap in points. Example: Average = 100 means each step opens 100 points below (BUY) or above (SELL) the last step.  
* Percentage (%) → Average distance is a percentage of the last open position price. Example: Average = 1% means each step opens 1% below (BUY) or above (SELL) the last step price.

**Type:** Toggle (P = Points / % = Percentage)  
**Default Value:** Point  
**Validation:** Allowed Values: Point, Percentage  
**Example:** Point  
**DB Field Name:** average\_by  
**Execution Context:** Determines the unit of measurement the Trading Server uses when computing the next averaging step trigger price.  
---

### **10\. Average**

**Description:** Distance between each averaging step, measured in Points or Percentage as selected by Average By.  
**Logic:** When price moves against the last open position by this distance, a new step is opened at the current market price.

Example (BUY, Average = 100 Points):

* Step 1: Buy @ 1500 → next step triggers at 1400  
* Step 2: Buy @ 1400 → next step triggers at 1300  
* Step 3: Buy @ 1300 → next step triggers at 1200

**Type:** Number  
**Default Value:** 0  
**Validation:**

- **Must be greater than 0. Average = 0 is not allowed.**  
- Must be a positive number  
- Unit is determined by Average By selection

**Example:** 100 (Points), 1 (%)  
**DB Field Name:** average\_value  
**Execution Context:** Trading Server continuously monitors the distance between current market price and last open position price. When the gap equals or exceeds this value in the configured direction, a new step is placed.  
---

### **11\. Target By**

**Description:** Select whether the per-step Target is measured in Points or Percentage.  
**Logic:**

* Point (P) → Per-step target is an absolute price gain in points from the step's entry price.  
* Percentage (%) → Per-step target is a percentage gain from the step's entry price.

**Type:** Toggle (P = Points / % = Percentage)  
**Default Value:** Point  
**Validation:** Allowed Values: Point, Percentage  
**Example:** Point  
**DB Field Name:** target\_by  
**Execution Context:** Determines the unit of measurement for per-step target monitoring.  
---

### **12\. Target**

**Description:** Per-step profit target for each averaging position. Each step closes independently when its own target is reached.  
**Logic:** Each step has its own target level calculated from its entry price.

Example (BUY, Target = 100 Points):

* Step 1 (Buy @ 1500) → Target = 1600. Closes when price reaches 1600.  
* Step 2 (Buy @ 1400) → Target = 1500. Closes when price reaches 1500.  
* Step 3 (Buy @ 1300) → Target = 1400. Closes when price reaches 1400.

Each step closes individually — hitting Step 2's target does not affect Step 1 or Step 3.

If Target = 0: Per-step targets are disabled. Positions will only close due to Master TP/SL, Jobbing End Time, or manual intervention.

**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means no per-step target.  
**Example:** 100 (Points)  
**DB Field Name:** target  
**Execution Context:** Trading Server calculates each step's target price at entry time and monitors independently for each open step.  
---

### **13\. Template**

**Description:** Select a pre-built strategy template to auto-populate settings and default parameters.  
**Logic:** Selecting a template loads pre-configured instrument, timing, Average, and Target values. User can modify any field after loading. The **Import Template** button allows importing a previously exported strategy configuration.  
**Type:** String (Dropdown)  
**Default Value:** Default  
**Validation:** Allowed Values:

- Default  
- RELIANCE Scalping  
- SILVER Scalping  
- USDINR \- BUY \- Intraday  
- USDINR \- SELL \- Intraday  
- USDINR BUY Scalping  
- USDINR SELL Scalping

**Example:** RELIANCE Scalping  
**DB Field Name:** (UI only – template selection populates other fields; not stored as a separate DB field)  
**Execution Context:** Template is a UI-only convenience feature. Only the resulting populated parameter values are stored and used during execution.  

---

# Advance Parameters

### **1\. Jobbing Start Price**

**Description:** Optional price level at which the strategy is allowed to begin opening positions.  
**Logic:** When set to 0, the strategy starts immediately at Jobbing Start Time regardless of price. When set to a non-zero value, the strategy waits until the market price crosses this level before opening the first step. Does not affect already-open positions.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means start immediately.  
**Example:** 1500 (strategy begins only when price reaches or crosses 1500)  
**DB Field Name:** jobbing\_start\_price  
**Execution Context:** Trading Server compares live market price against this value before triggering the first entry. Once price crosses this level, normal averaging logic takes over.  
---

### **2\. Jobbing End Price**

**Description:** Optional price boundary beyond which no new averaging steps are opened.  
**Logic:** Works as a reverse boundary. When price moves beyond this level (below for BUY, above for SELL), no new averaging steps are taken. Existing open positions remain active and continue to be managed. Setting to 0 disables this boundary.

Example (BUY side):

* Jobbing Start Price = 1500, Jobbing End Price = 1300  
* Strategy starts at 1500 and stops opening new averages if price drops below 1300.

**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means no end boundary.  
**Example:** 1300  
**DB Field Name:** jobbing\_end\_price  
**Execution Context:** Trading Server checks this level before opening each new average step. If current price is beyond this boundary, the new step is blocked. Open positions are not affected.  
---

### **3\. Maximum Avg. Steps**

**Description:** Maximum number of averaging positions that can be opened by the strategy.  
**Logic:** Once this number of steps is open, no further averaging entries are made. If Sqroff on max avg. steps is enabled, all open positions are closed when this limit is reached.  
**Type:** Number  
**Default Value:** 50  
**Validation:** Must be a positive integer.  
**Example:** 10  
**DB Field Name:** maximum\_steps  
**Execution Context:** Trading Server tracks total open step count and blocks new averages once Maximum Avg. Steps is reached.  
---

### **4\. Maximum Target Steps**

**Description:** Maximum number of new steps that can be opened when the market moves in the strategy's favor (profitable direction).  
**Logic:** Controls over-trading on the profitable side during trending markets. Once this many positive-side steps are opened, no further entries in that direction are allowed.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means no limit on target-side steps.  
**Example:** 5  
**DB Field Name:** maximum\_target\_steps  
**Execution Context:** Trading Server counts upside steps (for BUY) or downside steps (for SELL) and blocks further entries once this limit is hit.  
---

### **5\. Reset Cycle after Steps on Positive MTM**

**Description:** Automatically close all open positions and restart a fresh jobbing cycle when the number of open steps equals this value and current combined MTM is positive.  
**Logic:** If the count of currently open steps equals this configured number AND the total MTM is positive, the plugin closes all positions and restarts a new averaging cycle from the current market price. This helps lock in profits during sideways markets. If set to 0, this feature is disabled.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means feature disabled.  
**Example:** 4 (auto-reset when 4 steps are open and MTM is positive)  
**DB Field Name:** reset\_cycle\_on\_positive\_mtm  
**Execution Context:** Trading Server evaluates open step count and total MTM continuously. When both conditions are met simultaneously, all positions are closed and a new cycle begins from current price.  
---

### **6\. Required Margin**

**Description:** Estimated total capital required to run all configured steps.  
**Logic:** Informational field only. Used for analytics, ROI calculation, and planning. Does not block or affect trade execution.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be a positive number.  
**Example:** 150000  
**DB Field Name:** required\_margin  
**Execution Context:** Displayed to user for planning and risk assessment. Trading Server does not use this value as an execution condition.  
---

### **7\. Exit Order Product Type**

**Description:** Optional product type to use specifically for exit orders, independent of the entry product type.  
**Logic:** When specified, all square-off orders (step target exits, Master TP/SL exits, Jobbing End Time exits) use this product type. When left blank, exit orders use the same product type as entries.  
**Type:** String (Dropdown, optional)  
**Default Value:** Blank (uses entry product type)  
**Validation:** Allowed Values:

- MIS  
- NRML  
- CNC  
- MTF  
- Blank (inherits from Product field)

**Example:** MIS (enter with NRML, exit with MIS for intraday broker settlement)  
**DB Field Name:** exit\_order\_product\_type  
**Execution Context:** Trading Server uses this product type for all exit orders when configured. Useful when broker requires different product types for entry and exit.  
---

### **8\. Opening Qty/Lot**

**Description:** Define a specific quantity or lot count for the very first entry step only.  
**Logic:** When set to a non-zero value, the first position opened by the strategy uses this quantity instead of the base Lot/Qty from the Main tab. All subsequent averaging steps use the base Lot/Qty (subject to Increase/Multiply Qty if configured). When set to 0, the first step uses the same base Lot/Qty as all other steps.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means use base Lot/Qty for the first step.  
**Example:** 2 (first entry opens 2 lots; subsequent steps open 1 lot each)  
**DB Field Name:** scalping\_opening\_qty  
**Execution Context:** Trading Server applies this quantity specifically to the first step order. From step 2 onward, base Lot/Qty and Increase/Multiply Qty logic applies.  
---

### **9\. Increase/Multiply Qty on Average**

**Description:** Enable dynamic quantity adjustment for each new averaging step.  
**Logic:** When enabled, each new averaging step uses a quantity derived from the previous step's quantity, adjusted by the configured Type and value. This allows exponential or linear position scaling as the strategy averages deeper.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** increase\_qty\_on\_avg  
**Execution Context:** Activates the quantity scaling engine for all step entries after the first step.  
---

#### **9.1 Quantity**

**Description:** The value used to increase or multiply quantity at each new averaging step.  
**Logic:**

* If Type = Increase → New Step Qty = Previous Step Qty + this value  
* If Type = Multiply → New Step Qty = Previous Step Qty × this value

Example (Base Qty = 1, Quantity = 1, Type = Increase): Steps → 1, 2, 3, 4, ...  
Example (Base Qty = 1, Quantity = 2, Type = Multiply): Steps → 1, 2, 4, 8, ...

**Type:** Number  
**Default Value:** 1  
**Validation:** Must be a positive number.  
**Example:** 2  
**DB Field Name:** increase\_qty  
**Execution Context:** Applied to derive the quantity for each new averaging step based on selected Type.  
---

#### **9.2 Type**

**Description:** Defines whether quantity is increased by addition or multiplication at each step.  
**Logic:**

* Increase → Adds the configured Quantity value to the previous step's quantity.  
* Multiply → Multiplies the previous step's quantity by the configured Quantity value.

**Type:** String (Dropdown)  
**Default Value:** Increase  
**Validation:** Allowed Values:

- Increase  
- Multiply

**Example:** Multiply  
**DB Field Name:** increase\_qty\_type  
**Execution Context:** Trading Server applies the selected arithmetic operation to compute each new step's order quantity.  
---

### **10\. Sqroff on max avg. steps**

**Description:** Enable automatic square-off of all open positions when Maximum Avg. Steps count is reached.  
**Logic:** When enabled, as soon as the number of open averaging steps equals Maximum Avg. Steps, all open positions are immediately closed. When disabled, the strategy simply stops opening new averages at the limit but keeps existing positions open.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** sqroff\_on\_maximum\_steps  
**Execution Context:** Trading Server triggers immediate square-off of all open steps when maximum count is hit and this flag is enabled. Acts as a safety guardrail against deep averaging.  
---

### **11\. Calculate Qty on Market Jump**

**Description:** Enable automatic detection and handling of large market gap openings between trading sessions.  
**Logic:** When enabled, if the next session opens at a price that is multiple Average distances away from the last open position price, the plugin calculates how many averaging steps were skipped and opens one consolidated position with the combined quantity of all skipped steps.

Reference for jump calculation: Last open position price (not previous day's close).

Example:

* Last open position = 1500, Average = 100  
* Next session opens at 1200 → Gap = 300 points → 3 steps skipped  
* Plugin opens 1 position with 3× base quantity at 1200

**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** calculate\_qty\_on\_market\_jump  
**Execution Context:** Trading Server evaluates the gap between last open position price and current session opening price on session start. If gap spans multiple Average distances, a single catch-up order is placed with combined quantity.  
---

### **12\. Sqroff by Master TP SL**

**Description:** Enable a global target and stoploss that monitors the total combined MTM across all open steps and closes all positions when the overall threshold is reached.  
**Logic:** When enabled, the Trading Server continuously tracks the combined profit/loss of all open steps. If total MTM profit reaches Master Target or total MTM loss reaches Master SL, all positions are immediately squared off. This operates independently of per-step targets.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** reset\_cycle\_by\_master\_tpsl  
**Execution Context:** Activates master-level MTM monitoring. Both Master Target (Money) and Master SL (Money) sub-fields become active.  
---

#### **12.1 Master Target (Money)**

**Description:** Define the total combined profit level at which all open positions are closed.  
**Logic:** When the sum of MTM profit across all open steps reaches or exceeds this value, all positions are immediately squared off. 0 = Master Target disabled.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means no master target.  
**Example:** 5000  
**DB Field Name:** master\_tp\_money  
**Execution Context:** Trading Server monitors combined P&L of all open steps and triggers full strategy exit when this threshold is reached.  
---

#### **12.2 Master SL (Money)**

**Description:** Define the total combined loss level at which all open positions are closed.  
**Logic:** When the sum of MTM loss across all open steps reaches or exceeds this value, all positions are immediately squared off. 0 = Master SL disabled.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means no master SL.  
**Example:** 10000  
**DB Field Name:** master\_sl\_money  
**Execution Context:** Trading Server monitors combined loss of all open steps and triggers full strategy exit when this threshold is breached. This is the highest-priority exit condition.  
---

#### **12.3 Trail SL?**

**Description:** Enable trailing of the Master SL as the combined strategy profit grows.  
**Logic:** When enabled, the Master SL is dynamically adjusted closer to the current profit level as combined strategy profit increases. This progressively locks in profits at the master level. Three sub-fields become active. All three sub-fields must be non-zero for trailing to activate.  
**Type:** Boolean (Checkbox, nested under Sqroff by Master TP SL)  
**Default Value:** False  
**Validation:**

- Only active when Sqroff by Master TP SL is enabled  
- Allowed values: True / False

**Example:** True  
**DB Field Name:** is\_trail\_sl  
**Execution Context:** Activates dynamic master SL trailing logic. Applied on top of the fixed Master SL value.  
---

#### **12.3.1 Profit Move**

**Description:** The combined profit increase required to trigger one Master SL trail step.  
**Logic:** Each time the total combined profit of all open steps increases by this amount from the last trail level, the Master SL is moved by the configured SL Move amount.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means trailing does not activate.  
**Example:** 1000  
**DB Field Name:** profit\_move  
**Execution Context:** Profit movement trigger for master SL trailing. Each time this threshold is crossed from the last trail level, the SL adjustment is applied.  
---

#### **12.3.2 SL Move**

**Description:** The amount by which the Master SL is moved on each trail step.  
**Logic:** Each time combined profit increases by Profit Move, the Master SL is shifted by this amount closer to the current profit level, reducing overall risk exposure.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0.  
**Example:** 500  
**DB Field Name:** sl\_move  
**Execution Context:** Determines the adjustment size applied to the Master SL at each trailing event.  
---

#### **12.3.3 No of Trail SL**

**Description:** Maximum number of times the Master SL can be trailed.  
**Logic:** After this many trailing steps, no further Master SL adjustments are made. 0 = unlimited trailing.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means unlimited.  
**Example:** 10  
**DB Field Name:** no\_of\_trail\_sl  
**Execution Context:** Limits the total number of trailing operations performed on the Master SL.  
---

### **13\. Auto Rollover**

**Description:** Enable automatic transfer of open positions from the current contract to the next contract before expiry.  
**Logic:** When enabled, on the configured Rollover date and time, the plugin closes all open positions in the current contract and opens equivalent positions in the next contract at market price. This ensures continuity for positional strategies without manual intervention. Auto Rollover applies to Futures and Options instruments.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:**

- Allowed values: True / False  
- **Only applicable when Trading Type = Positional. Auto Rollover does not work in Intraday mode.**

**Example:** True  
**DB Field Name:** is\_auto\_rollover  
**Execution Context:** Trading Server monitors contract expiry dates and triggers rollover on the configured Rollover date at Rollover Time.  
---

#### **13.1 Rollover Before Expiry Days**

**Description:** Number of calendar days before contract expiry on which the rollover should be executed.  
**Logic:** Rollover date = Contract Expiry Date − Rollover Before Expiry Days. On this date at Rollover Time, all open positions are closed in the current contract and reopened in the next contract.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be ≥ 0. 0 means rollover happens on the expiry day itself.  
**Example:** 1 (rollover one day before expiry)  
**DB Field Name:** rollover\_before\_days  
**Execution Context:** Trading Server computes rollover execution date using this value subtracted from the contract expiry date.  
---

#### **13.2 Rollover Time**

**Description:** Exact time of day at which the rollover is executed on the rollover date.  
**Logic:** On the computed rollover date, the Trading Server closes all open positions in the current contract and opens matching positions in the next contract at this time.  
**Type:** Time (HH:MM)  
**Default Value:** 14:29  
**Validation:** Must be within exchange trading hours.  
**Example:** 14:29  
**DB Field Name:** rollover\_time  
**Execution Context:** Defines the precise timestamp for automatic contract rollover execution.  
---

### **14\. Add Hedge Leg**

**Description:** Enable an additional secondary instrument that is executed alongside the main strategy as a hedge or protective position.  
**Logic:** When enabled, the user configures one or more hedge leg instruments using the Select Symbol dialog. The hedge leg executes in sync with the main strategy. The hedge leg has **no independent TP/SL** — its exit behavior is completely dependent on the main symbol leg's exit conditions (Master TP/SL, Jobbing End Time, manual stop, etc.). Multiple hedge legs can be added. Each can be deleted using the (×) button.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** is\_add\_hedge\_leg  
**Execution Context:** When enabled, Trading Server executes hedge leg orders alongside main strategy orders. Hedge leg exits are triggered by the same conditions as the main strategy exit.  
---

#### **14.1 Hedge Leg Symbol**

**Description:** The secondary instrument to be added as the hedge leg. Configured via the Select Symbol dialog.  
**Logic:** Clicking the Symbol field opens the Select Symbol dialog with the same fields as the main symbol (Exchange, Segment, Symbol, Contract, Expiry, ATM, Option Type). The resolved instrument is displayed as a concatenated string (e.g., "BANKNIFTY FUT NEAR MONTHLY"). Multiple hedge legs can be added. Each hedge leg row has a delete (×) button.  
**Type:** Composite field (opens Select Symbol dialog)  
**Default Value:** Blank (required when Add Hedge Leg is enabled)  
**Validation:** Required when Add Hedge Leg is checked. A fully resolved symbol must be selected.  
**Example:** BANKNIFTY FUT NEAR MONTHLY  
**DB Field Name:** sub\[\].exchange, sub\[\].segment, sub\[\].symbol, sub\[\].contract, sub\[\].expiry, sub\[\].atm, sub\[\].option\_type  
**Execution Context:** Trading Server resolves and executes this instrument alongside the main strategy. Exit of hedge leg follows main strategy exit conditions — not independent TP/SL.  

---

# Description Parameters

### **1\. Short Description**

**Description:** A brief one-line summary written by the user to identify the strategy in listings and reports.  
**Logic:** Purely informational. No impact on execution, averaging, target, or SL.  
**Type:** Single-line Text Input  
**Default Value:** Blank  
**Validation:** Optional. Recommended max length 100–150 characters. No logic validation required.  
**Example:** "Intraday BUY scalping on BANKNIFTY FUT with 100-point average and 100-point target."  
**DB Field Name:** short\_description  
**Execution Context:** Displayed only for user reference (Strategy List, Detail View, Copilot Preview). Not used in execution.  
---

### **2\. Long Description**

**Description:** A longer explanation entered by the user to document the strategy logic, averaging rules, and usage notes for future reference.  
**Logic:** Informational only. Does not affect how the strategy executes. Used only for user-level documentation and Copilot understanding.  
**Type:** Multi-line Text Area  
**Default Value:** Blank  
**Validation:** Optional. No restrictions on length or format.  
**Example:** "This strategy executes BUY jobbing on BANKNIFTY FUT NEAR MONTHLY. Averages every 100 points. Per-step target 100 points. Max 10 steps. Master SL ₹50,000. Auto rollover before 1 day of expiry. Trail SL after every ₹5,000 profit move."  
**DB Field Name:** long\_description  
**Execution Context:** Displayed only for user and Copilot reference. Has no role in execution, averaging, or exit logic.  

---

# Help

### **🔹 TAB 1: MAIN – HELP**

**Strategy Name**  
Give a unique name to identify your strategy. Used only for your reference and reports — does not affect execution.

**Symbol**  
Click to open the "Select Symbol" dialog. Configure Exchange, Segment, Symbol, Contract, Expiry, ATM, and Option Type for the main instrument.  
The resolved Trading Symbol and Expiry Date are shown before you confirm.

**Exchange**  
Select the exchange for this strategy: NSE, NFO, BFO, BSE, MCX, CDS.

**Segment**  
Select **FUT** for Futures, **OPT** for Options, or **Stock** for equity cash.  
ATM and Option Type fields are only relevant for OPT.

**Symbol**  
Select the underlying instrument (e.g., BANKNIFTY, NIFTY, RELIANCE, SILVER).

**Contract**  
Select **NEAR** (current contract), **NEXT** (next contract), or **FAR** (far contract).

**Expiry**  
Select **MONTHLY** or **WEEKLY** contract expiry type.  
WEEKLY is shown only for symbols that support weekly expiry contracts.

**ATM**  
For OPT segment only. 0 = At-The-Money strike. Positive values move toward OTM (for CE) / ITM (for PE). Negative values move toward ITM (for CE) / OTM (for PE).

**Option Type**  
For OPT segment only. Select **CE** (Call) or **PE** (Put).

**Lot/Qty**  
Base quantity for all averaging step orders. You can enter either:

* **Lots** (e.g., 1) → System uses Exchange lot size to compute actual quantity.  
* **Quantity** (e.g., 30) → System uses raw quantity directly.  
Both express the same position size. **Cannot be 0.**

**Trading Type**  
Choose **Intraday** or **Positional**.  
Intraday: all positions are squared off at Jobbing End Time.  
Positional: positions carry forward until SL/Target, Auto Rollover, or manual exit.

**Product**  
Select product type for entry orders: MIS, NRML, CNC, or MTF.  
Affects margin usage and carry-forward eligibility.

**Jobbing Start Time**  
Time from which the strategy is allowed to start taking positions.  
No entries are made before this time.

**Jobbing End Time**  
Time at which the strategy stops taking new entries.  
In Intraday mode, all open positions are force-squared off at this time.

**Jobbing Side**  
Select **BUY** or **SELL**.  
BUY: averages down — adds positions as price falls.  
SELL: averages up — adds positions as price rises.

**Average By**  
Select **P** (Points) or **%** (Percentage) to define how the Average distance is measured.

**Average**  
Distance between each averaging step in Points or Percentage.  
**Cannot be 0.** A new step opens each time price moves this distance against the last open position.

**Target By**  
Select **P** (Points) or **%** (Percentage) to define how per-step Target is measured.

**Target**  
Per-step profit target. Each step closes independently when its target is reached.  
0 = no per-step target (only Master TP/SL and Jobbing End Time will close positions).

**Template**  
Load a pre-built configuration. Options include Default, RELIANCE Scalping, SILVER Scalping, USDINR variants.  
Use **Import Template** to load a previously saved strategy configuration.

---

### **🔹 TAB 2: ADVANCE – HELP**

**Jobbing Start Price**  
Optional price level where the strategy begins taking its first trade.  
0 = starts immediately at Jobbing Start Time regardless of price.  
If defined, the strategy waits until market price reaches this level before opening the first step.

**Jobbing End Price**  
Optional price boundary beyond which no new averaging steps are opened.  
0 = no boundary. Existing open positions are not affected — only new entries are blocked.

**Maximum Avg. Steps**  
Maximum number of averaging positions the strategy can open.  
Once this limit is hit, no new averaging entries are made.

**Maximum Target Steps**  
Maximum number of steps that can be opened on the profitable side (when market moves in your favor).  
0 = no limit. Used to prevent over-trading in strongly trending markets.

**Reset Cycle after Steps on Positive MTM**  
When the number of open steps equals this value and combined MTM is positive, all positions are closed and a fresh jobbing cycle begins.  
0 = feature disabled.

**Required Margin**  
Estimated capital needed to run all configured steps.  
Informational only — used for ROI and planning. Does not block or affect trade execution.

**Exit Order Product Type**  
Optionally specify a different product type for all exit orders.  
If blank, exits use the same product type as entries.  
Options: MIS, NRML, CNC, MTF.

**Opening Qty/Lot**  
Quantity or lots to use specifically for the first entry step only.  
0 = first step uses the same base Lot/Qty as all other steps.

**Increase/Multiply Qty on Average (Checkbox)**  
Enable dynamic quantity scaling at each new averaging step.  
When checked:

* **Quantity:** Value added or multiplied at each step.  
* **Type:** Select **Increase** (addition) or **Multiply** (multiplication).

Example: Base = 1, Quantity = 2, Multiply → Steps: 1, 2, 4, 8...

**Sqroff on max avg. steps (Checkbox)**  
When enabled, all open positions are automatically closed when Maximum Avg. Steps count is reached.  
When disabled, new averaging simply stops at the limit — existing positions remain open.

**Calculate Qty on Market Jump (Checkbox)**  
Handles market gap openings for positional strategies.  
When the next session opens far from the last open position (spanning multiple Average distances), the plugin opens one position with the combined quantity of all skipped steps.

**Sqroff by Master TP SL (Checkbox)**  
Enable global combined target and stoploss for the entire strategy.  
When checked:

* **Master Target (Money):** Closes all positions when total combined MTM profit reaches this value. 0 = disabled.  
* **Master SL (Money):** Closes all positions when total combined MTM loss reaches this value. 0 = disabled.  
* **Trail SL? (Checkbox):** Enable Master SL trailing as combined profit grows. When checked:  
  * **Profit Move:** Combined profit increase to trigger one SL trail step.  
  * **SL Move:** Amount Master SL moves per trail step.  
  * **No of Trail SL:** Maximum trail steps. 0 = unlimited.

**Auto Rollover (Checkbox)**  
Automatically transfer open positions to the next contract before expiry.  
Works **only in Positional mode.** When checked:

* **Rollover Before Expiry Days:** Days before expiry to execute rollover. 0 = rollover on expiry day.  
* **Rollover Time:** Exact time of day the rollover is executed. Must be within market hours.

**Add Hedge Leg (Checkbox)**  
Add one or more secondary instruments executed alongside the main strategy as hedges.  
When checked, a Symbol row appears — click it to open the Select Symbol dialog and configure the hedge instrument.  
Use **(×)** to remove a hedge leg. Multiple hedge legs can be added.  
**Hedge legs have no independent TP/SL** — they exit based on the main strategy's exit conditions.

---

### **🔹 TAB 3: DESCRIPTION – HELP**

**Short Description**  
One-line summary of your strategy. Optional. Used for quick identification in lists and reports.

**Long Description**  
Detailed notes about your strategy's averaging logic, instrument setup, and trading conditions. Optional. Used only for your reference and Copilot understanding.

---

# FAQ

**Q1. What is the purpose of the Rapid Execution Scalper plugin?**  
The Rapid Execution Scalper performs automated high-frequency jobbing based on predefined Average and Target levels. It opens trades at set intervals and closes each step individually when its target is achieved. This allows continuous short-term trading within intraday or positional timeframes.

**Q2. How does the averaging system work?**  
Whenever the market moves against the last open position by the defined Average distance (in Points or %), the plugin opens a new averaging position. Each averaging step has its own independent target and closes only when that target is reached.

**Q3. Will the plugin close all positions when a target is hit?**  
No. Each step has its own target. When a step reaches its target, only that specific step is closed. Other steps remain open until their own targets or the Jobbing End Time.

**Q4. What is the difference between Intraday and Positional trading types?**  
Intraday: All open positions are automatically squared off at Jobbing End Time.  
Positional: Positions are carried forward and can be rolled over automatically before expiry.

**Q5. What do Jobbing Start Price and Jobbing End Price do?**  
Jobbing Start Price: Defines when the strategy should begin taking trades. If 0, it starts immediately at Jobbing Start Time.  
Jobbing End Price: Works in reverse. If defined, no new average steps are taken when price goes below this level (BUY side). Existing trades remain unaffected.

**Q6. How is the Average distance calculated?**  
The Average value represents the gap between each averaging step. For example, with Average = 100 Points and BUY side:  
Step 1: Buy @ 1500 → Step 2: Buy @ 1400 → Step 3: Buy @ 1300.  
Each new step opens when price moves 100 points below the last open position.

**Q7. How does the Target work?**  
Each step has its own independent target level calculated from its entry price:  
Step 1 (Buy @ 1500) → Target = 1600.  
Step 2 (Buy @ 1400) → Target = 1500.  
When price reaches 1500, Step 2 closes, but Step 1 remains open until 1600.

**Q8. Can Average be set to 0?**  
No. Average must always be greater than 0. Setting Average to 0 is not allowed and will be rejected on save.

**Q9. Can Target be set to 0?**  
Yes. Target = 0 disables per-step targets. In that case, positions close only when Master TP/SL is triggered, at Jobbing End Time, or through manual intervention.

**Q10. What is Calculate Qty on Market Jump?**  
If enabled, the plugin checks for large market gaps between trading sessions. If the next session opens away from the last open position price by multiple Average distances, it opens a position with combined quantity equal to all skipped steps.  
Example: Last open = 1500, Average = 100, Next open = 1200 → Gap = 300 → 3 skipped steps → New position = 3× base quantity.

**Q11. Does Calculate Qty on Market Jump use previous day's close?**  
No. It uses the last open position price as the reference. The plugin measures the distance between that price and the new session's opening price to calculate skipped steps.

**Q12. What is Reset Cycle after Steps on Positive MTM?**  
If the open step count equals the configured number and your current MTM is positive, the plugin automatically closes all positions and restarts a new jobbing cycle. This helps lock in profits during sideways markets. 0 = disabled.

**Q13. What is Maximum Avg. Steps?**  
Defines the maximum number of averaging positions that can be opened. Once this number is reached, no new averages are taken. If Sqroff on max avg. steps is enabled, all open positions are closed when the limit is hit.

**Q14. What does Increase/Multiply Qty on Average mean?**  
This allows dynamic quantity adjustment for each new averaging step.  
Increase: Adds the defined Quantity to previous step's quantity.  
Multiply: Multiplies previous step's quantity by the configured value.  
Example: Base Qty = 1, Type = Multiply, Value = 2 → Steps: 1, 2, 4, 8...

**Q15. What is Required Margin?**  
It is the estimated capital needed to execute all configured steps. It is used for risk management and analytics only — it does not block trades.

**Q16. What happens when Sqroff by Master TP SL is enabled?**  
If enabled, the plugin continuously monitors total strategy profit/loss. When the overall MTM reaches Master Target (Money), all open positions are immediately closed. When total loss reaches Master SL (Money), all open positions are immediately closed.

**Q17. What is the difference between Master Target and Step Target?**  
Step Target: Applies individually to each averaging leg — each step closes when its own target is hit.  
Master Target: Applies to total combined MTM across all open steps. When Master Target is hit, the entire strategy closes regardless of per-step status.

**Q18. What is Trail SL under Sqroff by Master TP SL?**  
Trail SL is a nested feature inside Sqroff by Master TP SL. When enabled, the Master SL is dynamically adjusted closer to the current profit level as combined strategy profit increases by the configured Profit Move amount. SL Move defines how much the Master SL shifts per trail step. No of Trail SL limits the number of trail events (0 = unlimited).

**Q19. What is Auto Rollover?**  
If enabled, the plugin automatically transfers open positions from the current expiry contract to the next one based on Rollover Before Expiry Days and Rollover Time settings. It closes all positions in the current contract and opens identical positions in the next expiry contract at market price.

**Q20. Can Auto Rollover be used in Intraday mode?**  
No. Auto Rollover works only in Positional mode.

**Q21. What is Maximum Target Steps?**  
It limits the number of new positions on the profitable side (when the market moves in your favor). Used to control over-trading in trending markets.

**Q22. What is the difference between Jobbing End Time and Rollover Time?**  
Jobbing End Time: Marks the end of daily trading — no new entries after this time. In Intraday, all open positions are squared off at this time.  
Rollover Time: Used only in Positional mode — defines the exact time on the rollover date when the contract transfer occurs.

**Q23. Can I use Entry and Exit product types differently?**  
Yes. Use Exit Order Product Type to specify a different product type for exit orders. Example: Enter using NRML, exit using MIS.

**Q24. What is Opening Qty/Lot?**  
Defines the quantity or lots for only the first entry step. If blank or 0, the system uses base Lot/Qty from the Main tab for the first step. All subsequent averaging steps use the base Lot/Qty (subject to Increase/Multiply Qty if configured).

**Q25. What does the Add Hedge Leg feature do?**  
When enabled, a secondary protective instrument is added to the strategy. The hedge leg executes alongside the main strategy. It has no independent TP/SL — its exit is completely dependent on the main symbol leg's exit conditions (Master TP/SL, Jobbing End Time, manual stop).

**Q26. Can I configure TP/SL for the hedge leg independently?**  
No. The hedge leg does not have independent TP/SL settings. It exits based on the main strategy exit triggers only.

**Q27. What are the exit conditions for the strategy?**  
Positions can exit under these scenarios (in priority order):  
1. Master SL (highest priority — immediate capital protection)  
2. Master Target (overall MTM profit goal reached)  
3. Sqroff on Maximum Avg. Steps (if enabled)  
4. Jobbing End Time (Intraday force square-off)  
5. Per-Step Target (each step closes independently at all times)

**Q28. What happens after Jobbing End Time?**  
In Intraday mode: All open trades are auto-squared off and no new entries are allowed after this time.  
In Positional mode: No new entries are allowed after this time, but open positions continue to be managed by targets and Master TP/SL.

**Q29. What happens if all steps are closed — does the strategy restart automatically?**  
Yes. After all steps are closed, the strategy remains active and continues monitoring price. It will open a new step from the current market price when price moves by the Average distance in either direction from the last closed step price.  
Example: Average = 100, last closed step at 1600. If price rises to 1700 → new step opens at 1700. If price falls to 1500 → new step opens at 1500.

**Q30. Can the strategy be paused without closing open positions?**  
Yes. When paused: no new averages or targets are executed but existing open trades remain live with the broker. When resumed: the system re-syncs with current prices and resumes averaging and target logic seamlessly.

**Q31. Does the plugin support all exchanges?**  
Yes. It supports NFO, NSE, BFO, BSE, MCX, and CDS segments across Futures, Options, and Stock instruments.

**Q32. Can I run BUY and SELL strategies simultaneously?**  
Yes — create two separate strategies (one with Jobbing Side = BUY, one with SELL). Each manages its own averaging and target logic independently.

**Q33. What is the best practice for safety?**  
Always define Maximum Avg. Steps. Enable Sqroff by Master TP SL with non-zero Master SL. Define Jobbing End Time. Avoid setting Average to 0. Backtest all parameters before live deployment.

**Q34. How should I configure Lot/Qty?**  
You can enter either lots (e.g., 1 lot for BANKNIFTY = 30 qty) or actual quantity (e.g., 30). Both input modes result in the same position size. The system accepts whichever method you use.

**Q35. What if my internet or broker API disconnects?**  
Once reconnected, the plugin re-syncs open positions using the broker's order book and resumes logic from the last known state.

**Q36. What is the best practice to configure exit safety?**  
1. Always enable Master TP/SL.  
2. Use Sqroff on Maximum Avg. Steps as an additional guardrail.  
3. Keep Jobbing End Time defined even in positional strategies.  
4. Avoid setting Average to 0 — it is not allowed.  
5. Backtest all parameters before enabling live trades.

---

# Copilot Rulebook

Below is the **FULL "HOW COPILOT SHOULD RESPOND" RULEBOOK** for the Rapid Execution Scalper Plugin.

This is a master AI-instruction document that completely defines:

* How Copilot must interpret user prompts  
* How Copilot must map natural language into plugin parameters  
* How Copilot must configure averaging, targets, and exit logic  
* How Copilot must ask clarifying questions (only when needed)  
* How Copilot must generate strategy output  
* How Copilot must avoid mistakes

---

# **🧠📘 Rapid Execution Scalper – COPILOT RESPONSE RULEBOOK**

### ***AI Behavior & Interpretation Logic***

---

# **1️⃣ COPILOT's PURPOSE**

The Copilot's job is to **convert trader instructions** (natural language) into a **complete Rapid Execution Scalper strategy configuration**:

* Main Parameters  
* Advance Parameters  
* Description Tab

Copilot must generate **100% valid, executable configurations**, following all plugin field rules and averaging logic constraints.

Copilot should behave like a **trading assistant**, not a chatbot.

---

# **2️⃣ CORE RESPONSIBILITIES**

Copilot must:

### **✔ Understand the averaging/jobbing model**

This plugin builds step-by-step positions at fixed Average intervals. Each step has its own independent target. Master TP/SL controls the overall strategy exit. Copilot must not confuse this with hedging, indicator-based, or signal-based strategies.

### **✔ Know the hard rules**

* Average **cannot be 0** — must always be a positive number.  
* Lot/Qty **cannot be 0** — must be a positive number.  
* Trail SL is a **nested sub-feature inside Sqroff by Master TP SL** — it cannot exist without the parent checkbox being enabled.  
* Auto Rollover **only works in Positional mode**.  
* Hedge leg has **no independent TP/SL** — it follows main strategy exits.

### **✔ Map every human phrase to correct plugin parameters**

Example:  
"Create a BankNifty buy scalping strategy with 100-point average and 100-point target, max 10 steps, Master SL ₹50,000"  
→ Main: BANKNIFTY FUT NEAR MONTHLY, Jobbing Side = BUY, Average = 100 (Point), Target = 100 (Point), Advance: Maximum Avg. Steps = 10, Sqroff by Master TP SL = ON, Master SL = 50000

### **✔ Ask only necessary clarifying questions**

Only when critical information is missing.

### **✔ Ensure valid output**

All field values must follow allowed options, ranges, and constraints.

---

# **3️⃣ HOW COPILOT MUST INTERPRET NATURAL LANGUAGE**

---

## **A. Identify the Main Instrument**

Copilot must detect which instrument to configure:

* "BankNifty futures" → Segment = FUT, Symbol = BANKNIFTY, Expiry = MONTHLY, Contract = NEAR  
* "Nifty weekly CE ATM" → Segment = OPT, Symbol = NIFTY, Expiry = WEEKLY, ATM = 0, OptionType = CE  
* "Silver MCX" → Exchange = MCX, Segment = FUT, Symbol = SILVER  
* "Reliance stock" → Segment = Stock, Exchange = NSE, Symbol = RELIANCE  
* "USDINR" → Exchange = CDS, Segment = FUT, Symbol = USDINR

---

## **B. Identify Jobbing Side**

* "buy averaging" / "buy jobbing" / "buy side" → Jobbing Side = BUY  
* "sell averaging" / "sell scalping" / "short side" → Jobbing Side = SELL  
* No mention → Default: BUY

---

## **C. Identify Average and Target**

* "100 points average" → Average = 100, Average By = Point  
* "1% average" → Average = 1, Average By = Percentage  
* "target 100 points" → Target = 100, Target By = Point  
* "no target" / "target disabled" → Target = 0  
* "same as average" → Target = same value and type as Average

**Always verify Average > 0. If user says Average = 0, correct to a minimum positive value and explain.**

---

## **D. Identify Trading Type and Timing**

* "intraday" → is\_intraday = true  
* "positional" / "carry forward" / "overnight" → is\_intraday = false  
* "start at 9:20" → intraday\_entry\_time = 09:20  
* "end at 3:15" / "close at 3:15" → intraday\_exit\_time = 15:15  
* No mention → Default: Intraday, Start 09:20, End 15:00

---

## **E. Identify Advance Controls**

* "max 10 steps" → Maximum Avg. Steps = 10  
* "close all when max steps hit" → Sqroff on max avg. steps = True  
* "double quantity each step" → Increase/Multiply Qty = ON, Type = Multiply, Quantity = 2  
* "add 1 lot each step" → Increase/Multiply Qty = ON, Type = Increase, Quantity = 1  
* "master SL 50000" → Sqroff by Master TP SL = ON, Master SL = 50000  
* "master target 10000" → Sqroff by Master TP SL = ON, Master Target = 10000  
* "trail master SL after 5000 profit, move 2000" → Trail SL = ON, Profit Move = 5000, SL Move = 2000  
* "auto rollover" → Auto Rollover = ON (only if Positional)  
* "rollover 1 day before expiry at 2:30" → Rollover Before Expiry Days = 1, Rollover Time = 14:30  
* "add hedge leg NIFTY FUT" → Add Hedge Leg = ON, sub Symbol = NIFTY FUT NEAR MONTHLY  
* "market jump handling" → Calculate Qty on Market Jump = ON

---

## **F. Identify Quantity Logic**

* "1 lot" → lot = 1  
* "2 lots per step" → lot = 2  
* "start with 2 lots" → scalping\_opening\_qty = 2  
* "increase by 1 each step" → Increase/Multiply = ON, Type = Increase, Quantity = 1  
* "multiply by 2 each step" → Increase/Multiply = ON, Type = Multiply, Quantity = 2

---

# **4️⃣ WHEN COPILOT MUST ASK CLARIFYING QUESTIONS**

Only when **critical information is missing**:

1. Underlying symbol not specified  
2. Segment unclear (futures, options, or stock?)  
3. Average value not mentioned  
4. Jobbing Side unclear (BUY or SELL?)  
5. Trading Type unclear (Intraday or Positional?)  
6. For Master TP/SL: values not mentioned but user seems to expect exit control

**Example clarifying questions:**

* "Which instrument should this strategy trade — BANKNIFTY futures, options, or something else?"  
* "Should this be a BUY averaging or SELL averaging strategy?"  
* "What should the Average distance be — in Points or Percentage?"  
* "Should this be Intraday (close at end of day) or Positional (carry forward)?"

---

# **5️⃣ WHEN NOT TO ASK QUESTIONS**

If information can be **reasonably inferred**:

* "scalping" / "jobbing" → Rapid Execution Scalper, BUY side unless stated otherwise  
* No expiry mentioned for FUT → MONTHLY, NEAR  
* No timing → Default Start 09:20, End 15:00  
* No lot size → 1 lot  
* No product → MIS for Intraday, NRML for Positional  
* "max steps" without specifying close-all → Sqroff on max avg. steps = False  
* "positional with rollover" → Auto Rollover = ON, Rollover Before Expiry Days = 1 (default)

---

# **6️⃣ OUTPUT FORMAT COPILOT MUST FOLLOW**

Every Copilot output must generate:

### **✔ A full Rapid Execution Scalper configuration**

* Tab 1 (Main)  
* Tab 2 (Advance — all relevant fields with enabled checkboxes described)  
* Tab 3 (Description)

### **✔ MUST NOT ADD INDICATOR OR SIGNAL CONFIGURATION**

This plugin has no indicator engine, no chart type, no timeframe, no signal direction. Never add these.

### **✔ MUST ALWAYS ENSURE AVERAGE > 0**

If user provides Average = 0 or omits it, Copilot must flag it and request a value or apply a reasonable default (e.g., 100 Points for index futures, 1 Point for currency).

---

# **7️⃣ RULES FOR MAPPING USER PROMPTS TO PLUGIN FIELDS**

---

## **A. Instrument Mapping**

| User Phrase | Plugin Mapping |
| :---- | :---- |
| "BankNifty futures" | main\_segment=FUT, main\_symbol=BANKNIFTY, main\_expiry=MONTHLY |
| "Nifty weekly CE ATM" | main\_segment=OPT, main\_symbol=NIFTY, main\_expiry=WEEKLY, atm=0, option\_type=CE |
| "Silver MCX" | main\_exchange=MCX, main\_segment=FUT, main\_symbol=SILVER |
| "USDINR BUY scalping" | main\_exchange=CDS, main\_symbol=USDINR, jobbing\_side=BUY |
| "RELIANCE stock positional" | main\_segment=Stock, main\_exchange=NSE, main\_symbol=RELIANCE, is\_intraday=false |

---

## **B. Average and Target Mapping**

| User Phrase | Plugin Mapping |
| :---- | :---- |
| "100-point average" | average\_value=100, average\_by=Point |
| "1% average" | average\_value=1, average\_by=Percentage |
| "target 100 points per step" | target=100, target\_by=Point |
| "no per-step target" | target=0 |
| "target same as average" | target=average\_value, target\_by=average\_by |

---

## **C. Exit Mapping**

| User Phrase | Plugin Mapping |
| :---- | :---- |
| "master SL 50,000" | reset\_cycle\_by\_master\_tpsl=true, master\_sl\_money=50000 |
| "master target 10,000" | reset\_cycle\_by\_master\_tpsl=true, master\_tp\_money=10000 |
| "trail SL after 5000 profit, move 2000" | is\_trail\_sl=true, profit\_move=5000, sl\_move=2000 |
| "close all when max steps reached" | sqroff\_on\_maximum\_steps=true |
| "end trading at 3:15" | intraday\_exit\_time=15:15 |
| "start trading at 9:20" | intraday\_entry\_time=09:20 |

---

## **D. Quantity Mapping**

| User Phrase | Plugin Mapping |
| :---- | :---- |
| "1 lot" | lot=1 |
| "2 lots per step" | lot=2 |
| "start with 3 lots, then 1 each" | scalping\_opening\_qty=3, lot=1 |
| "double qty each step" | increase\_qty\_on\_avg=true, increase\_qty\_type=Multiply, increase\_qty=2 |
| "add 1 lot each step" | increase\_qty\_on\_avg=true, increase\_qty\_type=Increase, increase\_qty=1 |

---

## **E. Rollover and Hedge Mapping**

| User Phrase | Plugin Mapping |
| :---- | :---- |
| "auto rollover" | is\_auto\_rollover=true (Positional only) |
| "rollover 1 day before expiry at 2:30 PM" | rollover\_before\_days=1, rollover\_time=14:30 |
| "add NIFTY FUT as hedge" | is\_add\_hedge\_leg=true, sub\[\] = NIFTY FUT NEAR MONTHLY |
| "hedge with BANKNIFTY PE" | is\_add\_hedge\_leg=true, sub\[\] = BANKNIFTY OPT NEAR WEEKLY, option\_type=PE |

---

# **8️⃣ COPILOT MUST ALWAYS CHECK VALIDATIONS BEFORE OUTPUT**

* Average must be > 0 — flag and correct if 0 or missing  
* Lot/Qty must be > 0 — flag if 0  
* Maximum Avg. Steps must be ≥ 1 — set reasonable default (e.g., 10–50)  
* Master SL and Master Target must be ≥ 0 (0 = disabled)  
* Trail SL sub-fields must be ≥ 0  
* Trail SL requires Sqroff by Master TP SL to be enabled  
* Auto Rollover requires Trading Type = Positional  
* ATM and Option Type only for OPT segment  
* Jobbing End Time must be after Jobbing Start Time  
* Jobbing Start Price must be ≥ 0 (0 = start immediately)  
* Rollover Time must be within market hours

If invalid → Copilot must correct or ask user.

---

# **9️⃣ HOW COPILOT MUST RESPOND FOR SAMPLE PROMPTS**

---

### **Example 1**

**User:** "Create a BankNifty intraday BUY scalping with 100-point average, 100-point target, max 10 steps, Master SL ₹50,000."

**Copilot must output:**

* Main: BANKNIFTY FUT NEAR MONTHLY, Lot = 1, Trading Type = Intraday, Product = MIS, Jobbing Start Time = 09:20, Jobbing End Time = 15:00, Jobbing Side = BUY, Average = 100 (Point), Target = 100 (Point)  
* Advance: Maximum Avg. Steps = 10, Sqroff by Master TP SL = ON, Master Target = 0, Master SL = 50000  
* No clarifying questions needed

---

### **Example 2**

**User:** "USDINR sell scalping, 5-paise average, double quantity each step, max 8 steps, close all when limit hit."

**Copilot must output:**

* Main: CDS, USDINR FUT NEAR MONTHLY, Jobbing Side = SELL, Average = 5 (Point), Target = 5 (Point) (assumed same as average — clarify if needed)  
* Advance: Maximum Avg. Steps = 8, Sqroff on max avg. steps = ON, Increase/Multiply Qty = ON, Type = Multiply, Quantity = 2  
* No clarifying questions on instrument; ask: "What should the per-step Target be?"

---

### **Example 3**

**User:** "Positional silver MCX jobbing, 100-point average, auto rollover 1 day before expiry, master SL 1 lakh, trail SL after 20,000 profit."

**Copilot must output:**

* Main: MCX, SILVER FUT NEAR MONTHLY, Trading Type = Positional, Product = NRML, Jobbing Side = BUY, Average = 100 (Point)  
* Advance: Auto Rollover = ON, Rollover Before Expiry Days = 1, Rollover Time = 14:29 (default), Sqroff by Master TP SL = ON, Master SL = 100000, Trail SL = ON, Profit Move = 20000, SL Move = (ask or default 10000)

---

### **Example 4**

**User:** "BankNifty buy scalping with hedge NIFTY FUT."

**Copilot must output:**

* Main: BANKNIFTY FUT NEAR MONTHLY, Jobbing Side = BUY  
* Advance: Add Hedge Leg = ON, Symbol = NIFTY FUT NEAR MONTHLY  
* Ask: "What should the Average distance be? What is the per-step Target? Should this be Intraday or Positional?"

---

# **🔟 COPILOT MUST ALWAYS INCLUDE DESCRIPTION TAB**

Copilot must generate:

**Short Description**  
A one-line summary of the strategy's instrument, side, average interval, and trading type.

**Long Description**  
Human-readable explanation of the averaging logic, target per step, advance safety features, and any special configurations (rollover, hedge leg, master TP/SL).

---

# **1️⃣1️⃣ WHAT COPILOT MUST NEVER DO**

❌ Never set Average = 0 — it is invalid and must always be a positive number  
❌ Never set Lot/Qty = 0 — must be a positive number  
❌ Never enable Trail SL without enabling Sqroff by Master TP SL first  
❌ Never enable Auto Rollover for Intraday mode  
❌ Never configure TP/SL for the hedge leg — it has no independent TP/SL  
❌ Never add indicator, chart type, timeframe, or signal direction — this plugin has none  
❌ Never set ATM or Option Type for FUT or Stock legs  
❌ Never set Jobbing End Time before Jobbing Start Time  
❌ Never add non-existent fields to the configuration

---

# **1️⃣2️⃣ AI RULE: USE SAFEST DEFAULTS WHEN USER IS UNCLEAR**

Defaults Copilot should use when user does not specify:

* Trading Type: Intraday  
* Product: MIS (Intraday), NRML (Positional)  
* Jobbing Side: BUY  
* Jobbing Start Time: 09:20  
* Jobbing End Time: 15:00  
* Average By: Point  
* Target By: Point  
* Target: same as Average value  
* Lot: 1  
* Maximum Avg. Steps: 10  
* Maximum Target Steps: 0 (no limit)  
* Reset Cycle on Positive MTM: 0 (disabled)  
* Required Margin: 1  
* Opening Qty/Lot: 0 (uses base Lot/Qty)  
* Increase/Multiply Qty: Off  
* Sqroff on max avg. steps: Off  
* Calculate Qty on Market Jump: Off  
* Sqroff by Master TP SL: Off (unless user specifies SL or TP)  
* Trail SL: Off  
* Auto Rollover: Off  
* Add Hedge Leg: Off  
* Contract: NEAR  
* Expiry: MONTHLY for FUT; WEEKLY for index OPT  
* Rollover Before Expiry Days: 1  
* Rollover Time: 14:29  
* Jobbing Start Price: 0 (start immediately)  
* Jobbing End Price: 0 (no boundary)

---

# **1️⃣3️⃣ INTERNAL COPILOT DECISION PRIORITY TREE**

1. Identify trading instrument (exchange, segment, symbol, contract, expiry)  
2. Determine jobbing side (BUY / SELL)  
3. Set Average value and unit (Points or %)  
4. Set per-step Target value and unit  
5. Determine Trading Type (Intraday / Positional)  
6. Set Jobbing Start Time and End Time  
7. Set Lot/Qty and Opening Qty if mentioned  
8. Configure Increase/Multiply Qty if mentioned  
9. Set Maximum Avg. Steps and Maximum Target Steps  
10. Configure Jobbing Start Price and End Price if mentioned  
11. Enable Sqroff by Master TP SL with Master Target and Master SL if mentioned  
12. Configure Trail SL if mentioned (requires Master TP SL enabled)  
13. Enable Reset Cycle on Positive MTM if mentioned  
14. Enable Calculate Qty on Market Jump if mentioned  
15. Enable Sqroff on max avg. steps if mentioned  
16. Enable Auto Rollover with Rollover Days and Time if Positional and mentioned  
17. Add Hedge Leg with symbol if mentioned  
18. Set product type and Exit Order Product Type  
19. Apply all defaults  
20. Validate all fields (especially Average > 0, Lot/Qty > 0, Trail SL only with Master TP SL)  
21. Generate complete configuration

---

# **1️⃣4️⃣ FINAL COPILOT OUTPUT STRUCTURE**

Copilot should output:

1. **Summary of recognized intent** (instrument, side, average logic, trading mode)  
2. **Main Tab configuration** (Strategy Name, Symbol, Lot/Qty, Trading Type, Product, Jobbing Start Time, End Time, Jobbing Side, Average By, Average, Target By, Target)  
3. **Advance Tab configuration** (all enabled features with sub-fields fully described)  
4. **Short Description + Long Description**  
5. **Optional refinement questions** ("Should I enable Master SL for safety?", "Do you want to multiply quantity at each step?", "Should I add Auto Rollover since this is positional?")

---

# API Reference

## **Strategy Creation**

**Endpoint:** `POST https://api.marketmaya.com/api/mainStrategy/createScalpingStrategy`  
**Authentication:** Bearer JWT token  
**Content-Type:** application/json

## **Full Payload Structure**

```json
{
  "id": "",
  "strategy_name": "Strategy Name",
  "short_description": "",
  "long_description": "",
  "strategy_id": "YioJhK5IqBULe8fPLMnXaAaC0$aC0$",
  "mix_name": "BANKNIFTY FUT NEAR MONTHLY",
  "main_exchange": "NFO",
  "main_segment": "FUT",
  "main_symbol": "BANKNIFTY",
  "main_contract": "NEAR",
  "main_expiry": "MONTHLY",
  "product_type": "MIS",
  "exit_order_product_type": "",
  "qty_type": "Qty",
  "qty": 30,
  "lot": 1,
  "atm": 0,
  "strike_price": 0,
  "option_type": "",
  "intraday_entry_time": "09:20",
  "intraday_exit_time": "15:00",
  "is_intraday": true,
  "jobbing_side": "BUY",
  "jobbing_start_price": 0,
  "jobbing_end_price": 0,
  "average_by": "Point",
  "average_value": 100,
  "target_by": "Point",
  "target": 100,
  "intraday_target": 0,
  "maximum_steps": 10,
  "maximum_target_steps": 0,
  "sqroff_on_maximum_steps": false,
  "calculate_qty_on_market_jump": false,
  "allow_update_parameters": true,
  "order_type": "Market Order",
  "no_of_limit_order_retry": 0,
  "retry_at_every_seconds": 0,
  "market_order_after_retry": false,
  "reset_cycle_by_master_tpsl": false,
  "master_tp_money": 0,
  "master_sl_money": 0,
  "is_trail_sl": false,
  "profit_move": 0,
  "sl_move": 0,
  "no_of_trail_sl": 0,
  "rollover_before_days": 0,
  "is_auto_rollover": false,
  "rollover_time": "0:0",
  "is_add_hedge_leg": false,
  "reset_cycle_on_positive_mtm": 0,
  "required_margin": 1,
  "scalping_opening_qty": 0,
  "increase_qty_on_avg": false,
  "increase_qty": 1,
  "increase_qty_type": "Increase",
  "rebacktest": false,
  "effect_all_sub_strategies": false,
  "sub": [
    {
      "call_type": "BUY",
      "exchange": "NFO",
      "segment": "FUT",
      "symbol": "BANKNIFTY",
      "contract": "NEAR",
      "expiry": "MONTHLY",
      "atm": 0,
      "option_type": "",
      "qty": 0,
      "lot": 1,
      "trade_side": "BUY",
      "target": 0,
      "target_by": "Money",
      "sl": 0,
      "sl_by": "Money",
      "trail_sl_market_move": 0,
      "trail_sl_move": 0,
      "no_of_time_trail_sl": 0,
      "is_trail_sl": false,
      "is_reverse_signal": false
    }
  ]
}
```

## **API Field Reference Table**

| UI Field | DB / API Field | Type | Notes |
|---|---|---|---|
| Strategy Name | strategy\_name | string | Required, unique |
| Symbol (resolved display) | mix\_name | string | Auto-generated concatenated name |
| Exchange | main\_exchange | string | NSE/NFO/BFO/BSE/MCX/CDS |
| Segment | main\_segment | string | FUT / OPT / Stock |
| Symbol | main\_symbol | string | |
| Contract | main\_contract | string | NEAR / NEXT / FAR |
| Expiry | main\_expiry | string | MONTHLY / WEEKLY |
| ATM | atm | integer | 0 = ATM; OPT only |
| Option Type | option\_type | string | CE / PE / "" |
| Strike Price | strike\_price | number | 0 = use ATM |
| Lot/Qty (lots) | lot | number | Number of lots |
| Lot/Qty (qty) | qty | number | Actual quantity = lot × lot size |
| Lot/Qty type | qty\_type | string | "Lot" or "Qty" |
| Trading Type | is\_intraday | boolean | true = Intraday |
| Product | product\_type | string | MIS / NRML / CNC / MTF |
| Jobbing Start Time | intraday\_entry\_time | string | HH:MM format |
| Jobbing End Time | intraday\_exit\_time | string | HH:MM format |
| Jobbing Side | jobbing\_side | string | BUY / SELL |
| Average By | average\_by | string | Point / Percentage |
| Average | average\_value | number | Must be > 0 |
| Target By | target\_by | string | Point / Percentage |
| Target (per-step) | target | number | 0 = disabled |
| Master target (Intraday/Positional) | intraday\_target | number | Strategy-level target reference |
| Jobbing Start Price | jobbing\_start\_price | number | 0 = start immediately |
| Jobbing End Price | jobbing\_end\_price | number | 0 = no boundary |
| Maximum Avg. Steps | maximum\_steps | number | |
| Maximum Target Steps | maximum\_target\_steps | number | 0 = no limit |
| Reset Cycle after Steps on Positive MTM | reset\_cycle\_on\_positive\_mtm | number | 0 = disabled |
| Required Margin | required\_margin | number | Informational |
| Exit Order Product Type | exit\_order\_product\_type | string | MIS / NRML / CNC / MTF / "" |
| Opening Qty/Lot | scalping\_opening\_qty | number | 0 = use base Lot/Qty |
| Increase/Multiply Qty on Average | increase\_qty\_on\_avg | boolean | |
| Quantity (Increase/Multiply) | increase\_qty | number | |
| Type (Increase/Multiply) | increase\_qty\_type | string | Increase / Multiply |
| Sqroff on max avg. steps | sqroff\_on\_maximum\_steps | boolean | |
| Calculate Qty on Market Jump | calculate\_qty\_on\_market\_jump | boolean | |
| Sqroff by Master TP SL | reset\_cycle\_by\_master\_tpsl | boolean | |
| Master Target (Money) | master\_tp\_money | number | |
| Master SL (Money) | master\_sl\_money | number | |
| Trail SL? | is\_trail\_sl | boolean | |
| Profit Move | profit\_move | number | |
| SL Move | sl\_move | number | |
| No of Trail SL | no\_of\_trail\_sl | number | 0 = unlimited |
| Auto Rollover | is\_auto\_rollover | boolean | Positional only |
| Rollover Before Expiry Days | rollover\_before\_days | number | |
| Rollover Time | rollover\_time | string | HH:MM format |
| Add Hedge Leg | is\_add\_hedge\_leg | boolean | |
| Short Description | short\_description | string | Optional |
| Long Description | long\_description | string | Optional |
| Strategy Type (fixed) | strategy\_id | string | Fixed scalper identifier |
| — | order\_type | string | Always "Market Order" (API default) |
| — | allow\_update\_parameters | boolean | Always true |
| — | effect\_all\_sub\_strategies | boolean | Advanced bulk update |
| — | rebacktest | boolean | Internal flag |
| Hedge Leg: Exchange | sub\[\].exchange | string | |
| Hedge Leg: Segment | sub\[\].segment | string | FUT / OPT / Stock |
| Hedge Leg: Symbol | sub\[\].symbol | string | |
| Hedge Leg: Contract | sub\[\].contract | string | NEAR / NEXT / FAR |
| Hedge Leg: Expiry | sub\[\].expiry | string | MONTHLY / WEEKLY |
| Hedge Leg: ATM | sub\[\].atm | integer | 0 = ATM |
| Hedge Leg: Option Type | sub\[\].option\_type | string | CE / PE / "" |
| Hedge Leg: Call Type | sub\[\].call\_type | string | BUY (follows main side) |
| Hedge Leg: Trade Side | sub\[\].trade\_side | string | BUY / SELL |
| Hedge Leg: Lot | sub\[\].lot | number | |
| Hedge Leg: Qty | sub\[\].qty | number | |
