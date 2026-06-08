# Overview

**MM \- Inbound Signal Bridge**  
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date: 25-05-2026  
Prepared By: Aditya Vadodariya

# PLUGIN SUMMARY

# **✅ 1\. BRD VERSION (Formal, Precise, Functional Definition)**

## **Inbound Signal Bridge Plugin – Product Overview**

**Inbound Signal Bridge** is an externally-triggered, multi-symbol automated trade execution plugin that receives inbound signals from external sources — such as TradingView alerts, Pine Script webhooks, third-party signal providers, or custom trading systems — and bridges those signals directly into real broker orders across one or more configured instrument legs.

Unlike the Indicator Signal Engine (which generates signals internally using built-in indicators) or the Unified Strategy Builder (which triggers entries by time, price ranges, or premium conditions), the Inbound Signal Bridge has **no internal signal generation engine**. It acts purely as a reception and execution layer: when an external signal arrives for a strategy, the plugin executes all configured symbol legs simultaneously according to the pre-configured quantity, target, stoploss, and trailing rules.

The plugin supports **multi-symbol execution**, where multiple instruments (Futures, Options, Stocks — across any exchange and segment) are linked to the same strategy and all execute when a single inbound signal is received. Each symbol leg is independently configured with its own instrument details, quantity distribution method, target, stoploss, and stoploss trailing.

A core capability of this plugin is its **four dynamic quantity distribution methods** — Fix, Capital(%), Capital Risk(%), and Allocation Method 1 — which allow position sizing to be driven by available portfolio capital, risk parameters, and capital allocation rules rather than fixed lot counts alone.

The plugin provides **master-level exit controls** including Master Target and Master SL (both configurable by Money or Capital %), with safety controls such as Sqroff All Legs on single leg exit, Sqroff on Rejection, and Auto Sqroff on Contract Expiry.

**Strategy Type ID (API):** `XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$`  
**API Endpoint:** `POST https://api.marketmaya.com/api/mainStrategy/createCustomTradeStrategy`

---

## **Key Capabilities**

* Receive external signals (webhooks, alerts) and execute trades automatically without any internal indicator computation.  
* Configure **unlimited symbol legs**, each independently mapped to any instrument (FUT, OPT, Stock) across any supported exchange.  
* Support **four Qty Distribution methods**: Fix, Capital(%), Capital Risk(%), and Allocation Method 1 — enabling capital-proportional and risk-adjusted position sizing.  
* Define **per-leg Target and SL** (Money type) with independent stoploss trailing per leg.  
* Define **Master Target and Master SL** at strategy level to control combined portfolio exit.  
* Restrict entry to selected **working days** (Monday through Sunday).  
* Set **intraday exit** in minutes before market close, not a fixed clock time.  
* Enable **Auto Sqroff on Contract Expiry** to prevent holding expired contracts.  
* Control **Max Position** to cap simultaneous open symbol positions.  
* Control **Max Capital Allocation(%)** to cap per-symbol capital usage.  
* Safety: Sqroff All Legs on any single TP/SL hit, Sqroff on Rejection, parameter update controls.  
* Use **Templates** and **Import Template** for fast strategy replication.

The plugin supports a wide range of use cases including:

* TradingView alert-driven execution across multiple symbols  
* PMS (Portfolio Management Service) signal-based order routing  
* Multi-symbol basket execution on a single external trigger  
* Risk-adjusted position sizing using capital-proportional methods  
* Automated hedging using signal-driven CE and PE legs  
* Stock and futures portfolio rebalancing via external signals  
* Cross-exchange multi-leg execution from a single inbound call

---

## **Primary Objective**

To provide a **fully automated, externally-driven** trade execution engine that converts inbound signals from any external source into real broker orders across multiple instrument legs, with complete position sizing flexibility, leg-level exit controls, and strategy-level risk management.

---

# **✅ 2\. COPILOT VERSION (AI-Optimized, Natural Language, Training Input)**

**Inbound Signal Bridge is a multi-symbol, externally-triggered automated trade execution plugin** that fires real broker orders when an external signal is received — from TradingView, Pine Script, custom alert systems, or any webhook-capable signal source.

Copilot should understand that:

* This plugin does NOT compute indicators or signals internally. It only receives and executes.  
* Each strategy has one or more symbol legs. All active legs execute simultaneously when an inbound signal arrives.  
* Quantity can be fixed (lots) or dynamically calculated using Capital(%), Capital Risk(%), or Allocation Method 1.  
* Each leg has its own Target, SL, and Trail SL configured independently.  
* Master Target and Master SL operate on the combined P\&L of all legs.  
* Intraday exit is defined in minutes before market close (not a fixed time).  
* Working days includes all seven days (Mon–Sun).  
* The `main_strategy_parameter_id` field on a sub-strategy links it to another sub-strategy's parameters — this is an advanced cross-strategy linking feature.

When a user asks Copilot to "create an inbound signal strategy," Copilot should:

1. Identify the instruments (symbols, segments, exchanges) to trade.  
2. Select quantity distribution method and configure qty/lots.  
3. Configure per-leg Target, SL, and Trail SL if required.  
4. Set Master Target and Master SL if mentioned.  
5. Set working days and exit time.  
6. Enable safety features (Sqroff All Legs, Auto Sqroff on Expiry) if appropriate.  
7. Map all inputs into valid plugin fields.

Copilot should treat Inbound Signal Bridge as the plugin for **externally-triggered, signal-reception-based, multi-symbol execution strategies**.

---

# **✅ 3\. SHORT PLUGIN CARD SUMMARY (To display on homepage)**

### **Inbound Signal Bridge**

Bridge external signals (TradingView, webhooks, alert systems) directly to multi-symbol broker execution.  
Configure instrument legs with dynamic qty sizing, per-leg TP/SL, master exit controls, and capital allocation rules — no internal indicators required.

---

# Parameter Description

# Main Parameters

### **1\. Strategy Name**

**Description:** User-defined name of the strategy. Shown in UI and used for identification.  
**Logic:** Does not affect execution. Only used for listing, search, copy/duplicate, and Copilot reference.  
**Type:** String  
**Default Value:** Blank ("")  
**Validation:**

- Required  
- Must be unique per user  
- Minimum length 3, maximum 100 characters  
- Cannot include unsupported special characters

**Example:** "BNF Weekly Hedge – TradingView Signal"  
**DB Field Name:** strategy\_name  
**Execution Context:** Used only by UI and Copilot to reference the strategy. Trading Server ignores this value.  
---

### **2\. Capital**

**Description:** Total portfolio capital assigned to this strategy. Used as the reference base for dynamic quantity calculation methods.  
**Logic:** This value acts as the "available capital" denominator in Capital(%), Capital Risk(%), and Allocation Method 1 quantity distribution formulas. It represents the trader's intended capital deployment for this strategy. If set to 0, dynamic qty methods reference account-level available capital at runtime.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 500000  
**DB Field Name:** required\_margin  
**Execution Context:** Stored as `required_margin` in the API and referenced by the trading engine at runtime when computing position size dynamically for Capital(%), Capital Risk(%), and Allocation Method 1 distribution types. When set to 0, the engine falls back to the account's live available capital.  

**Note:** In the Unified Strategy Builder and Indicator Signal Engine plugins, `required_margin` is purely informational (user's estimated margin). In Inbound Signal Bridge, it doubles as the **Capital base** for dynamic qty formulas — so it carries both an informational and a computational role.  
---

### **3\. Trading Type**

**Description:** Select whether the strategy is Intraday or Positional.  
**Logic:**

* Intraday → Positions are closed a defined number of minutes before market close (configured in Advance tab).  
* Positional → Positions carry forward until natural exit conditions (Target/SL), contract expiry, or pre-expiry sqroff.

**Type:** String (Dropdown)  
**Default Value:** Positional  
**Validation:** Must be "Intraday" or "Positional"  
**Example:** Intraday  
**DB Field Name:** is\_intraday (false \= Positional, true \= Intraday)  
**Execution Context:** Controls when and how open legs are force-squared off at end of session.  
---

### **4\. Product**

**Description:** Select the order product type to use for all legs in this strategy.  
**Logic:** Included in every order request to the broker during execution.  
**Type:** String (Dropdown)  
**Default Value:** NRML  
**Validation:** Allowed Values:

- MIS  
- NRML  
- CNC

**Example:** NRML  
**DB Field Name:** product\_type  
**Execution Context:** Trading Server uses this product type when placing all orders for this strategy.  
---

### **5\. Master Target**

**Description:** Define the overall combined target profit for the strategy.  
**Logic:** When the total combined MTM profit of all active legs reaches or exceeds this value, all legs are squared off and no new positions are accepted until the strategy is reset. Set to 0 to disable.  
**Type:** Number with type toggle (M \= Money)  
**Default Value:** 0  
**Validation:**

* Must be 0 or a positive number  
* 0 means no master target

**Example:** 5000  
**DB Field Name:** intraday\_target (numeric value); target\_by (type: "Money" or "Capital(%)")  
**Execution Context:** Trading Server monitors combined P\&L of all legs continuously and triggers full strategy exit when this threshold is reached.  

**Note:** The "M" toggle displayed next to the field indicates the current type (M \= Money). The `target_by` field in the API stores this type. Currently supported value: "Money".  
---

### **6\. Master SL**

**Description:** Define the overall combined stoploss for the strategy.  
**Logic:** When the total combined MTM loss of all active legs reaches or exceeds this value, all legs are squared off and no new positions are accepted until the strategy is reset. Set to 0 to disable.  
**Type:** Number with type toggle (M \= Money)  
**Default Value:** 0  
**Validation:**

* Must be 0 or a positive number  
* 0 means no master SL

**Example:** 3000  
**DB Field Name:** intraday\_sl (numeric value); sl\_by (type: "Money" or "Capital(%)")  
**Execution Context:** Trading Server continuously monitors combined loss and sqroffs all legs when this threshold is breached.  

**Note:** Same toggle behavior as Master Target. The `sl_by` field stores type.  
---

### **7\. Max Position**

**Description:** Maximum number of simultaneous open symbol positions allowed in this strategy.  
**Logic:** Once the number of open positions equals this value, any new inbound signal for an additional symbol will be rejected. Set to 0 to disable the limit (unlimited positions allowed).  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive integer. 0 \= no limit.  
**Example:** 8  
**DB Field Name:** max\_position  
**Execution Context:** Trading Server checks current open position count before accepting any new inbound signal. If count \>= Max Position, signal is rejected.  

**Example:** If 10 symbols are configured in the strategy and Max Position \= 8, the system will accept the first 8 signal calls and reject the 9th and 10th.  
---

### **8\. Max Capital Allocation(%)**

**Description:** Define the maximum percentage of total capital that can be allocated to any single symbol in this strategy.  
**Logic:** This cap is applied when any symbol leg uses "Capital Risk(%)" as its Qty Distribution method. If a symbol's calculated capital requirement exceeds this percentage of total capital, the system clips the allocation to this cap.  
**Type:** Number (Percentage)  
**Default Value:** 100  
**Validation:**

* Must be a positive number  
* 1–100 (percentage)  
* Relevant only when any leg uses Capital Risk(%) distribution

**Example:** 10 (each symbol can use maximum 10% of total capital)  
**DB Field Name:** max\_position\_allocation\_percent  
**Execution Context:** Applied at qty calculation time when Capital Risk(%) distribution is active. Prevents over-concentration in any single symbol.  

---

# Symbols Parameters

Each symbol entry represents one instrument leg. Multiple symbols can be added. Each is configured and executed independently when a signal arrives.

### **1\. Symbol**

**Description:** The trading instrument assigned to this leg. Clicking the Symbol field opens the "Select Symbol" dialog where full instrument details are configured.  
**Logic:** The resolved symbol is displayed as a concatenated string: Symbol \+ Segment \+ Contract \+ Expiry \+ ATM \+ Option Type (e.g., "BANKNIFTY FUT NEAR MONTHLY" or "NIFTY OPT NEAR WEEKLY 0 CE"). The resolved actual trading symbol and expiry date are shown at the bottom of the dialog before confirming.  
**Type:** Composite field (opens dialog)  
**Default Value:** Blank (required)  
**Validation:** Required. A fully resolved symbol must be selected.  
**Example:** BANKNIFTY FUT NEAR MONTHLY  
**DB Field Name:** exchange, segment, symbol, contract, expiry, atm, option\_type (all stored as separate fields in the sub array)  
**Execution Context:** Trading Server uses these fields to identify the exact instrument contract for order placement at execution time.  
---

#### **1.1 Exchange**

**Description:** The exchange for this leg's instrument.  
**Logic:** Controls which segments and symbols are available.  
**Type:** String (Dropdown)  
**Default Value:** NFO  
**Validation:** Allowed Values: NSE, NFO, BFO, BSE, MCX, CDS  
**Example:** NFO  
**DB Field Name:** exchange  
**Execution Context:** Determines which market feed and instrument master is used for this leg.  
---

#### **1.2 Segment**

**Description:** Segment of the leg instrument.  
**Logic:** Determines instrument type. Option Type and ATM fields become active only for OPT segment.  
**Type:** String (Dropdown)  
**Default Value:** FUT  
**Validation:** Allowed Values:

- FUT  
- OPT  
- Stock

**Example:** OPT  
**DB Field Name:** segment  
**Execution Context:** Determines contract type used during instrument resolution and order placement.  
---

#### **1.3 Symbol**

**Description:** The underlying instrument symbol for this leg.  
**Logic:** All available symbols are filtered based on selected Exchange and Segment.  
**Type:** String (Dropdown / Searchable)  
**Default Value:** BANKNIFTY  
**Validation:** Must be a valid symbol for the selected exchange and segment.  
**Example:** NIFTY, RELIANCE, 360ONE  
**DB Field Name:** symbol  
**Execution Context:** Instrument master lookup key used to resolve exact contract.  
---

#### **1.4 Contract**

**Description:** Select the contract series for this leg.  
**Logic:** Determines which contract in the expiry sequence is selected at execution time.  
**Type:** String (Dropdown)  
**Default Value:** NEAR  
**Validation:** Allowed Values:

- NEAR (nearest/current contract)  
- NEXT (next contract in sequence)  
- FAR (far/distant contract)

**Example:** NEAR  
**DB Field Name:** contract  
**Execution Context:** Used with Expiry to resolve the exact contract date when the signal arrives.  
---

#### **1.5 Expiry**

**Description:** Select the expiry type for this leg's contract.  
**Logic:** Resolved dynamically at execution time using the symbol's expiry calendar combined with the Contract selection.  
**Type:** String (Dropdown)  
**Default Value:** MONTHLY  
**Validation:** Allowed Values:

- MONTHLY  
- WEEKLY (shown only if symbol supports weekly expiry contracts)

**Example:** WEEKLY  
**DB Field Name:** expiry  
**Execution Context:** Trading Server resolves to the actual contract expiry date at execution time.  
---

#### **1.6 ATM**

**Description:** Strike offset from At-The-Money for option legs.  
**Logic:** Used only when Segment \= OPT. Defines how many strikes above or below ATM this leg should trade. 0 \= exactly ATM. Positive values move toward OTM for CE / ITM for PE. Negative values move toward ITM for CE / OTM for PE.  
**Type:** Integer  
**Default Value:** 0  
**Validation:**

- Applicable only when Segment \= OPT  
- Must be an integer (positive, negative, or zero)  
- Ignored for FUT and Stock segments

**Example:** 0 (ATM), 1 (one strike OTM for CE), \-1 (one strike ITM for CE)  
**DB Field Name:** atm  
**Execution Context:** Strike resolution engine selects the correct option strike based on this offset at the time the inbound signal triggers execution.  
---

#### **1.7 Option Type**

**Description:** Select CE (Call) or PE (Put) for option legs.  
**Logic:** Active only when Segment \= OPT. Blank and ignored for FUT and Stock.  
**Type:** String (Dropdown)  
**Default Value:** CE  
**Validation:** Allowed Values:

- CE  
- PE  
  Valid only when Segment \= OPT

**Example:** PE  
**DB Field Name:** option\_type  
**Execution Context:** Determines which side of the option chain is used for strike selection.  
---

### **2\. Strike Price**

**Description:** Fixed strike price for options legs when a specific absolute strike is required instead of ATM-relative selection.  
**Logic:** When set to 0, strike selection uses the ATM offset (field 1.6). When set to an actual strike price (e.g., 48000), the system trades that exact strike regardless of ATM position. The Select Symbol dialog resolves the actual trading symbol and expiry date shown before confirmation.  
**Type:** Number  
**Default Value:** 0  
**Validation:**

- Must be 0 or a valid positive strike price  
- 0 means use ATM-relative selection  
- Applicable primarily for OPT segment

**Example:** 0 (use ATM offset), 48000 (fixed strike)  
**DB Field Name:** strike\_price  
**Execution Context:** When non-zero, Trading Server uses this exact strike for the order. When 0, ATM-relative resolution applies.  
---

### **3\. Qty Distribution**

**Description:** Define how the trade quantity is calculated for this leg.  
**Logic:** Four methods are available. The selected method determines which additional quantity sub-field is shown (Lot/Qty or Percentage(%)).  
**Type:** Dropdown  
**Default Value:** Fix  
**Validation:** Allowed Values:

- Fix  
- Capital(%)  
- Capital Risk(%)  
- Allocation Method 1

**Example:** Capital(%)  
**DB Field Name:** qty\_distribution  
**Execution Context:** Trading Server uses this method at signal time to compute the actual order quantity.  
---

#### **3.A Fix**

**Logic:** Trade a fixed quantity per signal. Quantity \= Lot × Contract Lot Size.  
**Sub-field shown:** Lot/Qty  
**DB Field Name:** lot (number of lots), qty (computed quantity)  
**Example:** Lot \= 2 → trades 2 lots of the selected instrument  
---

#### **3.B Capital(%)**

**Logic:** System calculates quantity based on available capital and the configured percentage.  
**Formula:** `Qty = (Available Capital × Percentage%) / Instrument Price`  
**Sub-field shown:** Percentage(%)  
**DB Field Name:** qty (stores the percentage value, e.g., 2 for 2%)  
**Example:** Capital \= ₹5,00,000, Percentage \= 2% → Qty \= (500000 × 2/100) / instrument price  
---

#### **3.C Capital Risk(%)**

**Logic:** System calculates quantity based on available capital, the configured risk percentage, and the symbol's SL value.  
**Formula:**  
`Risk Capital = Available Capital × Percentage%`  
`Qty = Risk Capital / SL`  
**Sub-field shown:** Percentage(%)  
**DB Field Name:** qty (stores the percentage value)  
**Example:** Capital \= ₹5,00,000, Risk \= 20%, SL \= ₹1,000 → Risk Capital \= ₹1,00,000 → Qty \= 100  
**Note:** Max Capital Allocation(%) cap applies to this method.  
---

#### **3.D Allocation Method 1**

**Logic:** System allocates capital equally across all available open position slots and calculates quantity from the per-slot allocation.  
**Formula:**  
`Free Margin per Symbol = Available Capital / Available Positions`  
`Qty = Free Margin per Symbol / Instrument Price`  
**Sub-field shown:** Lot/Qty (informational)  
**DB Field Name:** qty (computed)  
**Example:** Total Capital \= ₹5,00,000, Available Capital \= ₹2,00,000, Available Positions \= 5 → Free Margin \= ₹40,000 → Qty \= 40,000 / price  
---

### **4\. Lot/Qty**

**Description:** Number of lots (for Fix and Allocation Method 1) or the percentage value (for Capital(%) and Capital Risk(%)).  
**Logic:** Field label and meaning changes based on selected Qty Distribution. For Fix: number of lots. For Capital(%) and Capital Risk(%): percentage value used in the formula.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be a positive number  
**Example:** 1 (for Fix, 1 lot); 2 (for Capital(%), 2% of capital)  
**DB Field Name:** lot (for Fix-based lots); qty (for percentage-based and computed qty)  
**Execution Context:** Used by qty calculation engine at signal time.  
---

### **5\. Target**

**Description:** Define the profit target value for this leg (Money type).  
**Logic:** When this leg's profit reaches this value, the leg is squared off. 0 \= no target for this leg.  
**Type:** Number with M type toggle  
**Default Value:** 0  
**Validation:** Must be \>= 0. 0 means no target.  
**Example:** 2500  
**DB Field Name:** target (numeric); target\_by (type: "Money")  
**Execution Context:** Trading Server monitors this leg's P\&L and exits when target is reached.  
---

### **6\. SL**

**Description:** Define the stoploss value for this leg (Money type).  
**Logic:** When this leg's loss reaches this value, the leg is squared off. 0 \= no stoploss for this leg.  
**Type:** Number with M type toggle  
**Default Value:** 0  
**Validation:** Must be \>= 0. 0 means no SL.  
**Example:** 1500  
**DB Field Name:** sl (numeric); sl\_by (type: "Money")  
**Execution Context:** Triggers leg square-off when loss hits this value.  
---

### **7\. Trail SL**

**Description:** Enable stoploss trailing for this leg.  
**Logic:** When enabled (checkbox ticked), the stoploss is dynamically tightened as the leg's profit increases. Three sub-fields become active. When all sub-fields are 0, trailing does not activate even if checkbox is ON.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** is\_trail\_sl  
**Execution Context:** Activates dynamic SL adjustment for this leg.  
---

#### **7.1 Market Move (Points)**

**Description:** The profit increase in points required to trigger one SL trailing step.  
**Logic:** Once this leg's profit increases by this amount from the last trail level, the SL is shifted by the configured SL Move amount.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0. 0 means trailing does not activate.  
**Example:** 1500  
**DB Field Name:** trail\_sl\_market\_move  
**Execution Context:** Profit movement trigger for SL trailing. Each time this threshold is crossed, SL moves.  
---

#### **7.2 SL Move (Points)**

**Description:** The amount in points by which the SL is moved on each trail step.  
**Logic:** Each time profit increases by "Market Move (Points)", the SL is shifted by this many points closer to the current price, locking in more profit.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 500  
**DB Field Name:** trail\_sl\_move  
**Execution Context:** Determines the size of each SL trailing adjustment.  
---

#### **7.3 No of Trail SL**

**Description:** Maximum number of times the SL can trail for this leg.  
**Logic:** After this many trailing steps, no further SL adjustments are made. 0 \= unlimited trailing.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0. 0 means unlimited.  
**Example:** 5  
**DB Field Name:** no\_of\_time\_trail\_sl  
**Execution Context:** Limits total number of trailing operations on this leg's SL.  
---

### **8\. Copy (Icon)**

**Description:** Duplicates this symbol leg row with identical settings.  
**Logic:** Creates a new sub-strategy entry pre-filled with all values from the current leg. User can then modify the duplicate to configure a different instrument or qty.  
**Type:** UI Action (Icon)  
**DB Field Name:** (UI only — triggers creation of a new sub-strategy object)  
**Execution Context:** Not an execution parameter. Used for rapid multi-leg setup.  
---

### **9\. Add (+)**

**Description:** Adds a new blank symbol leg row.  
**Logic:** Creates an empty sub-strategy entry for configuration.  
**Type:** UI Action (Button)  
**DB Field Name:** (UI only)  
**Execution Context:** Not an execution parameter. Used to build multi-symbol strategies.  
---

### **🔒 Hidden Field: main\_strategy\_parameter\_id**

**Description:** Links this sub-strategy to another sub-strategy's parameter set, enabling cross-strategy parameter inheritance or conditional execution dependency.  
**Logic:** When empty (""), this leg operates fully independently. When set to another sub-strategy's ID, this leg is linked to that sub-strategy. This is used in advanced PMS or portfolio configurations where one symbol's execution depends on or mirrors parameters of another symbol already in position.  
**Type:** String (ID reference)  
**Default Value:** "" (empty — independent)  
**Validation:** Must be empty or a valid sub-strategy ID.  
**Example:** "9kQBFPI5E72KlVG8lnHfOgaC0$aC0$"  
**DB Field Name:** main\_strategy\_parameter\_id  
**Execution Context:** Trading Server checks this link during signal processing to determine execution dependency or parameter inheritance.  
**Note:** This field is not exposed in the standard UI. It is set programmatically via API or internal configuration. Strategies where this is populated are referred to as "strategies with hidden features" in the platform.  

---

# Advance Parameters

### **1\. Working Days**

**Description:** Select the weekdays on which the strategy is allowed to accept and execute inbound signals.  
**Logic:** When a signal arrives on a day not in the enabled list, the system rejects the signal and no trades are placed. Existing open positions continue to be managed regardless of the day setting.  
**Type:** Multiple Boolean Flags (Checkboxes)  
**Default Value:** MON \= True, TUE \= True, WED \= True, THU \= True, FRI \= True, SAT \= False, SUN \= False  
**Validation:** Allowed values per day: True / False  
**Example:** Mon–Fri enabled, Sat–Sun disabled.  
**DB Field Name:** run\_mon, run\_tue, run\_wed, run\_thu, run\_fri, run\_sat, run\_sun  
**Execution Context:** Checked before accepting any new inbound signal on a given day.  

**Note:** Unlike Unified Strategy Builder and Indicator Signal Engine (which support Mon–Sat only), Inbound Signal Bridge supports **all seven days including Sunday** via the `run_sun` field — relevant for MCX commodity markets that trade on Saturdays, or international signals.  
---

### **2\. Exit Before Market Close (Intraday / Contract Expiry)**

**Description:** Group setting defining when intraday positions are force-exited before market close, and whether contracts are automatically squared off on expiry day.  
**Logic:** Two sub-settings control this group.  
**Type:** Group  
**DB Field Name:** intraday\_exit\_time\_min, auto\_sqroff\_on\_contract\_exp  
---

#### **2.1 Minute(s)**

**Description:** Number of minutes before market close at which intraday positions are force-squared off.  
**Logic:** Trading Server computes the sqroff time as (Market Close Time − Minute(s)). For example, if market closes at 15:30 and Minute(s) \= 15, sqroff happens at 15:15. This applies when Trading Type \= Intraday.  
**Type:** Number  
**Default Value:** 15  
**Validation:** Must be a positive integer within reasonable market hours window.  
**Example:** 15 (exit 15 minutes before close)  
**DB Field Name:** intraday\_exit\_time\_min  
**Execution Context:** Trading Server uses this to compute the daily force-exit timestamp for intraday strategies.  

**Note:** Unlike USB and ISE which use an absolute clock time (e.g., 15:15:00), Inbound Signal Bridge uses a relative "minutes before close" value. This makes it market-time-agnostic and compatible with different exchanges (NSE closes at 15:30, MCX at different times).  
---

#### **2.2 Auto Sqroff on Contract Expiry**

**Description:** Enable automatic square-off of all open positions on the contract expiry date.  
**Logic:** When enabled, on the day a held contract expires, all open positions in that contract are automatically closed by the system at or before the scheduled expiry time, preventing holding into expiry settlement.  
**Type:** Boolean (Checkbox)  
**Default Value:** True  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** auto\_sqroff\_on\_contract\_exp  
**Execution Context:** Trading Server checks contract expiry dates for all open positions daily and triggers forced exit on the expiry date when this is enabled.  
---

### **3\. Required Margin**

**Description:** Group setting that defines the estimated margin percentage required for different instrument and position types. Used internally for capital utilization and quantity calculation.  
**Logic:** These three percentage values represent the broker margin requirement as a fraction of total position value. They are used in qty distribution calculations to estimate capital consumed per position.  
**Type:** Group of Number (Percentage) fields  
**DB Field Name:** margin\_stock\_intraday, margin\_stock\_positional, margin\_futopt\_positional  
---

#### **3.1 Stock Intraday(%)**

**Description:** Margin percentage required for intraday stock positions.  
**Type:** Number (Percentage)  
**Default Value:** 30  
**Validation:** Must be a positive number.  
**Example:** 30 (30% of position value required as margin for intraday stock trades)  
**DB Field Name:** margin\_stock\_intraday  
**Execution Context:** Used in qty sizing calculations for stock legs with Intraday trading type.  
---

#### **3.2 Stock Positional(%)**

**Description:** Margin percentage required for positional stock positions.  
**Type:** Number (Percentage)  
**Default Value:** 100  
**Validation:** Must be a positive number.  
**Example:** 100 (100% of position value required — full delivery margin for positional stock)  
**DB Field Name:** margin\_stock\_positional  
**Execution Context:** Used in qty sizing calculations for stock legs with Positional trading type.  
---

#### **3.3 Future & Option(%)**

**Description:** Margin percentage required for Futures and Options positions (both intraday and positional).  
**Type:** Number (Percentage)  
**Default Value:** 30  
**Validation:** Must be a positive number.  
**Example:** 30 (30% SPAN + exposure margin typical for F\&O)  
**DB Field Name:** margin\_futopt\_positional  
**Execution Context:** Used in qty sizing calculations for FUT and OPT legs.  
---

### **4\. Sqroff All Legs (on any single leg close by TP or SL)**

**Description:** Enable automatic square-off of all other open legs when any single leg hits its target or stoploss.  
**Logic:** When enabled, if one symbol leg closes due to its individual TP or SL being hit, the system immediately squares off all other open legs in the same strategy.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** sqroffAllLegs  
**Execution Context:** Used as a global exit trigger — a single leg's exit cascades to all remaining legs.  
---

### **5\. Sqroff Position on Rejection**

**Description:** Enable automatic square-off of all open legs when any new leg order is rejected.  
**Logic:** When enabled, if during order placement any leg's order is rejected by the broker (e.g., margin shortfall, risk limit breach, symbol freeze), the system immediately squares off all currently open legs to avoid unhedged or partial positions.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** pause\_and\_sqroff\_trading\_on\_margin\_exeed  
**Execution Context:** Safety mechanism — prevents incomplete strategy positions when partial leg execution occurs.  

---

# Description Parameters

### **1\. Short Description**

**Description:** A brief one-line summary written by the user to identify the strategy in listings and reports.  
**Logic:** Purely informational. No impact on execution, signals, target, or SL.  
**Type:** Single-line Text Input  
**Default Value:** Blank  
**Validation:** Optional. Recommended max length 100–150 characters. No logic validation required.  
**Example:** "BNF weekly CE hedge on TradingView signal, 2% capital per trade."  
**DB Field Name:** short\_description  
**Execution Context:** Displayed only for user reference (Strategy List, Detail View, Copilot Preview). Not used in execution.  
---

### **2\. Long Description**

**Description:** A longer explanation entered by the user to document strategy idea, signal source, capital rules, and usage notes for future reference.  
**Logic:** Informational only. Does not affect how the strategy executes.  
**Type:** Multi-line Text Area  
**Default Value:** Blank  
**Validation:** Optional. No restrictions on length or format.  
**Example:** "Receives TradingView SuperTrend alerts on BANKNIFTY. Entry on BUY alert. 2 legs: BNF FUT NEAR MONTHLY (Fix, 1 lot) + NIFTY CE NEAR WEEKLY (Capital 2%). Master SL ₹5000. Auto sqroff 15 min before close."  
**DB Field Name:** long\_description  
**Execution Context:** Displayed only for user and Copilot reference. Has no role in execution, qty, SL, TP, or signal handling.  

---

# Help

### **🔹 TAB 1: MAIN – HELP**

**Strategy Name**  
Give a unique name to identify this strategy. Used only for your reference and reports — does not affect execution.

**Capital**  
Set the total portfolio capital assigned to this strategy. This is the base amount used to calculate position size dynamically when Qty Distribution is Capital(%), Capital Risk(%), or Allocation Method 1.  
If set to 0, the system uses the available account capital at runtime.

**Trading Type**  
Choose **Intraday** or **Positional**.  
Intraday: positions are closed a configured number of minutes before market close (set in Advance tab).  
Positional: positions carry forward until SL/Target, contract expiry, or manual exit.

**Product**  
Select product type: **MIS**, **NRML**, or **CNC**.  
This is used for every order placed by this strategy. MIS positions may be auto-squared off by the broker at end of day.

**Master Target**  
Set the total combined profit level at which all legs should be closed.  
When combined MTM reaches this value, all open positions are squared off and no new signals are accepted until the strategy is reset.  
Set to 0 to disable.

**Master SL**  
Set the total combined loss level at which all legs should be closed.  
When combined MTM loss reaches this value, all open positions are squared off and no new signals are accepted until reset.  
Set to 0 to disable.

**Max Position**  
The maximum number of symbol positions that can be open simultaneously.  
If 10 symbols are configured and Max Position \= 8, signals for the 9th and 10th symbol will be rejected.  
Set to 0 for no limit.

**Max Capital Allocation(%)**  
Caps the maximum percentage of total capital that can be allocated to any single symbol.  
Active only when any symbol uses "Capital Risk(%)" Qty Distribution.  
Example: 10% means each symbol can consume at most 10% of total capital.

---

### **🔹 TAB 2: SYMBOLS – HELP**

**Symbol**  
Click to open the "Select Symbol" dialog. Configure Exchange, Segment, Symbol, Contract, Expiry, ATM, and Option Type for this leg.  
The resolved Trading Symbol and Expiry Date are shown before you confirm.

**Exchange**  
Select the exchange for this leg: NSE, NFO, BFO, BSE, MCX, CDS.

**Segment**  
Select **FUT** for Futures, **OPT** for Options, or **Stock** for equity cash.  
ATM and Option Type fields are only relevant for OPT.

**Symbol**  
Select the underlying instrument (e.g., BANKNIFTY, NIFTY, RELIANCE, 360ONE).

**Contract**  
Select **NEAR** (current contract), **NEXT** (next contract), or **FAR** (far contract).

**Expiry**  
Select **MONTHLY** or **WEEKLY** contract expiry type.  
WEEKLY is shown only for symbols that support weekly expiry contracts.

**ATM**  
For OPT segment only. 0 \= At-The-Money strike. Positive values move toward OTM (CE) / ITM (PE). Negative values move toward ITM (CE) / OTM (PE).

**Option Type**  
For OPT segment only. Select **CE** (Call) or **PE** (Put).

**Strike Price**  
For OPT legs. Set to 0 to use ATM-relative strike selection (based on ATM field). Enter an actual strike price (e.g., 48000) to trade a fixed strike regardless of ATM.

**Qty Distribution**  
Select how trade quantity is calculated. Four options:
- **Fix** → Fixed lot count per trade.
- **Capital(%)** → Qty based on capital percentage. Lot/Qty field shows the percentage.
- **Capital Risk(%)** → Qty based on how much capital to risk relative to SL. Lot/Qty field shows the risk percentage.
- **Allocation Method 1** → Qty based on capital divided equally by available open positions.

**Lot/Qty**  
For Fix: number of lots. Actual quantity \= Lots × Exchange lot size.  
For Capital(%): enter the percentage of capital to use.  
For Capital Risk(%): enter the percentage of capital to risk per trade.

**Target**  
Profit value at which this leg will be squared off. 0 \= No target for this leg.

**SL**  
Loss value at which this leg will be stopped out. 0 \= No stoploss for this leg.

**Trail SL (Checkbox)**  
Enable stoploss trailing for this leg. When checked, three sub-fields appear:
- **Market Move (Points):** Profit movement to trigger one SL trail step.
- **SL Move (Points):** Amount SL moves per trail step.
- **No of Trail SL:** Maximum trail steps. 0 \= unlimited.

**Copy Icon**  
Duplicates this symbol row with all current settings for quick multi-leg setup.

**Add (+)**  
Adds a new blank symbol leg row.

---

### **🔹 TAB 3: ADVANCE – HELP**

**Working Days**  
Select which days of the week this strategy accepts inbound signals.  
Days not selected will cause any signal on that day to be rejected.  
Supports Monday through Sunday (7 days, including Sunday for commodity/MCX markets).

**Exit Before Market Close – Minute(s)**  
For Intraday strategies: set how many minutes before market close all open positions are force-exited.  
Example: 15 means exit at market close time minus 15 minutes.

**Auto Sqroff on Contract Expiry**  
When checked, the system automatically closes all positions in a contract on its expiry date.  
Prevents holding into expiry settlement and eliminates overnight expiry risk.

**Required Margin – Stock Intraday(%)**  
Estimated margin percentage for intraday stock positions. Default: 30%.  
Used in capital-based qty calculations.

**Required Margin – Stock Positional(%)**  
Estimated margin percentage for positional stock positions. Default: 100%.  
Full delivery margin is typically required for positional stock holdings.

**Required Margin – Future & Option(%)**  
Estimated margin percentage for Futures and Options positions. Default: 30%.  
Represents typical SPAN + exposure margin for F\&O instruments.

**Sqroff All Legs (on any single leg close by TP or SL)**  
When enabled: if any one symbol leg hits its TP or SL and exits, all other open legs in this strategy are immediately squared off.  
Use this when your multi-leg structure must exit as a complete unit.

**Sqroff Position on Rejection**  
When enabled: if any new order for a leg is rejected by the broker (margin failure, freeze, etc.), all currently open legs are immediately squared off.  
Prevents partial or unbalanced position exposure.

---

### **🔹 TAB 4: DESCRIPTION – HELP**

**Short Description**  
One-line summary of your strategy. Optional. Used for quick identification in lists.

**Long Description**  
Detailed notes about your strategy's signal source, capital rules, instrument setup, and trading logic. Optional. Used only for your reference and Copilot understanding.

---

# FAQ

**Q1. What is the Inbound Signal Bridge plugin?**  
A multi-symbol automated execution engine that receives external trading signals (from TradingView, Pine Script, webhooks, or any alert system) and converts them into real broker orders across configured instrument legs — with no internal signal generation.

**Q2. How is this different from the Indicator Signal Engine?**  
Indicator Signal Engine generates signals internally using built-in indicators (RSI, MACD, SuperTrend, etc.). Inbound Signal Bridge receives signals from outside — it does not compute any indicators internally. It is purely an execution and position management layer.

**Q3. How is this different from the Unified Strategy Builder?**  
Unified Strategy Builder uses time-based, price-range-based, or premium-based internal entry rules with complex strike selection. Inbound Signal Bridge has no internal entry logic — it executes only when an external signal is received via webhook or API call.

**Q4. What external sources can send signals to this plugin?**  
Any system that can make an HTTP POST request: TradingView Pine Script alerts, custom Python/API scripts, third-party signal providers, PMS (Portfolio Management Service) systems, or any webhook-capable alert platform.

**Q5. Do all symbol legs execute when one signal arrives?**  
Yes. When a valid inbound signal is received for a strategy, all configured and active symbol legs execute simultaneously as a single batch.

**Q6. Can I have different instruments in the same strategy?**  
Yes. Each symbol leg is independently configured — you can mix FUT, OPT, and Stock legs from different exchanges in one strategy, all executing on the same signal.

**Q7. What Qty Distribution types are available?**  
Four types:
1. **Fix** — Fixed lot count per trade.
2. **Capital(%)** — Qty = (Available Capital × %) / Instrument Price.
3. **Capital Risk(%)** — Qty = (Available Capital × Risk%) / SL.
4. **Allocation Method 1** — Qty = (Available Capital / Available Position Count) / Instrument Price.

**Q8. When should I use Capital Risk(%) distribution?**  
Use this when you want to risk a fixed percentage of your capital per trade. The system automatically sizes the position so the SL equals the configured risk amount, regardless of the instrument price.

**Q9. What does Max Capital Allocation(%) do?**  
It caps the maximum capital any single symbol can consume. Only applies when the leg uses Capital Risk(%) distribution. Example: if set to 10%, no single symbol can use more than 10% of total capital, even if the risk calculation would allow more.

**Q10. What does Max Position do?**  
Limits the total number of simultaneously open symbol positions. If the limit is reached, new inbound signals for additional symbols are rejected. Set to 0 for no limit.

**Q11. What is the difference between Leg SL and Master SL?**  
Leg SL exits only that individual symbol leg when its loss threshold is hit. Master SL monitors the combined P\&L of all legs and exits everything when total combined loss reaches the threshold.

**Q12. Can I use both Leg SL and Master SL simultaneously?**  
Yes. Whichever triggers first causes the respective exit — Leg SL exits only that leg; Master SL exits all legs.

**Q13. What does Trail SL do?**  
As a leg's profit increases by "Market Move (Points)", the stoploss is tightened by "SL Move (Points)" — progressively locking in profit while allowing further upside.

**Q14. How is Intraday exit time configured here?**  
Unlike other plugins that use an absolute time (e.g., 15:15:00), Inbound Signal Bridge uses "minutes before market close" (e.g., 15 minutes). This is exchange-agnostic and automatically adjusts to different market closing times.

**Q15. What does Auto Sqroff on Contract Expiry do?**  
When enabled, all open positions in a contract are automatically closed by the system on the contract's expiry date. This prevents accidental settlement at expiry, which is critical for options and futures strategies.

**Q16. Can I trade on Saturday and Sunday?**  
Inbound Signal Bridge supports all 7 days (Mon–Sun) via individual `run_sun` and `run_sat` flags. This supports MCX commodity markets (which trade on Saturdays) and international signal routing.

**Q17. What happens when Master Target or Master SL is hit?**  
All open legs are squared off immediately. Unlike Unified Strategy Builder which supports automatic reexecution cycles, Inbound Signal Bridge does not automatically reexecute — the strategy pauses until manually reset.

**Q18. What is the purpose of "Sqroff All Legs on TP/SL"?**  
When one symbol leg hits its individual TP or SL and exits, this switch forces all other open legs to close simultaneously. Use this when your multi-symbol structure must always trade and exit as a complete basket.

**Q19. What does "Sqroff Position on Rejection" protect against?**  
If a broker rejects any new leg order (due to margin shortfall, circuit breaker, or any reason), this switch immediately closes all currently open legs. This prevents a situation where part of the strategy is hedged and part is not — protecting against naked exposure.

**Q20. What are Required Margin settings for?**  
They define the estimated margin percentage for each instrument type. These are used in capital-based qty calculations to determine how much capital each position will consume when computing dynamic position sizes.

**Q21. Can different legs have different qty distributions?**  
Yes. Each symbol leg has its own Qty Distribution setting — one leg can use Fix while another uses Capital(%). They are fully independent.

**Q22. What is the "Import Template" feature?**  
It allows importing a previously saved/exported strategy configuration, pre-filling all settings. The Template dropdown also provides preset strategy configurations.

**Q23. Can the same strategy have a mix of CE and PE legs?**  
Yes. You can add multiple OPT legs with different option types, ATM offsets, and expiries. All execute on the same inbound signal.

**Q24. What is the hidden "main\_strategy\_parameter\_id" field?**  
An advanced API-level field that links one symbol leg to another sub-strategy's parameters. This is used in PMS or portfolio configurations where one leg's execution depends on another strategy's leg being active. It is not exposed in the standard UI and is set programmatically.

**Q25. What is "allow\_update\_parameters"?**  
An API-level flag (default: true) that controls whether parameters of this strategy can be updated programmatically (e.g., by a PMS admin pushing parameter changes to client strategies in real time). Not exposed in the standard UI.

**Q26. What is "effect\_all\_sub\_strategies"?**  
An API-level flag that, when true, causes a parameter change to propagate to all symbol legs in the strategy simultaneously. Useful for batch updates across all legs from a single API call.

**Q27. What happens if an inbound signal arrives on a disabled working day?**  
The signal is rejected. No orders are placed. Existing open positions continue to be managed by their individual SL/Target rules regardless.

**Q28. Can I have a strategy with no Master Target or Master SL?**  
Yes. Setting both to 0 disables them. Individual leg-level TP/SL still operate independently per leg.

**Q29. What if no Trail SL is set but checkbox is ON?**  
If the checkbox is ON but all three sub-fields (Market Move, SL Move, No of Trail SL) are 0, trailing does not activate. All three must be non-zero for trailing to work.

**Q30. How does Allocation Method 1 calculate qty?**  
It divides available capital by the number of currently available position slots to get per-symbol free margin, then divides by instrument price for qty. This dynamically distributes capital evenly across all open positions.

---

# Copilot Rulebook

Below is the **FULL "HOW COPILOT SHOULD RESPOND" RULEBOOK** for the Inbound Signal Bridge Plugin.

This is a master AI-instruction document that completely defines:

* How Copilot must interpret user prompts  
* How Copilot must map natural language into plugin parameters  
* How Copilot must configure symbols, qty distribution, and exit rules  
* How Copilot must ask clarifying questions (only when needed)  
* How Copilot must generate strategy output  
* How Copilot must avoid mistakes

---

# **🧠📘 Inbound Signal Bridge – COPILOT RESPONSE RULEBOOK**

### ***AI Behavior & Interpretation Logic***

---

# **1️⃣ COPILOT's PURPOSE**

The Copilot's job is to **convert trader instructions** (natural language) into a **complete Inbound Signal Bridge strategy configuration**:

* Main Parameters  
* Symbols Parameters (one or more legs)  
* Advance Parameters  
* Description Tab

Copilot must generate **100% valid, executable configurations** following all plugin field rules and quantity distribution constraints.

Copilot should behave like a **trading assistant**, not a chatbot.

---

# **2️⃣ CORE RESPONSIBILITIES**

Copilot must:

### **✔ Understand that this plugin has NO internal signal generation**

There are no indicators, no chart types, no timeframes. Entry is triggered externally. Copilot must not add any indicator configuration to ISB strategies.

### **✔ Understand capital-based qty distribution**

Capital(%), Capital Risk(%), and Allocation Method 1 are mathematically driven. Copilot must apply the correct formula when interpreting user intent.

### **✔ Map every human phrase to correct plugin parameters**

Example:  
"Trade BankNifty futures on TradingView signal, risk 2% of 5 lakh capital per trade, SL 3000"  
→ Symbol: BANKNIFTY FUT NEAR MONTHLY, Qty Distribution: Capital Risk(%), Percentage: 2, SL: 3000

### **✔ Ask only necessary clarifying questions**

Only when critical information is missing.

### **✔ Never add indicator or chart configuration**

ISB has no indicator engine. Never add Signal, TimeFrame, ChartType, or indicator fields.

### **✔ Ensure valid output**

All fields must follow allowed options, data types, and validations.

---

# **3️⃣ HOW COPILOT MUST INTERPRET NATURAL LANGUAGE**

---

## **A. Identify Instruments (Symbols)**

Copilot must detect which instruments to configure as symbol legs:

* "BankNifty futures" → Segment \= FUT, Symbol \= BANKNIFTY, Expiry \= MONTHLY, Contract \= NEAR  
* "Nifty weekly CE ATM" → Segment \= OPT, Symbol \= NIFTY, Expiry \= WEEKLY, ATM \= 0, OptionType \= CE  
* "Reliance stock" → Segment \= Stock, Exchange \= NSE, Symbol \= RELIANCE  
* "100 points OTM CE" → ATM \= +1 or more depending on context  
* "current week expiry" → Expiry \= WEEKLY, Contract \= NEAR

---

## **B. Identify Quantity Distribution**

| User Phrase | Qty Distribution |
|-------------|-----------------|
| "fixed 2 lots" / "2 lots per trade" | Fix, Lot \= 2 |
| "2% of capital" / "allocate 2% capital" | Capital(%), qty \= 2 |
| "risk 1% of capital" / "1% capital risk per SL" | Capital Risk(%), qty \= 1 |
| "equal allocation across positions" | Allocation Method 1 |
| No mention | Default: Fix, Lot \= 1 |

---

## **C. Identify Exit Logic**

* "stoploss 3000" → leg sl \= 3000 (or master sl if "combined" or "overall")  
* "target 5000" → leg target \= 5000 (or master target if "overall")  
* "trail SL after 1000 profit, trail 500" → Market Move \= 1000, SL Move \= 500  
* "exit 15 minutes before close" → Minute(s) \= 15  
* "auto close on expiry" → Auto Sqroff on Contract Expiry \= True

---

## **D. Identify Capital and Position Settings**

* "5 lakh capital" → Capital \= 500000  
* "max 5 positions at a time" → Max Position \= 5  
* "each stock max 10% allocation" → Max Capital Allocation(%) \= 10

---

## **E. Identify Safety Settings**

* "close all legs if any leg hits SL" → Sqroff All Legs \= True  
* "close all if order rejected" → Sqroff Position on Rejection \= True  
* "trade only Monday to Friday" → run\_mon–fri \= True, run\_sat/sun \= False

---

## **F. Identify Trading Type**

* "intraday" → is\_intraday \= True  
* "positional" / "carry forward" → is\_intraday \= False  
* No mention → Default: Positional (is\_intraday \= False)

---

# **4️⃣ WHEN COPILOT MUST ASK CLARIFYING QUESTIONS**

Only when **critical information is missing**:

1. Symbol/instrument not specified  
2. Segment not clear (futures, options, or stock?)  
3. Qty distribution method ambiguous  
4. Capital not specified (needed for Capital(%) or Capital Risk(%))  
5. SL not specified (needed for Capital Risk(%) calculation)  
6. Expiry not specified for options  
7. No legs defined at all

**Example clarifying questions:**

* "Which instrument should this strategy trade — futures, options, or stocks?"  
* "Do you want fixed lot size or capital-based sizing?"  
* "What is the total capital for this strategy?"  
* "What is the SL per leg — needed to calculate Capital Risk(%) qty."

---

# **5️⃣ WHEN NOT TO ASK QUESTIONS**

If information can be **reasonably inferred**:

* Single symbol mentioned with no qty → Fix, 1 lot  
* "weekly" → Expiry \= WEEKLY  
* "ATM" → ATM \= 0  
* No expiry for FUT → MONTHLY  
* No contract → NEAR  
* No entry time mention → no entry time field (ISB has no entry time — it's signal-driven)  
* No working days mention → Mon–Fri enabled, Sat–Sun disabled  
* No exit time mention → Minute(s) \= 15 (default)  
* No Master Target/SL → 0 (disabled)

---

# **6️⃣ OUTPUT FORMAT COPILOT MUST FOLLOW**

Every Copilot output must generate:

### **✔ A full Inbound Signal Bridge configuration**

* Tab 1 (Main)  
* Tab 2 (Symbols — each leg fully described)  
* Tab 3 (Advance)  
* Tab 4 (Description)

### **✔ MUST NOT ADD INDICATOR OR SIGNAL CONFIGURATION**

ISB has no chart type, no timeframe, no indicator section. Never add these.

### **✔ MUST CORRECTLY APPLY QTY DISTRIBUTION MATH**

Always state the formula and result when using Capital(%) or Capital Risk(%).

---

# **7️⃣ RULES FOR MAPPING USER PROMPTS TO PLUGIN FIELDS**

---

## **A. Qty Distribution Mapping**

| User Phrase | Qty Distribution | Lot/Qty Field |
|-------------|-----------------|---------------|
| "1 lot fixed" | Fix | lot \= 1 |
| "5% of capital" | Capital(%) | qty \= 5 |
| "risk 2% of capital" | Capital Risk(%) | qty \= 2 |
| "equal split across positions" | Allocation Method 1 | automatic |

---

## **B. Symbol Mapping**

| Phrase | Plugin Mapping |
|--------|---------------|
| "BankNifty futures near monthly" | segment\=FUT, symbol\=BANKNIFTY, contract\=NEAR, expiry\=MONTHLY |
| "Nifty weekly CE ATM" | segment\=OPT, symbol\=NIFTY, expiry\=WEEKLY, atm\=0, optionType\=CE |
| "100 points OTM put weekly" | segment\=OPT, expiry\=WEEKLY, atm\=-1 for PE (OTM direction) |
| "Reliance stock delivery" | segment\=Stock, symbol\=RELIANCE, product\=CNC |
| "360ONE weekly OPT" | segment\=OPT, symbol\=360ONE, expiry\=WEEKLY |

---

## **C. Exit Mapping**

| Phrase | Plugin Mapping |
|--------|---------------|
| "SL 2500 per leg" | sub.sl \= 2500 |
| "combined SL 10000" | intraday\_sl \= 10000 (Master SL) |
| "target 5000 total" | intraday\_target \= 5000 (Master Target) |
| "trail after 1000, move 500" | trail\_sl\_market\_move\=1000, trail\_sl\_move\=500 |
| "exit 10 min before close" | intraday\_exit\_time\_min \= 10 |
| "auto close on expiry" | auto\_sqroff\_on\_contract\_exp \= true |

---

# **8️⃣ COPILOT MUST ALWAYS CHECK VALIDATIONS BEFORE OUTPUT**

* Max Position must be \>= 0 (0 \= no limit)  
* Max Capital Allocation must be 1–100  
* Lot/Qty must be positive  
* SL and Target must be \>= 0  
* Trail SL sub-fields must be \>= 0  
* ATM must be integer (only for OPT)  
* Option Type CE/PE only for OPT segment  
* For Capital Risk(%): SL must be non-zero (else division by zero in formula)  
* Minute(s) for exit must be a valid positive number  
* At least one symbol leg must be configured

If invalid → Copilot must correct or ask user.

---

# **9️⃣ HOW COPILOT MUST RESPOND FOR SAMPLE PROMPTS**

---

### **Example 1**

**User:** "Create a TradingView signal strategy for BankNifty futures, 1 lot, SL 3000, exit 15 min before close."

**Copilot must output:**

* Symbol: BANKNIFTY FUT NEAR MONTHLY, Qty Distribution: Fix, Lot \= 1, SL \= 3000  
* Advance: Minute(s) \= 15, Auto Sqroff on Contract Expiry \= True  
* Master Target: 0 (disabled), Master SL: 0 (disabled)  
* Working Days: Mon–Fri  
* No clarifying questions needed

---

### **Example 2**

**User:** "Multi-stock portfolio signal strategy. 10 lakh capital, risk 2% per stock per trade, max 5 positions."

**Copilot must infer:**

* Capital \= 1,000,000  
* Qty Distribution: Capital Risk(%)  
* qty \= 2 (2% risk per trade)  
* Max Position \= 5  
* Ask: "Which stocks/instruments should I add as legs?" and "What is the SL per stock for the Capital Risk(%) calculation?"

---

### **Example 3**

**User:** "Signal bridge for NIFTY weekly CE ATM + BANKNIFTY weekly PE ATM hedge. 1 lot each. Combined SL 5000."

**Copilot must output:**

* Leg 1: NIFTY OPT NEAR WEEKLY, atm\=0, CE, Fix, 1 lot  
* Leg 2: BANKNIFTY OPT NEAR WEEKLY, atm\=0, PE, Fix, 1 lot  
* Master SL \= 5000  
* Sqroff All Legs \= True (basket exits together on combined SL)  
* No clarifying questions needed

---

### **Example 4**

**User:** "Create a strategy that closes all positions if any one leg hits SL, and also closes all if an order gets rejected."

**Copilot must output:**

* Advance: Sqroff All Legs \= True  
* Advance: Sqroff Position on Rejection \= True  
* Ask: "Which instruments should I add as legs?" (symbol missing)

---

# **🔟 COPILOT MUST ALWAYS INCLUDE DESCRIPTION TAB**

Copilot must generate:

**Short Description**  
A one-line summary of what instruments this strategy trades and what signal source it expects.

**Long Description**  
Human-readable explanation of the signal source, qty rules, exit conditions, and capital configuration.

---

# **1️⃣1️⃣ WHAT COPILOT MUST NEVER DO**

❌ Never add indicator, chart type, timeframe, or signal direction fields — ISB has none  
❌ Never set negative values in SL, Target, or Trail fields  
❌ Never configure Capital Risk(%) without a non-zero SL value (causes divide-by-zero)  
❌ Never leave the Symbols tab empty — at least one leg required  
❌ Never ignore Max Position when user specifies a position limit  
❌ Never add non-existent fields to the configuration  
❌ Never assume Intraday when user says "positional" or vice versa  
❌ Never set ATM or Option Type for FUT or Stock legs

---

# **1️⃣2️⃣ AI RULE: USE SAFEST DEFAULTS WHEN USER IS UNCLEAR**

Defaults Copilot should use when user does not specify:

* Trading Type: Positional (is\_intraday \= false)  
* Product: NRML  
* Qty Distribution: Fix, 1 lot  
* Capital: 0 (uses account available capital at runtime)  
* Master Target: 0 (disabled)  
* Master SL: 0 (disabled)  
* Max Position: 0 (no limit)  
* Max Capital Allocation: 100%  
* Exit Minute(s): 15  
* Auto Sqroff on Contract Expiry: True  
* Working Days: Mon–Fri enabled; Sat, Sun disabled  
* Contract: NEAR  
* Expiry: MONTHLY for FUT; WEEKLY for index OPT  
* ATM: 0  
* SL: 0 (no SL per leg) unless user specifies  
* Target: 0 (no target per leg) unless user specifies  
* Trail SL: Off unless mentioned  
* Sqroff All Legs: False  
* Sqroff Position on Rejection: False

---

# **1️⃣3️⃣ INTERNAL COPILOT DECISION PRIORITY TREE**

1. Identify instruments (symbols, segments, exchanges)  
2. Determine number of symbol legs  
3. Select qty distribution method per leg  
4. Configure capital and position controls (Max Position, Max Capital Allocation, Capital)  
5. Configure per-leg SL, Target, and Trail SL  
6. Configure Master Target and Master SL  
7. Set trading type (Intraday or Positional)  
8. Set product type  
9. Set working days  
10. Set exit minute(s) and Auto Sqroff on Contract Expiry  
11. Set safety switches (Sqroff All Legs, Sqroff on Rejection)  
12. Apply all defaults  
13. Validate all fields  
14. Generate complete configuration

---

# **1️⃣4️⃣ FINAL COPILOT OUTPUT STRUCTURE**

Copilot should output:

1. **Summary of recognized intent** (signal source, instruments, capital rules)  
2. **Main Tab configuration** (Strategy Name, Capital, Trading Type, Product, Master Target/SL, Max Position, Max Capital Allocation)  
3. **Symbols Tab configuration** (each leg fully described with Exchange, Segment, Symbol, Contract, Expiry, ATM, Option Type, Strike Price, Qty Distribution, Lot/Qty, Target, SL, Trail SL)  
4. **Advance Tab configuration** (Working Days, Exit Minute(s), Auto Sqroff, Required Margin %, Sqroff All Legs, Sqroff on Rejection)  
5. **Short description \+ Long description**  
6. **Optional refinement questions** ("Should I enable Master SL?", "Do you want Trail SL on any leg?", "Should Sqroff All Legs be enabled for basket exit?")

---

# API Reference

## **Strategy Creation**

**Endpoint:** `POST https://api.marketmaya.com/api/mainStrategy/createCustomTradeStrategy`  
**Authentication:** Bearer JWT token  
**Content-Type:** application/json

## **Full Payload Structure**

```json
{
  "id": "",
  "strategy_name": "Strategy Name",
  "short_description": "",
  "long_description": "",
  "strategy_type_id": "XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$",
  "product_type": "NRML",
  "required_margin": 0,
  "is_intraday": false,
  "target_by": "Money",
  "intraday_target": 0,
  "sl_by": "Money",
  "intraday_sl": 0,
  "allow_update_parameters": true,
  "max_position": 0,
  "max_position_allocation_percent": 100,
  "run_mon": true,
  "run_tue": true,
  "run_wed": true,
  "run_thu": true,
  "run_fri": true,
  "run_sat": false,
  "run_sun": false,
  "intraday_exit_time_min": 15,
  "margin_stock_intraday": 30,
  "margin_stock_positional": 100,
  "margin_futopt_positional": 30,
  "auto_sqroff_on_contract_exp": true,
  "pause_and_sqroff_trading_on_margin_exeed": false,
  "sqroffAllLegs": false,
  "effect_all_sub_strategies": false,
  "sub": [
    {
      "id": "",
      "exchange": "NFO",
      "segment": "FUT",
      "main_strategy_parameter_id": "",
      "symbol": "BANKNIFTY",
      "contract": "NEAR",
      "expiry": "MONTHLY",
      "atm": 0,
      "option_type": "",
      "qty_distribution": "Fix",
      "qty": 30,
      "lot": 1,
      "strike_price": 0,
      "target": 0,
      "target_by": "Money",
      "sl": 0,
      "sl_by": "Money",
      "trail_sl_market_move": 0,
      "trail_sl_move": 0,
      "no_of_time_trail_sl": 0,
      "is_trail_sl": false
    }
  ]
}
```

## **API Field Reference Table**

| UI Field | DB / API Field | Type | Notes |
|----------|---------------|------|-------|
| Strategy Name | strategy\_name | string | Required, unique |
| Capital | required\_margin | number | Capital base for dynamic qty; 0 = use live account capital |
| Trading Type | is\_intraday | boolean | false \= Positional |
| Product | product\_type | string | MIS / NRML / CNC |
| Master Target | intraday\_target + target\_by | number + string | target\_by \= "Money" |
| Master SL | intraday\_sl + sl\_by | number + string | sl\_by \= "Money" |
| Max Position | max\_position | number | 0 \= no limit |
| Max Capital Allocation(%) | max\_position\_allocation\_percent | number | 1–100 |
| Short Description | short\_description | string | Optional |
| Long Description | long\_description | string | Optional |
| Working Days | run\_mon/tue/wed/thu/fri/sat/sun | boolean each | 7 day flags |
| Exit Minute(s) | intraday\_exit\_time\_min | number | Minutes before close |
| Auto Sqroff on Contract Expiry | auto\_sqroff\_on\_contract\_exp | boolean | |
| Stock Intraday(%) | margin\_stock\_intraday | number | |
| Stock Positional(%) | margin\_stock\_positional | number | |
| Future & Option(%) | margin\_futopt\_positional | number | |
| Sqroff All Legs | sqroffAllLegs | boolean | |
| Sqroff Position on Rejection | pause\_and\_sqroff\_trading\_on\_margin\_exeed | boolean | |
| Strategy Type (fixed) | strategy\_type\_id | string | Fixed ISB identifier |
| — | allow\_update\_parameters | boolean | Always true |
| — | effect\_all\_sub\_strategies | boolean | Advanced bulk update |
| — | isEditCode | boolean | False on create |
| Sub: Exchange | sub[].exchange | string | NSE/NFO/BFO/BSE/MCX/CDS |
| Sub: Segment | sub[].segment | string | FUT / OPT / Stock |
| Sub: Symbol | sub[].symbol | string | |
| Sub: Contract | sub[].contract | string | NEAR / NEXT / FAR |
| Sub: Expiry | sub[].expiry | string | MONTHLY / WEEKLY |
| Sub: ATM | sub[].atm | integer | 0 \= ATM |
| Sub: Option Type | sub[].option\_type | string | CE / PE / "" |
| Sub: Qty Distribution | sub[].qty\_distribution | string | Fix/Capital(%)/Capital Risk(%)/Allocation Method 1 |
| Sub: Lot/Qty | sub[].lot | number | Lots for Fix mode |
| Sub: Percentage | sub[].qty | number | % value or computed qty |
| Sub: Strike Price | sub[].strike\_price | number | 0 \= use ATM |
| Sub: Target | sub[].target | number | |
| Sub: Target Type | sub[].target\_by | string | "Money" |
| Sub: SL | sub[].sl | number | |
| Sub: SL Type | sub[].sl\_by | string | "Money" |
| Sub: Trail SL | sub[].is\_trail\_sl | boolean | |
| Sub: Market Move | sub[].trail\_sl\_market\_move | number | |
| Sub: SL Move | sub[].trail\_sl\_move | number | |
| Sub: No of Trail SL | sub[].no\_of\_time\_trail\_sl | number | 0 \= unlimited |
| Sub: ID | sub[].id | string | Auto-generated unique ID; "" on create, populated on edit |
| Sub: Linked Sub ID | sub[].main\_strategy\_parameter\_id | string | "" or ID (hidden) |
