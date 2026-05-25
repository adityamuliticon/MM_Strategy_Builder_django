# Overview

**MM \- Unified Strategy Builder Plugin**  
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date: 03-12-2025  
Prepared By: Paresh Bhatiya

# PLUGIN SUMMARY

# **✅ 1\. BRD VERSION (Formal, Precise, Functional Definition)**

## **Unified Strategy Builder Plugin – Product Overview**

**Unified Strategy Builder** is an advanced multi-leg strategy creation engine designed for building hedged option and futures structures with complete control over entries, exits, re-execution, and overall MTM behavior. The plugin allows traders to configure individual legs (BUY/SELL CE, PE, FUT, STOCK), define custom strike selection logic, and set leg-wise Target, Stoploss, Trailing, and conditional actions.

Beyond individual legs, Unified Strategy Builder provides **global/master-level controls** such as Master Target, Master Stoploss, Profit Locking, Trailing, Re-execution cycles, Working Day filters, VIX-based volatility filters, and pre-expiry square-off conditions.

The plugin supports **event-driven multi-leg automation**, where one leg can trigger another based on TP/SL or waiting conditions. Idle legs can be activated dynamically through action-based execution like Execute Leg, Re-enter Leg, or Sqroff Leg.

The strategy is fully parameterized, giving complete flexibility to model:

* Delta-neutral structures  
* Directional hedges  
* Spreads (vertical, horizontal, diagonal)  
* Ratio hedging  
* Premium-based and volatility-sensitive systems

The plugin is designed exclusively for creating structured hedged models with automation, risk control, and complete customizability for option sellers, buyers, and futures traders.

---

## **Key Capabilities**

* Build **unlimited legs**, each with independent logic.  
* Use flexible **strike selection**: ATM/ATM%, Premium Range, Delta Range, Theta Range, Nearest Premium/Delta/Theta, etc.  
* Configure **leg-level TP/SL**, trailing, profit locking, wait-and-trade, range breakout entries.  
* Configure **strategy-level TP/SL** using Combined Profit or Combined Premium.  
* Assign **actions** (Execute/Re-enter/Sqroff) on leg TP, SL, and also at Master TP/SL.  
* Enable **automatic re-execution cycles** with delay controls.  
* Manage expiry risk with **pre-expiry square-off**.  
* Control volatility exposure using **VIX Start–End range**.  
* Restrict entries to selected **working days**.  
* Enable safety features like sqroff on rejection, sqroff on any leg hit, and TP/SL tracking while paused.

The plugin is designed for **hedging strategies**, but can also build:

* Straddles, Strangles  
* Ratio spreads  
* Iron condor / butterfly  
* Intraday multi-leg hedging  
* Premium decay strategies  
* Dynamic reentry strategies  
* BTST/STBT positional hedges

---

## **Primary Objective**

To provide a **highly configurable**, **risk-aware**, and **automation-friendly** strategy-building environment that supports any multi-leg hedging system with precision and control.

---

# **✅ 2\. COPILOT VERSION (AI-Optimized, Natural Language, Training Input)**

**Unified Strategy Builder is a multi-leg options and futures strategy builder** that lets traders create any combination of hedged positions with full control over entry rules, leg behavior, and overall MTM management.

Copilot should understand that:

* Each leg can have its own strike selection method, target, stoploss, trailing and conditional actions.  
* Legs can be idle and activated only when another leg hits target or stoploss.  
* Strategy-level outcomes are controlled using **Master Target** and **Master Stoploss**, which operate on combined profit or combined premium.  
* The system can automatically **re-enter** after exits based on configured cycle counts and delays.  
* The plugin supports **VIX filtering**, **working-day restrictions**, **wait-and-trade**, **range breakout**, and **pre-expiry exit**.

When a user asks Copilot to “create a strategy,” Copilot should:

1. Identify how many legs are needed.  
2. Assign BUY/SELL, CE/PE, expiry, strike selection logic for each leg.  
3. Configure leg-level target/SL and trailing if required.  
4. Configure Master Target / Master SL values if mentioned or implied.  
5. Enable VIX filters, day filters, or pre-expiry sqroff if asked.  
6. Convert trader instructions into correct parameter mappings using plugin rules.

Copilot should treat Unified Strategy Builder as the plugin for **hedged, multi-legged, risk-managed option strategies**.

---

# **✅ 3\. SHORT PLUGIN CARD SUMMARY (To display on homepage)**

### **Unified Strategy Builder**

Create fully automated hedged strategies using multi-leg options or futures.  
Configure custom strike logic, per-leg TP/SL, global MTM target/SL, trailing, VIX filters, and automatic re-entry cycles.

# Parameter Description

# Main Parameters

### **1\. Strategy Name**

**Description:** User-defined name of the strategy. Shown in UI and used for identification.  
**Logic:** Does not affect execution. Only used for listing, search, copy/duplicate, and Copilot reference.  
**Type:** String  
**Default Value:**  Blank (“”)  
**Validation:**

- Required  
- Must be unique per user  
- Minimum length 3, maximum 100 characters  
- Cannot include unsupported special characters

**Example:**  “Unified Strategy Builder – BankNifty Intraday”  
**DB Field Name:**  strategy\_name  
**Execution Context:**  Used only by UI and Copilot to reference the strategy. Trading Server ignores this value.  
---

### **2\. Underlying Exchange**

**Description:** Select the exchange of the underlying instrument. Available exchanges include NSE, NFO, BFO, BSE, MCX, and CDS.  
**Logic:**  Controls which segments and symbols become available next.  
**Type:**  String (Dropdown)  
**Default Value:** NFO  
**Validation:**  Must be a valid exchange from the list.  
**Example:**  NFO  
**DB Field Name:** Main\_exchange  
**Execution Context:** Determines which market feed is used to fetch underlying LTP for strike selection.  
---

### **3\. Underlying Segment**

**Description:** Select the segment for the underlying instrument (FUT, OPT, or Stock).  
**Logic:** Filters and populates the appropriate symbol list based on selected exchange.  
**Type:** String (Dropdown)  
**Default Value:** FUT  
**Validation:** Must be a valid segment for the selected exchange.  
**Example:** FUT  
**DB Field Name:** main\_segment  
**Execution Context:** Used to determine how the underlying is mapped in the instrument master.  
---

### **4\. Underlying Symbol**

**Description:** Select the instrument to be used as the base for strike selection (BankNifty, Nifty, FINNIFTY, etc.).  
**Logic:**  All leg strike price calculations (ATM, %, delta, theta, premium range) use this underlying's LTP.  
**Type:**  String (Dropdown)  
**Default Value:**  BANKNIFTY  
**Validation:**  Must be a valid symbol for the selected exchange and segment.  
**Example:**  BankNifty  
**DB Field Name:**  main\_symbol  
**Execution Context:**  Trading Server reads this symbol’s live LTP for computing leg strike prices.  
---

### **5\. Trading Type**

**Description:**  Select whether the strategy is Intraday or Positional.  
**Logic:** 

* Intraday → Positions square off at Sqroff Time  
* Positional → Positions carry forward until expiry, BTST/STBT, or sqroff-before-expiry rules

**Type:**  String (Dropdown)  
**Default Value:**  Intraday  
**Validation:**  Must be “Intraday” or “Positional”  
**Example:**  Intraday  
**DB Field Name:**  is\_intraday  
**Execution Context:** Controls how and when all open legs are squared off.  
---

### **6\. Product**

**Description:** Select the order product type (MIS, NRML, CNC, or MTF).  
**Logic:** Included in every order request to the broker during execution.  
**Type:** String (Dropdown)  
**Default Value:** MIS  
**Validation:** Must be a valid product type.  
**Example:** NRML  
**DB Field Name:** product\_type  
**Execution Context:** Trading Server uses this while placing all buy/sell orders.  
---

### **7\. Start Time**

**Description:** Define when the strategy can begin executing legs.  
**Logic:** Leg entries start from this time unless delayed by Wait & Trade, Range Breakout, or Combined Premium Entry.  
**Type:** Time (HH:mm:ss)  
**Default Value:** 09:15:00  
**Validation:** Must be within exchange trading hours.  
**Example:** 09:20:00  
**DB Field Name:**  
 intraday\_entry\_time\_hr  
 intraday\_entry\_time\_min  
 intraday\_entry\_time\_sec  
**Execution Context:** Trading Server begins checking entry conditions only after this time.  
---

### **8\. Sqroff Time**

**Description:** Define the exit time for Intraday strategies.  
**Logic:** All open legs are closed at this time when Trading Type \= Intraday.  
**Type:** Time (HH:mm:ss)  
**Default Value:** 15:15:00  
**Validation:**

* Must be within market hours  
* Must be greater than Start Time

**Example:** 15:20:00  
**DB Field Name:**  
 intraday\_exit\_time\_hr  
 intraday\_exit\_time\_min  
 intraday\_exit\_time\_sec  
**Execution Context:** Trading Server force-sqroffs all open positions at this time.  
---

### **9\. Range Breakout**

**Description:** Enable or disable the Range Breakout entry feature.  
**Logic:** System calculates a price range (High & Low) from Start Time to Range End Time. Legs execute only when the underlying breaks the range high or range low.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** None  
**Example:** True  
**DB Field Name:** is\_range\_break\_out  
**Execution Context:** Trading Server waits for breakout direction before executing legs.  
---

### **9.1 Range End Time**

**Description:** End time for calculating the breakout range.  
**Logic:** OHLC is computed between Start Time → Range End Time. This range is used for breakout checks.  
**Type:** Time (HH:mm:ss)  
**Default Value:** 09:20:00  
**Validation:**

* Must be greater than Start Time  
* Must be within market hours

**Example:** 09:18:00  
**DB Field Name:**  
 range\_end\_time\_hr  
 range\_end\_time\_min  
 range\_end\_time\_sec  
**Execution Context:** Breakout logic becomes active once this time is reached.  
---

### **10\. BTST/STBT**

**Description:** Enable Buy-Today-Sell-Tomorrow / Sell-Today-Buy-Tomorrow mode.  
**Logic:** Strategy carries positions to the next day. Square-off happens after the configured number of Gap Days.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed only when Trading Type \= Positional.  
**Example:** True  
**DB Field Name:** is\_btst\_stbt  
**Execution Context:** Overrides intraday sqroff; Trading Server exits positions after Gap Days.  
---

### **10.1 Gap Days**

**Description:** Number of days to hold positions for BTST/STBT.  
**Logic:** Positions are squared off after the given number of days from entry.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be a positive integer.  
**Example:** 2  
**DB Field Name:** btst\_gap\_days  
**Execution Context:** Trading Server exits positions on (Entry Date \+ Gap Days).  
---

### **11\. Combined Premium Entry**

**Description:** Enable entry based on the combined premium of legs.  
**Logic:** Legs execute only when the total combined premium of selected legs meets the defined Total Premium threshold.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** None  
**Example:** True  
**DB Field Name:** is\_combined\_prem\_entry  
**Execution Context:** Trading Server continuously checks total premium until condition is met.  
---

### **11.1 Total Premium**

**Description:** Define the combined premium threshold for entry.  
**Logic:** Entry is triggered when summed premium of all configured leg strikes matches this value.  
**Type:** Number  
**Default Value:** 100  
**Validation:** Must be a positive number.  
**Example:** 350  
**DB Field Name:** total\_combined\_premium  
**Execution Context:** Trading Server compares combined premium to this value before executing any leg.

# Leg Parameters

## **1\. Idle**

**Description:** Enable or disable idle mode for this leg. Idle legs do not execute at the start and are triggered only by target or stoploss actions.  
**Logic:** When enabled, the leg is skipped during initial entry and only activated through “Action on Target” or “Action on SL” from another leg.  
**Type:** Boolean  
**Default Value:** False  
**Validation:**

* Allowed values: True / False

**Example:** True  
**DB Field Name:** is\_idle  
**Execution Context:** Trading Server executes idle legs only when triggered by action rules.  
---

## **2\. Trade Side**

**Description:** Define whether the leg will execute a BUY or SELL order.  
**Logic:** Determines direction of the leg’s trade.  
**Type:** Dropdown  
**Default Value:** BUY  
**Validation:** Allowed Values:

* BUY  
* SELL

**Example:** SELL  
**DB Field Name:** trade\_side  
**Execution Context:** Trading Server sends BUY or SELL order as defined.  
---

## **3\. Lots**

**Description:** Number of lots to trade for this leg.  
**Logic:** Quantity \= Lots × Contract Lot Size.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be a positive integer  
**Example:** 2  
**DB Field Name:** lot  
**Execution Context:** Used to compute order quantity during trade execution.  
---

### **4\. Segment**

**Description:** Segment of the trading instrument: Options, Futures, or Stock.  
**Logic:** Controls how instrument is selected (option chain, futures chain, stock master).  
**Type:** Dropdown  
**Default Value:** OPT  
**Validation:** Allowed Values:

- OPT  
- FUT  
- Stock

**Example:** OPT  
**DB Field Name:** segment  
**Execution Context:** Determines contract type to be selected from master.  
---

### **5\. Expiry**

**Description:** Select expiry bucket for this leg. Controls which weekly or monthly contract the strategy uses.  
**Logic:** Resolved dynamically at execution time using underlying’s expiry calendar.  
**Type:** Dropdown  
**Default Value:** Current Month  
**Validation:** Allowed Values:

- Current Week  
- Week 1  
- Week 2  
- Current Month  
- Month 1  
- Month 2  
   (Weekly options only shown if symbol supports weekly expiries)

**Example:** Current Week  
**DB Field Name:** expiry  
**Execution Context:** Trading Server resolves the expiry bucket to an actual contract before placing orders.  
---

### **6\. Option Type**

**Description:** Select whether the leg is CE (Call) or PE (Put).  
**Logic:** Used only when Segment \= OPT.  
**Type:** Dropdown  
**Default Value:** CE  
**Validation:** Allowed Values:

* CE  
* PE  
   Valid only when Segment \= OPT

**Example:** PE  
**DB Field Name:** option\_type  
**Execution Context:** Controls which side of the option chain is used.  
---

### **7\. Strike Selection**

**Description:** Defines how the option strike will be selected for this leg.  
**Logic:** System calculates appropriate strike based on ATM, %, Premium Range, Delta Range, Theta Range, or nearest metrics.  
**Type:** Dropdown  
**Default Value:** Strike by ATM Value  
**Validation:** Allowed Values:

- Strike by ATM Value  
- Strike by ATM %  
- Strike by Premium Range  
- Strike by Nearest Premium  
- Strike by Delta Range  
- Strike by Nearest Delta  
- Strike by Theta Range  
- Strike by Nearest Theta

**Example:** Strike by Premium Range  
**DB Field Name:** atm\_type  
**Execution Context:** Strike resolution engine chooses correct strike from option chain.  
---

### **7.1 ATM Value**

**Description:** ATM offset values for selecting strike based on underlying’s spot price.  
**Logic:** Creates a strike by adding or subtracting ATM offset (e.g., ATM \+200).  
**Type:** Dropdown  
**Default Value:** ATM 0  
**Validation:** Allowed only when Strike Selection \= Strike by ATM Value  
 Dropdown Values:

- ATM \+200  
- ATM \+100  
- ATM 0  
- ATM \-100  
- ATM \-200  
   (Up to 20 increments depending on symbol)

**Example:** ATM \-100  
**DB Field Name:** atm  
**Execution Context:** Final strike \= nearest available strike matching ATM offset.  
---

### **7.2 ATM %**

**Description:** ATM percentage-based offset values.  
**Logic:** Selects strike using LTP × (1 ± % value).  
**Type:** Dropdown  
**Default Value:** ATM % 0  
**Validation:** Allowed only when Strike Selection \= Strike by ATM %  
 Dropdown Values:

- ATM % 1.0  
- ATM % 0.75  
- ATM % 0.50  
- ATM % 0.25  
- ATM % 0  
- ATM % \-0.25  
- ATM % \-0.50  
- ATM % \-0.75  
- ATM % \-1.0

**Example:** ATM % 0.50  
**DB Field Name:** atm  
**Execution Context:** Strike determined based on % move around underlying price.  
---

### **7.2 Start Range**

**Description:** Lower threshold for Premium Range, Delta Range, or Theta Range selection.  
**Logic:** Filters strikes whose premium/delta/theta ≥ Start Range.  
**Type:** Number  
**Default Value:** 10  
**Validation:**

- Enabled only when Strike Type \= Premium Range / Delta Range / Theta Range  
-  Must be positive  
- Must be less than End Range

**Example:** 10  
**DB Field Name:** premium\_start\_range  
**Execution Context:** Used as lower bound during range filtering.  
---

### **7.3 End Range**

**Description:** Upper threshold for strike selection.  
**Logic:** Filters strikes whose premium/delta/theta ≤ End Range.  
**Type:** Number  
**Default Value:** 20  
**Validation:**

- Enabled only for Premium/Delta/Theta Range  
- Must be positive  
- Must be greater than Start Range

**Example:** 20  
**DB Field Name:** premium\_end\_range  
**Execution Context:** Used as upper bound during range filtering.  
---

### **7.4 Direction**

**Description:** Direction for strike filtering (ITM/OTM/BOTH).  
**Logic:** Filters strikes based on distance from ATM.  
**Type:** Dropdown  
**Default Value:** BOTH  
**Validation:** Allowed Values:

- BOTH  
- ITM  
- OTM  
   Applies when Strike Type \= Premium Range / Delta Range / Theta Range / Nearest Premium / Nearest Delta / Nearest Theta

**Example:** OTM  
**DB Field Name:** strike\_direction  
**Execution Context:** Refines strike selection after range checks.  
---

### **7.5 Condition**

**Description:** Match condition for nearest strike models.  
**Logic:** Determines whether nearest strike should be chosen freely or filtered first by \>= or \<= condition.  
**Type:** Dropdown  
**Default Value:** Any  
**Validation:** Allowed Values:

- Any  
- AboveEqual (\>=)  
- BelowEqual (\<=)  
   Applies only to:  
- Strike by Nearest Premium  
- Strike by Nearest Delta  
- Strike by Nearest Theta

**Example:** AboveEqual (\>=)  
**DB Field Name:** strike\_condition  
**Execution Context:** Controls how nearest strike is matched to metric.  
---

### **8\. Target By**

**Description:** Select how leg target is calculated (money, points, %, delta, theta, range).  
**Logic:** Determines which metric Trading Server monitors to close the leg.  
**Type:** Dropdown  
**Default Value:** Target by Money  
**Validation:** Allowed Values:

* Target by Money  
* Target by Point  
* Target by Point (%)  
* Target by Delta  
* Target by Delta (%)  
* Target by Theta  
* Target by Theta (%)  
* Target by Range High/Low

**Example:** Target by Point  
**DB Field Name:** target\_by  
**Execution Context:** Trading Server checks P\&L or price movement as per selected metric.  
---

### **8.1 Target Value**

**Description:** Numeric target value based on selected Target By type.  
**Logic:** 0 \= No target  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0  
**Example:** 2500  
**DB Field Name:** target  
**Execution Context:** Triggers sqroff or target action.  
---

### **9\. Profit Locking & Trailing**

(Parent Setting – individual parameters below)  
**Description:** Enable profit locking and trailing for this leg.  
**Logic:** When profit reaches specified levels, system locks profit and optionally trails it upward.  
**Type:** Group setting (Number fields)  
**Default Value:** All zeros → feature disabled  
**Validation:** All values must be ≥ 0  
**Example:** If Profit Reaches 5000, Lock 2500  
**DB Field Name:** (uses individual fields below)  
**Execution Context:** Trading Server locks profits and trails based on real-time P\&L.  
---

### **9.1 If Profit Reaches**

**Description:** Threshold to activate profit-locking.  
**Logic:** When profit ≥ this amount, lock rule becomes active.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 5000  
**DB Field Name:** if\_profit\_reaches  
**Execution Context:** Enables locking once threshold hit.  
---

### **9.2 Lock Minimum Profit**

**Description:** Minimum profit to protect when lock is active.  
**Logic:** If P\&L falls below this value after lock activation, system squres off.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0 (negative allowed if user wants)  
**Example:** 2500  
**DB Field Name:** lock\_minimum\_profit  
**Execution Context:** Defines protected profit floor.  
---

### **9.3 Then Every Increase in Profit By**

**Description:** Profit increase needed to trigger next trail.  
**Logic:** Each increase shifts the lock level upward.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 500  
**DB Field Name:** increse\_in\_profit\_by  
**Execution Context:** Determines when trailing step activates.  
---

### **9.4 Trail Profit By**

**Description:** Amount by which locked profit should be trailed.  
**Logic:** New lock profit \= previous lock \+ trail profit by.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 200  
**DB Field Name:** trail\_profit\_by  
**Execution Context:** Updates lock value.  
---

### **9.5 No of Time Trail**

**Description:** Maximum number of trailing cycles.  
**Logic:** 0 \= unlimited trailing.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 5  
**DB Field Name:** no\_of\_time\_trail\_tp  
**Execution Context:** Limits trailing adjustments.  
---

### **10\. Action on Target**

**Description:** Define what to do when this leg hits its target.  
**Logic:** Allows chaining legs: execute idle leg, reenter same leg, or sqroff another leg.  
**Type:** Dropdown  
**Default Value:** Execute Leg  
**Validation:**  
 Allowed Values:

* Execute Leg  
* Reenter Leg  
* Sqroff Leg

**Example:** Reenter Leg  
**DB Field Name:** action\_on\_target  
**Execution Context:** Trading Server performs specified action on target hit.  
---

### **10.1 Leg No**

**Description:** Leg number to execute/reenter/sqroff when target is hit.  
**Logic:** Must reference an idle leg.  
**Type:** Dropdown (Idle Legs Only)  
**Default Value:** First idle leg  
**Validation:** Must be an idle leg  
**Example:** 3  
**DB Field Name:** action\_on\_target\_leg\_no  
**Execution Context:** Determines which leg executes on target.  
---

### **10.2 Delay (Sec)**

**Description:** Delay before performing the target action.  
**Logic:** After target hits, system waits for defined seconds then acts.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 3  
**DB Field Name:** action\_on\_target\_delay  
**Execution Context:** Server waits before executing target action.  
---

### **11\. SL By**

**Description:** Select how stoploss is calculated (money, points, %, delta, theta, etc.).  
**Logic:** Defines which metric is monitored to trigger stoploss.  
**Type:** Dropdown  
**Default Value:** SL by Money  
**Validation:** Allowed Values:

* SL by Money  
* SL by Point  
* SL by Point (%)  
* SL by Delta  
* SL by Delta (%)  
* SL by Theta  
* SL by Theta (%)  
* SL by Range High/Low

**Example:** SL by Delta  
**DB Field Name:** sl\_by  
**Execution Context:** Trading Server checks selected metric to sqroff leg.  
---

### **11.1 SL Value**

**Description:** Stoploss value based on type.  
**Logic:** 0 \= No SL  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 1500  
**DB Field Name:** sl  
**Execution Context:** Triggers sqroff.  
---

### **12\. Stoploss Trailing**

**Description:** Enable SL trailing based on profit movement.  
**Logic:** SL moves upward/downward when profit increases.  
**Type:** Group (3 numerical sub-fields)  
**Default Value:** All values 0 → feature disabled  
**Validation:**\= 0  
**Example:** Increase 1000, Trail 500  
**DB Field Name:** Sub-fields below  
**Execution Context:** Dynamic adjustment of SL.  
---

### **12.1 Increase Profit By**

**Description:** Profit threshold to trigger SL trail.  
**Logic:** Trail activates when profit ≥ this.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 1000  
**DB Field Name:** trail\_sl\_market\_move  
**Execution Context:** Triggers SL trail.  
---

### **12.2 Trail SL By**

**Description:** Amount to trail SL each time.  
**Logic:** New SL \= Old SL \+ Trail SL By.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 500  
**DB Field Name:** trail\_sl\_move  
**Execution Context:** SL updated by this step.  
---

### **12.3 No of Time Trail**

**Description:** Maximum number of SL trailing cycles.  
**Logic:** 0 \= unlimited  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 5  
**DB Field Name:** no\_of\_time\_trail\_sl  
**Execution Context:** Limits how many times SL can trail.  
---

### **13\. Action on SL**

**Description:** Define what happens when this leg hits its SL.  
**Logic:** Controls hedging, reentry, or sqroff for related legs.  
**Type:** Dropdown  
**Default Value:** Execute Leg  
**Validation:** Allowed Values:

* Execute Leg  
* Reenter Leg  
* Sqroff Leg

**Example:** Execute Leg  
**DB Field Name:** action\_on\_sl  
**Execution Context:** Trading Server reacts to SL hit accordingly.  
---

### **13.1 Leg No**

**Description:** Leg to execute/reenter/sqroff on SL hit.  
**Logic:** Must be an idle leg.  
**Type:** Number (Dropdown)  
**Default Value:** First idle leg  
**Validation:** Must reference idle leg.  
**Example:** 4  
**DB Field Name:** action\_on\_sl\_leg\_no  
**Execution Context:** Defines target of SL action.  
---

### **13.2 Delay (Sec)**

**Description:** Delay before executing the SL action.  
**Logic:** System waits after SL before acting.  
**Type:** Number  
**Default Value:** 0  
**Validation:**\= 0  
**Example:** 3  
**DB Field Name:** action\_on\_target\_delay  
**Execution Context:** Delay applied before SL action.  
---

### **14\. Wait & Trade**

**Description:** Enable movement-based entry (Up %, Down %, Up pts, Down pts).  
**Logic:** Leg executes only when price moves by specified % or points.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** is\_wait\_and\_trade  
**Execution Context:** Trading Server monitors movement before entering leg.  
---

### **14.1 Wait & Trade Direction**

**Description:** Select direction and type of movement trigger.  
**Logic:** Controls whether entry waits for upward/downward move in percentage or points.  
**Type:** Dropdown  
**Default Value:** Up %  
**Validation:** Allowed Values:

* Up %  
* Down %  
* Up pts  
* Down pts

**Example:** Down pts  
**DB Field Name:** wait\_for  
**Execution Context:** Trading Server monitors price movement accordingly.  
---

### **14.2 Wait & Trade Value**

**Description:** Movement value in % or points.  
**Logic:** Entry happens when movement meets or exceeds this value.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be positive  
**Example:** 50  
**DB Field Name:** wait\_value  
**Execution Context:** Movement threshold compared to this value.  
---

### **15\. Execute on Range Breakout**

**Description:** Execute this leg specifically on breakout of range high or low.  
**Logic:** Entry depends fully on breakout conditions defined in Main → Range Breakout.  
**Type:** Boolean  
**Default Value:** False  
**Validation:**

* Enabled only when Main → Range Breakout \= True

**Example:** True  
**DB Field Name:** is\_wait\_and\_trade  
 (**Note:** this DB name conflicts with Wait & Trade; your API must correct this)  
**Execution Context:** Trading Server executes this leg only on breakout direction trigger.

# Advance Parameters

## **1\. Master Target By**

**Description:** Select how the overall master target for the strategy will be calculated – based on combined profit or combined premium of all legs.  
**Logic:** When “Combined Profit” is selected, the system monitors the net MTM profit across all active legs.  
 When “Combined Premium” is selected, the system monitors the sum of the premiums of all active legs.  
 This parameter only defines the metric used to evaluate the master target; the actual numeric threshold is defined in **Master Target Value**.  
**Type:** Dropdown (String)  
**Default Value:** Combined Profit  
**Validation:** Allowed Values:

* Combined Profit  
* Combined Premium

**Example:** Combined Profit  
**DB Field Name:** target\_by  
**Execution Context:** The trading engine uses this selection to interpret Master Target Value as either total profit or total premium while evaluating when the master target is hit.  
---

## **1.1 Master Target Value**

**Description:** Define the numeric threshold for the master target based on the selected method in “Master Target By”.  
**Logic:** If the selected mode is Combined Profit, this value represents the total net profit (in currency) at which the strategy should consider master target achieved.  
 If the selected mode is Combined Premium, this value represents the total combined premium value.  
 If this value is set to 0, master target is considered disabled.  
**Type:** Number  
**Default Value:** 0  
**Validation:**

* Must be 0 or a positive number  
* 0 means no master target

**Example:** 5000  
**DB Field Name:** intraday\_target  
**Execution Context:** The trading engine continuously compares the chosen master metric (profit or premium) against this value to decide when the master target condition is met.  
---

## **2\. Profit Locking & Trailing (Master Level)**

**Description:** Configure profit locking and trailing rules on the total combined profit of all legs at strategy level.  
**Logic:** When the overall strategy profit reaches the “If Profit Reaches” value, the system locks a minimum profit level. As profit increases further, the locked profit level can be trailed upwards based on “Every Increase in Profit By” and “Trail Profit By”, up to a maximum number of trails.  
**Type:** Group of Number fields  
**Default Value:** All fields \= 0 (means feature disabled)  
**Validation:** Each field under this group must be 0 or a positive number.  
**Example:** If Profit Reaches \= 5000, Lock Minimum Profit \= 2500, Every Increase in Profit By \= 500, Trail Profit By \= 200, No of Time Trail \= 5  
**DB Field Name:** if\_profit\_reaches, lock\_minimum\_profit, increse\_in\_profit\_by, trail\_profit\_by, no\_of\_time\_trail\_tp  
**Execution Context:** Used at strategy level to protect and trail overall profit irrespective of individual leg targets.  
---

### **2.1 If Profit Reaches**

**Description:** Define the total profit level at which master profit locking should start.  
**Logic:** Once total strategy profit reaches or exceeds this value, the system will start locking profit based on “Lock Minimum Profit”.  
**Type:** Number  
**Default Value:** 0  
**Validation:**

* Must be 0 or a positive number  
* 0 means no master profit locking

**Example:** 5000  
**DB Field Name:** if\_profit\_reaches  
**Execution Context:** Acts as the activation trigger for master profit locking and trailing logic.  
---

### **2.2 Lock Minimum Profit**

**Description:** Define the minimum profit that should be protected once the master profit locking is activated.  
**Logic:** After activation, if combined profit falls back down to or below this minimum lock value, all legs are squared off to protect this locked profit level.  
**Type:** Number  
**Default Value:** 0  
**Validation:**Must be 0 or a positive/negative number  
 (negative is allowed if the user wants to lock a reduced loss level instead of profit)  
**Example:** 2500  
**DB Field Name:** lock\_minimum\_profit  
**Execution Context:** Represents the minimum total P\&L that the system will try to preserve at strategy level once locking is active.  
---

### **2.3 Then Every Increase in Profit By**

**Description:** Define the profit increment after which the system should trail the locked profit.  
**Logic:** Each time the total profit increases by this amount from the last trail level, the system will adjust the locked profit upwards by the value specified in “Trail Profit By”.  
**Type:** Number  
**Default Value:** 0  
**Validation:**

* Must be 0 or a positive number  
* 0 means no trailing, only one-time locking

**Example:** 500  
**DB Field Name:** increse\_in\_profit\_by  
**Execution Context:** Used as the step distance for successive adjustments of the locked profit level at master scope.  
---

### **2.4 Trail Profit By**

**Description:** Define the amount by which the locked profit will be increased on each trailing event.  
**Logic:** Whenever the master profit increases by the configured step (“Every Increase in Profit By”), the system raises the locked profit by this amount.  
**Type:** Number  
**Default Value:** 0  
**Validation:**Must be 0 or a positive number

* 0 means no incremental trailing, even if “Every Increase in Profit By” is configured

**Example:** 200  
**DB Field Name:** trail\_profit\_by  
**Execution Context:** Controls how much the protected profit floor moves up with each successful trailing cycle.  
---

### **2.5 No of Time Trail**

**Description:** Define the maximum number of times master profit can be trailed.  
**Logic:** After the locked profit has been trailed this many times, no further trailing adjustments will be made.  
 If set to 0, trailing can continue unlimited times.  
**Type:** Number  
**Default Value:** 0  
**Validation:**Must be 0 or a positive number  
**Example:** 5  
**DB Field Name:** no\_of\_time\_trail\_tp  
**Execution Context:** Limits the number of trailing operations performed on master-level profit.  
---

## **3\. Action on Master Target**

**Description:** Define the action to be taken once the master target condition is reached.  
**Logic:** When the master target is achieved, all open legs are squared off and the strategy is reexecuted again based on the same leg parameters, controlled by reexecution count and delay.  
**Type:** Dropdown (single option)  
**Default Value:** Reexecute  
**Validation:** Allowed Values:

* Reexecute

**Example:** Reexecute  
**DB Field Name:** action\_on\_target  
**Execution Context:** Used by the trading engine to decide what to do immediately after the master target is hit.  
---

### **3.1 No of Times Reexecute**

**Description:** Define how many times the strategy should reexecute when master target is achieved.  
**Logic:** On each master target event, the strategy can be restarted. After this count is reached, reexecution will stop.  
 If set to 0, reexecution is unlimited during the active session.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 3  
**DB Field Name:** no\_of\_intraday\_cycle  
**Execution Context:** Controls maximum number of reexecution cycles allowed after master target events.  
---

### **3.2 Delay (Sec)**

**Description:** Define the delay in seconds before reexecuting the strategy after master target is reached.  
**Logic:** After strategy exits on master target, the system waits for this many seconds before reentering as per leg parameters.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 10  
**DB Field Name:** intraday\_cycle\_delay  
**Execution Context:** Used by the trading engine to introduce a cooling-off period between exit and the next reexecution cycle.  
---

## **4\. Master SL By**

**Description:** Select how the master stoploss is evaluated at strategy level.  
**Logic:** When “Combined Loss” is selected, the system compares total loss (negative MTM) against Master SL Value.  
 When “Combined Premium” is selected, the system compares total combined premium against Master SL Value.  
**Type:** Dropdown (String)  
**Default Value:** Combined Loss  
**Validation:** Allowed Values:

* Combined Loss  
* Combined Premium

**Example:** Combined Loss  
**DB Field Name:** sl\_by  
**Execution Context:** Determines the metric used for checking overall stoploss condition for the strategy.  
---

## **4.1 Master SL Value**

**Description:** Define the numeric stoploss value for the overall strategy.  
**Logic:** If Master SL By \= Combined Loss → this is the maximum total loss allowed.  
 If Master SL By \= Combined Premium → this is the threshold on combined premium.  
 If set to 0, master stoploss is disabled.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 3000  
**DB Field Name:** intraday\_sl  
**Execution Context:** As soon as the chosen stoploss metric hits this value, master stoploss is considered triggered and the configured “Action on Master SL” will execute.  
---

## **5\. Stoploss Trailing (Master Level)**

**Description:** Configure how the master stoploss should move as the strategy becomes profitable.  
**Logic:** When total profit increases by the configured step, the master stoploss is trailed closer to the current profit levels, thereby reducing risk and preserving profits.  
**Type:** Group of Number fields  
**Default Value:** All fields \= 0 (feature disabled)  
**Validation:** All fields must be 0 or positive.  
**Example:** Increase Profit by 1000, Trail SL by 500, No of Time Trail \= 5  
**DB Field Name:** profit\_move, sl\_move, no\_of\_trail\_sl  
**Execution Context:** Used to dynamically adjust the global stoploss as the strategy moves further into profit.  
---

### **5.1 Increase Profit by**

**Description:** Define the profit step required to trigger master SL trailing.  
**Logic:** Once cumulative profit increases by this amount from the last SL update level, the master SL is trailed by the configured value in “Trail SL by”.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
 0 means no trailing.  
**Example:** 1000  
**DB Field Name:** profit\_move  
**Execution Context:** Acts as the profit movement trigger for master SL trailing at strategy level.  
---

### **5.2 Trail SL by**

**Description:** Define how much the master stoploss should be moved on each trailing event.  
**Logic:** Each time the trigger condition is met, master SL is shifted by this amount towards the current profit levels.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 500  
**DB Field Name:** sl\_move  
**Execution Context:** Determines the adjustment size in the master stoploss when trailing is active.  
---

### **5.3 No of Time Trail**

**Description:** Define how many times master stoploss is allowed to trail.  
**Logic:** Once the count of trailing events reaches this value, further trailing will stop.  
 0 means unlimited SL trailing events are allowed.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 5  
**DB Field Name:** no\_of\_trail\_sl  
**Execution Context:** Limits the total number of trailing steps applied to the master stoploss.  
---

## **6\. Action on Master SL**

**Description:** Define what action the system should take when master stoploss is hit.  
**Logic:** When master SL condition is met, all legs are squared off and the strategy can be reexecuted again as per the reexecute settings.  
**Type:** Dropdown (single option)  
**Default Value:** Reexecute  
**Validation:** Allowed Values:

* Reexecute

**Example:** Reexecute  
**DB Field Name:** action\_on\_sl  
**Execution Context:** Trading engine uses this as the behavior once master stoploss is triggered.  
---

### **6.1 No of Times Reexecute**

**Description:** Define how many times the strategy should reexecute after master stoploss is triggered.  
**Logic:** Once this reexecute count is exhausted, no more reexecution will occur after SL hits.  
 0 means unlimited reexecution allowed.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 2  
**DB Field Name:** no\_of\_reexecute\_on\_sl  
**Execution Context:** Controls the number of strategy restart cycles after master SL events.  
---

### **6.2 Delay (Sec)**

**Description:** Define the delay in seconds before reexecuting the strategy after master SL is hit.  
**Logic:** After strategy exit on master SL, the system waits for this many seconds before entering again.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 15  
**DB Field Name:** reexecute\_delay\_on\_sl  
**Execution Context:** Used to avoid immediate reentry after a master SL, providing a cool-off period.  
---

## **7\. Sqroff before expiry days**

**Description:** Enable or disable automatic square-off of all legs a configurable number of days before contract expiry.  
**Logic:** When enabled, positions are not held until final expiry. Instead, they are closed earlier as per “No of Days” and “Sqroff Time”, which helps to avoid last-day volatility or illiquidity risk.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed Values: True / False  
 Applicable only when Trading Type is Positional.  
**Example:** True  
**DB Field Name:** (N/A for flag, but related to sqroff\_before\_expiry\_days and sqroff\_time)  
**Execution Context:** Used to activate or deactivate pre-expiry exit logic for positional strategies.  
---

### **7.1 No of Days**

**Description:** Define how many calendar days before expiry all legs should be squared off.  
**Logic:** If set to 0, square-off may happen on the day of expiry itself at defined time.  
 If \> 0, legs are closed that many days before expiry date.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be 0 or a positive number.  
**Example:** 2  
**DB Field Name:** sqroff\_before\_expiry\_days  
**Execution Context:** Trading engine uses instrument expiry date minus this value to compute pre-expiry exit date.  
---

### **7.2 Sqroff Time**

**Description:** Time of day at which pre-expiry square-off will occur.  
**Logic:** On the computed pre-expiry date (expiry minus “No of Days”), all open legs are squared off at this time.  
**Type:** Time (HH:mm:ss)  
**Default Value:** 15:15:00  
**Validation:** Must be within exchange trading hours.  
**Example:** 15:10:00  
**DB Field Name:** sqroff\_time  
**Execution Context:** Defines the exact timestamp on pre-expiry day when strategy exit is executed.  
---

## **8\. Working Days**

**Description:** Select the weekdays on which the strategy is allowed to run.  
**Logic:** The strategy will only execute entries on enabled days. If a day flag is disabled, no new trades will be started on that weekday, but existing positions may still be managed (as per system design).  
**Type:** Multiple Boolean Flags  
**Default Value:** MON, TUE, WED, THU, FRI \= True  
 SAT \= False  
**Validation:** Allowed values:

* MON  
* TUE  
* WED  
* THU  
* FRI  
* SAT

**Example:**  
 MON–FRI enabled, SAT disabled.  
**DB Field Name:**  
 run\_mon, run\_tue, run\_wed, run\_thu, run\_fri, run\_sat  
**Execution Context:** Checked before triggering any new entries for the day.  
---

## **9\. VIX Filter**

**Description:** Enable or disable the filter for taking positions based on volatility index (VIX) range.  
**Logic:** When enabled, the system will only allow strategy entries if the current VIX value lies within the defined start and end range. This helps to avoid trading when volatility is too high or too low.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed Values: True / False  
**Example:** True  
**DB Field Name:** enable\_vix\_filter  
**Execution Context:** When this flag is true, VIX Start Range and VIX End Range are evaluated before placing any new leg entries.  
---

### **9.1 VIX Start Range**

**Description:** Define the lower bound of the allowed VIX range.  
**Logic:** If current VIX is below this value, no new positions will be taken. Valid only when VIX Filter is enabled.  
**Type:** Number  
**Default Value:** 1  
**Validation:**

* Must be a positive number  
* Must be less than VIX End Range

**Example:** 12  
**DB Field Name:** vix\_start\_value  
**Execution Context:** Represents the minimum volatility level at which strategy entries are permitted.  
---

### **9.2 VIX End Range**

**Description:** Define the upper bound of the allowed VIX range.  
**Logic:** If current VIX is above this value, no new positions will be taken. Valid only when VIX Filter is enabled.  
**Type:** Number  
**Default Value:** 5  
**Validation:**

* Must be a positive number  
* Must be greater than VIX Start Range

**Example:** 18  
**DB Field Name:** vix\_end\_value *(you can map as vix\_end\_value in DB; if existing name is different, adjust accordingly)*  
**Execution Context:** Represents the maximum volatility level at which new entries are allowed for the strategy.  
---

## **10\. Enable TP/SL monitoring on paused strategy**

**Description:** Enable or disable execution of target/stoploss when the strategy is in paused state.  
**Logic:** When enabled, even if the strategy is paused (no new entries), the system will still monitor existing positions and execute TP/SL exits. When disabled, TP/SL conditions may not be processed while paused (as per your server implementation).  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed Values: True / False  
**Example:** True  
**DB Field Name:** enable\_tp\_sl\_on\_pause\_strategy  
**Execution Context:** Controls whether exit logic remains active during pause mode.  
---

## **11\. Sqroff all legs (on any single leg close by TP/SL)**

**Description:** Enable or disable automatic square-off of all legs when any single leg hits its target or stoploss.  
**Logic:** When enabled, if one leg hits TP or SL and closes, the system will square off all other open legs in the same strategy immediately.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed Values: True / False  
**Example:** True  
**DB Field Name:** sqroff\_all\_legs  
**Execution Context:** Used as global exit behavior when any leg hits its TP or SL.  
---

## **12\. Sqroff position on rejection on any leg**

**Description:** Enable or disable automatic square-off of all open legs when any new leg trade is rejected.  
**Logic:** When enabled, if during order placement of any leg the order gets rejected (e.g., margin issue, risk limit, etc.), the system will immediately square off all open legs to avoid unhedged or partial positions.  
**Type:** Boolean  
**Default Value:** False  
**Validation:** Allowed Values: True / False  
**Example:** True  
**DB Field Name:** pause\_and\_sqroff\_trading\_on\_margin\_exeed  
**Execution Context:** Acts as a safety mechanism to avoid incomplete or unbalanced strategies in case of leg rejections.  
---

## **13\. Required Margin**

**Description:** Estimated total margin required to run this strategy.  
**Logic:** This is an informational field used for display and reporting purposes only. It does not affect execution logic directly.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be a positive number.  
**Example:** 150000  
**DB Field Name:** required\_margin  
**Execution Context:** Shown to the user for planning, risk control, and ROI calculation. It can also be used by reports and analytics but is not an execution condition by itself.

# Description Parameters

## **1\. Short Description**

**Description:** A brief one-line summary written by the user to identify the strategy easily in listings and reports.  
**Logic:** Purely informational.  
 No impact on execution, signals, leg creation, target, or SL.  
 This is only stored as a note for the trader’s reference.  
**Type:** Single-line Text Input  
**Default Value:** Blank  
**Validation:** Optional field  
 Recommended max length 100–150 characters  
 No logic validation required  
**Example:** “BNF hedge model with re-entry and master MTM control.”  
**DB Field Name:** short\_description  
**Execution Context:** Displayed only for user reference (Strategy List, Detail View, Copilot Preview).  
 Not used anywhere in live execution or automation engine.  
---

## **2\. Detailed Description**

**Description:** A longer explanation entered by the user to document strategy idea, reasoning, notes, hedge logic, and usage style for future reference.  
**Logic:** Informational only.  
 Does not affect how the strategy executes.  
 Used only as a user-level description for understanding and record keeping.  
**Type:** Multi-line Text Area  
**Default Value:** Blank  
**Validation:** Optional field  
 Can be long text / bullet points / notes – no restrictions  
 No validation conditions  
**Example:** “This strategy enters CE-PE hedge, manages MTM using master target and trailing. Suitable for mid-volatility days. VIX filter recommended 12-18.”  
**DB Field Name:** detailed\_description  
**Execution Context:** Displayed only for reading by the user & Copilot.  
 Has no role in execution, re-entry, MTM logic, SL, TP, or hedging mechanics.

# Help

### **🔹 TAB 1: MAIN PARAMETERS – HELP**

**Strategy Name**  
Give a unique name to identify this strategy. It is only for your reference and reports – it does not change execution.

**Underlying Exchange**  
Select the exchange to trade on: NSE, NFO, BFO, BSE, MCX, or CDS.  
This controls which segments and symbols are available in the next fields.

**Underlying Segment**  
Select segment under the chosen exchange (e.g. FUT, OPT, EQ).  
This defines whether you will trade futures, options, or stocks for the underlying.

**Underlying Symbol**  
Choose the main symbol (e.g. BANKNIFTY, NIFTY, RELIANCE).  
All leg strike selection for options is based on this underlying price.

**Trading Type**  
Choose **Intraday** or **Positional**.  
Intraday: positions are squared off at Sqroff Time.  
Positional: positions continue until contract expiry (or pre-expiry sqroff if enabled).

**Product**  
Select product type: MIS, NRML, CNC, or MTF (as supported by broker).  
This affects margin usage and whether positions can be carried forward.

**Start Time**  
Time from which the strategy is allowed to start taking entries (HH:mm:ss).  
Legs will enter at or after this time, considering wait & trade and range breakout conditions.

**Sqroff Time**  
Time to exit all intraday positions (HH:mm:ss).  
Used only when Trading Type is Intraday.

**Range Breakout**  
Enable or disable range breakout-based entries.  
When enabled, legs enter only if price breaks the calculated high/low range between Start Time and Range End Time.

**Range End Time**  
End time for building the breakout range (HH:mm:ss).  
High/low between Start Time and Range End Time is used as breakout reference.

**BTST/STBT**  
Enable or disable BTST/STBT.  
When enabled (and Trading Type is Positional), system carries the position overnight and squares off after the configured Gap Days.

**Gap Days**  
Number of days to hold BTST/STBT positions.  
Position will be squared off after this many days from entry.

**Combined Premium Entry**  
Enable or disable entry based on **total combined premium** condition.  
When enabled, legs enter only if the total premium meets the defined Total Premium value.

**Total Premium**  
Total combined premium value to be used when Combined Premium Entry is enabled.  
Legs execute once this premium condition is satisfied.

### **🔹 TAB 2: LEG PARAMETERS – HELP**

**Idle**  
Mark this leg as Idle or Active.  
Idle legs do not enter at start time; they act only when triggered by other leg actions (e.g. Action on Target/SL).

**Trade Side**  
Select **BUY** or **SELL** for this leg.  
Defines whether you are long or short in this particular contract.

**Lots**  
Number of lots to trade for this leg.  
Final quantity \= Lots × Exchange lot size.

**Segment (Leg)**  
Choose **OPT**, **FUT**, or **Stock** for this leg.  
Controls whether the leg trades options, futures or the underlying stock.

**Expiry**  
Select expiry: **Current Week, Week 1, Week 2, Current Month, Month 1, Month 2**.  
System will pick contracts according to this relative expiry selection.

**Option Type**  
Select **CE** (Call) or **PE** (Put).  
Enabled only when Segment is OPT.

**Strike Selection**  
Choose how to select the option strike:

* Strike by ATM Value  
* Strike by ATM %  
* Strike by Premium Range  
* Strike by Nearest Premium  
* Strike by Delta Range  
* Strike by Nearest Delta  
* Strike by Theta Range  
* Strike by Nearest Theta  
   Strike, ATM, premium, delta or theta parameters below must match your selection.

**ATM Value**  
Used when **Strike by ATM Value** is selected.  
Pick offset like ATM \+200, \+100, 0, –100, –200 to move up/down from current ATM strike.

**ATM %**  
Used when **Strike by ATM %** is selected.  
Pick offset like ATM % 1.0, 0.75, 0.50, 0.25, 0, –0.25, –0.50, –0.75, –1.0 to shift strike by percentage from ATM.

**Start Range**  
Used when selecting by Premium Range / Delta Range / Theta Range.  
Defines lower bound of the range. Strike will be chosen within this range.

**End Range**  
Used with Premium/Delta/Theta Range selection.  
Defines upper bound of the range. Must be greater than Start Range.

**Direction**  
Used for range/nearest based selection.  
Choose **BOTH**, **ITM**, or **OTM** to decide whether to search in-the-money, out-of-the-money, or either side.

**Condition**  
Used for “Strike by Nearest Premium / Delta / Theta”.  
Choose condition: **Any**, **AboveEqual (\>=)**, or **BelowEqual (\<=)** to refine how nearest value is selected.

**Target By (Leg Target)**  
Select type of leg target:

* Target by Money  
* Target by Point  
* Target by Point (%)  
* Target by Delta / Delta (%)  
* Target by Theta / Theta (%)  
* Target by Range High/Low  
   Leg will exit when target is reached as per chosen mode.

**Target Value**  
Numeric value for leg target as per “Target By”.  
0 means no target for this leg.

**Profit Locking & Trailing (Leg)**  
Enable locking and trailing of **this leg’s** profit once it reaches a certain level.  
Requires setting If Profit Reaches, Lock Minimum Profit, Every Increase in Profit By, Trail Profit By and No of Time Trail.

**If Profit Reaches (Leg)**  
Profit level at which leg-level profit locking starts.

**Lock Minimum Profit (Leg)**  
Minimum profit to protect for this leg once locking is active.  
Leg will exit if profit falls back to this level after lock.

**Then Every Increase in Profit By (Leg)**  
Profit increment after which locked profit is trailed further.

**Trail Profit By (Leg)**  
How much to increase locked profit on each trail.

**No of Time Trail (Leg)**  
Number of times profit locking can trail for this leg.  
0 \= unlimited trailing.

**Action on Target (Leg)**  
What to do when **this leg’s target** is hit:

* Execute Leg → Trigger another idle leg  
* Reenter Leg → Re-enter same idle leg when price comes again  
* Sqroff Leg → Exit leg based on selected idle leg number.

**Action on Target – Leg No**  
Choose which idle leg number is affected by “Action on Target”.  
Used when action is Execute/Reenter/Sqroff selected leg.

**Action on Target – Delay (Sec)**  
Delay before the Action on Target is executed.  
Useful to avoid immediate next trade.

**SL By (Leg)**  
Select leg stoploss type:

* SL by Money  
* SL by Point  
* SL by Point (%)  
* SL by Delta / Delta (%)  
* SL by Theta / Theta (%)  
* SL by Range High/Low

**SL Value (Leg)**  
Numeric level for leg stoploss as per “SL By”.  
0 means no SL for this leg.

**Stoploss Trailing (Leg)**  
Enable SL trailing for this leg.  
Requires Increase Profit by, Trail SL by, and No of Time Trail.

**Increase Profit by (SL Trail – Leg)**  
Profit movement needed to trigger SL trailing for this leg.

**Trail SL by (Leg)**  
How much to move SL each time trailing is triggered.

**No of Time Trail (SL – Leg)**  
Maximum number of SL trail updates for this leg.  
0 \= unlimited trail.

**Action on SL (Leg)**  
What to do when this leg hits SL:

* Execute Leg  
* Reenter Leg  
* Sqroff Leg  
   Uses defined idle leg number and delay similar to Action on Target.

**Action on SL – Leg No**  
Idle leg number on which the SL action will be applied (execute, reenter, sqroff).

**Action on SL – Delay (Sec)**  
Delay (in seconds) before the configured SL action starts.

**Wait & Trade**  
Enable price-movement based entry for this leg.  
Leg will wait for up or down move (percentage or points) before executing.

**Wait & Trade Direction**  
Select movement type: **Up %**, **Down %**, **Up pts**, **Down pts**.  
Defines whether the leg fires on upward or downward move, and in % or points.

**Wait & Trade Value**  
Movement amount (percentage or points) required before this leg is executed.

**Execute on Range Breakout (Leg)**  
Use range breakout signal to execute this leg.  
Leg will enter only when range high or range low is broken as configured in Main tab.

### **🔹 TAB 3: ADVANCE PARAMETERS – HELP**

**Master Target By**  
Choose whether the master target is based on **Combined Profit** or **Combined Premium** of all legs.

**Master Target Value**  
Define the numeric master target threshold.  
When combined metric reaches this value, master target is considered hit.

**Profit Locking & Trailing (Master)**  
Enable strategy-level profit locking and trailing on total MTM.  
Requires If Profit Reaches, Lock Minimum Profit, Increase in Profit, Trail Profit By and No of Time Trail.

**If Profit Reaches (Master)**  
Total profit level where master profit locking starts.

**Lock Minimum Profit (Master)**  
Minimum profit to be protected for the whole strategy after locking is active.

**Then Every Increase in Profit By (Master)**  
Profit increment after which locked master profit is trailed further.

**Trail Profit By (Master)**  
Amount by which locked master profit is increased on each trailing event.

**No of Time Trail (Master)**  
Maximum number of master profit trailing cycles.  
0 \= unlimited trailing.

**Action on Master Target**  
Action after master target hit – strategy exits all legs and reexecutes as per configured cycles.

**No of Times Reexecute (Master Target)**  
Number of master target cycles allowed.  
0 \= unlimited reexecution.

**Delay (Sec) – Master Target**  
Delay time (in seconds) before reexecuting the strategy after master target exit.

**Master SL By**  
Choose how master stoploss is checked: **Combined Loss** or **Combined Premium**.

**Master SL Value**  
Overall loss/premium threshold for the strategy.  
When hit, master stoploss is triggered.

**Stoploss Trailing (Master)**  
Enable trailing of master stoploss based on profit moves.  
Uses Increase Profit by, Trail SL by, and No of Time Trail.

**Increase Profit by (SL Trail – Master)**  
Profit growth required to move master SL further into profit.

**Trail SL by (Master)**  
Value added to master SL at each trail.

**No of Time Trail (SL – Master)**  
Maximum number of times master SL can be trailed.  
0 \= unlimited.

**Action on Master SL**  
What to do when master SL is hit – exit all legs and reexecute strategy as per settings.

**No of Times Reexecute (Master SL)**  
Number of restart cycles allowed after master SL triggers.  
0 \= unlimited.

**Delay (Sec) – Master SL**  
Pause time before starting new cycle after a master SL exit.

**Sqroff Before Expiry Days**  
Enable or disable pre-expiry exit for positional strategies.  
All legs will be squared off X days before expiry at the given time.

**No of Days (Before Expiry)**  
Number of days before expiry to close all positions.  
0 \= close on expiry day.

**Sqroff Time (Before Expiry)**  
Time of day for pre-expiry square-off.

**Working Days**  
Select weekdays (MON–SAT) on which this strategy is allowed to run.  
Only these days will be considered for starting new entries.

**VIX Filter**  
Enable or disable volatility filter.  
When enabled, entries only happen if VIX is within Start and End range.

**VIX Start Range**  
Lower limit of VIX value to allow trades.  
If VIX is below this, no new entries.

**VIX End Range**  
Upper limit of VIX value to allow trades.  
If VIX is above this, no new entries.

**Enable TP/SL monitoring on paused strategy**  
If enabled, TP/SL will still trigger and close positions even when strategy is paused (no new entries).

**Sqroff all legs (on any single leg close by TP/SL)**  
When enabled, if any one leg hits its TP/SL and closes, all other open legs will also be squared off.

**Sqroff position on rejection on any leg**  
If any new order for a leg is rejected (e.g. margin issue), all existing legs are squared off to avoid unhedged exposure.

**Required Margin**  
Estimated capital required to run this strategy.  
Used for information, ROI and risk calculations only.

**Short Description**  
Short one-line summary of the strategy written by the user for easy identification.

**Detailed Description**  
Complete notes explaining strategy logic and usage, maintained only for user documentation and Copilot understanding.

# FAQ

**Q1. What is the Unified Strategy Builder plugin?**  
A multi-leg strategy engine that creates hedged option positions with consolidated MTM control, re-execution cycles, premium filters, volatility filters and automated TP/SL exit.

**Q3. Can I create straddle, strangle, iron-condor, calendar or ratio spreads here?**  
 Yes — any combination of CE/PE legs, any strike method, any expiry.  
 Full flexibility → Directional, Non-Directional or Neutral.

**Q4. Does this plugin execute trades, or only generate signals?**  
 It executes trades automatically based on leg rules & system checks.

**Q5. Is this suitable only for BankNifty/Nifty?**  
 No — you may use any symbol from exchange segment mapping (Index, Stocks, Futures, FX, MCX if enabled).

**Q6. When will strategy enter positions?**  
 At/after **Start Time**, only if entry conditions (premium, range breakout, VIX, wait & trade triggers) are satisfied.

**Q7. What if Range Breakout is ON but range never breaks?**  
 Then no trades will be taken for that day. System waits only until Range End Time.

**Q8. Can I run this as pure ATM or far OTM strike strategy?**  
 Yes — strike selection is independent per leg (ATM, OTM, ITM, Delta, Premium Range etc.).

**Q9. Can one leg enter first and second later based on price trigger?**  
 Yes. Use **Wait & Trade**, **Action on Target**, **Action on SL**, or **Idle Legs**.

**Q10. Will it re-enter on same strike after exit?**  
 Only if configured through Action on Target/SL Re-enter mode.

**Q11. Can leg target & SL work independently per leg?**  
 Yes. Each leg runs its own TP/SL logic unless global override is enabled in Advance tab.

**Q12. What happens if one leg hits target and other is running?**  
 If **Sqroff all legs on single TP/SL** is OFF → other legs continue.  
 If ON → all legs will exit instantly.

**Q13. How to manage long strangle exits independently?**  
 Set different Target/SL per leg \+ keep full-exit switch OFF in Advance.

**Q14. How many legs are supported?**  
 Unlimited — strategy is event-driven, not leg-limited.

**Q15. Can I do BUY \+ SELL in same expiry?**  
 Yes — hedging intention is the core purpose of this plugin.

**Q16. Which strike selection method is most stable for neutral hedges?**  
 Premium Range & Near-Delta structures are most balanced.

**Q17. When should I use Delta-based strike picking?**  
 When you want controlled directional exposure or Non-Directional Neutral Pairs.

**Q18. What if user selects wrong premium range?**  
 Leg won't enter unless premium exists in the selected range.

**Q19. Can I use different strike logic for each leg?**  
 Yes — every leg is completely independent.

**Q20. What is Master Target?**  
 A combined MTM/Premium profit threshold for full strategy exit.

**Q21. Difference between Leg Target & Master Target?**  
 Leg Target \= Individual exit  
 Master Target \= Overall bookout level for entire combined position

**Q22. Can we disable Master Target?**  
 Yes — set Master Target Value \= 0

**Q23. What happens when master target hits?**  
 All legs exit, then **re-execution starts** as configured.

**Q24. What is Master SL?**  
 A total loss/premium threshold where the entire strategy is squared off.

**Q25. Can Master Target & Master SL run together?**  
 Yes — whichever condition hits first wins.

**Q26. Profit locking vs Stoploss trailing difference?**  
 Locking protects minimum MTM once triggered.  
 Trailing moves lock/SL further forward as profits rise.

**Q27. Will it re-enter automatically after exit?**  
 Yes — if Master Target/SL re-execute count is non-zero.

**Q28. Can I limit number of cycles in a day?**  
 Yes — configure **No of Times Reexecute**.

**Q29. What if I want unlimited run?**  
 Set re-execution count \= 0\.

**Q30. Why do we need delay before re-entry?**  
 To avoid immediate re-entry into whipsaw conditions or same spike.

**Q31. Why exit before expiry?**  
 To avoid gamma spikes, liquidity drops, freak candles.

**Q32. Can positional run till final expiry?**  
 Yes — set **Sqroff Before Expiry Days \= 0**.

**Q33. What does VIX Filter do?**  
 Blocks entries when volatility is outside defined safe range.

**Q34. Which VIX range is normally safe for hedged strategies?**  
 10–20 typical; adjust as per market regime.

**Q35. If VIX goes high after entry, will position exit?**  
 No — VIX only controls new entries, not open positions.

**Q36. What if order is rejected due to margin?**  
 If rejection exit is ON → All positions SQR-OFF instantly to avoid naked exposure.

**Q37. Should I enable "Sqroff all legs on single TP/SL"?**  
 Enable only if your structure must exit as a complete pair/box/iron model.

**Q38. Is margin display mandatory?**  
 No — informative only.

**Q39. Does strategy require user to stay online?**  
 No. Once deployed → fully automated.

**Q40. When will execution stop automatically?**  
 When SL/Target cycles are completed OR market closes OR position forcibly squared off.

**Q41. Can this run every day without manual input?**  
 Yes — as long as cycles remain and conditions are valid.

**Q42. Can I pause the strategy?**  
 Yes — entries stop, but TP/SL execution continues if enabled.

**Q43. No trade executed even after Start Time — Why?**  
 Because conditions (VIX/Premium/Range/WaitTrigger) not satisfied.

**Q44. Strategy entered only 1 leg — why?**  
 Idle or conditional legs wait for trigger.  
 Check Wait & Trade or Action-On-Target logic.

**Q45. Why Master Target triggered early?**  
 Combined MTM hit threshold faster than expected → tighten target or reduce lots.

**Q46. VIX rejected entry even though premium looked good — why?**  
 Because VIX was outside configured range. VIX must satisfy first.

**Q47. Why system square-off everything after rejection?**  
 Fail-safe to prevent naked side exposure.

# Copilot Rulebook

Below is the **FULL “HOW COPILOT SHOULD RESPOND” RULEBOOK** for the Unified Strategy Builder Plugin.

This is a **master AI-instruction document** that completely defines:

* How Copilot must interpret user prompts  
* How Copilot must map natural-language into plugin parameters  
* How Copilot must ask clarifying questions (only when needed)  
* How Copilot must generate strategy output  
* How Copilot must avoid mistakes  
* How Copilot must reference Unified Strategy Builder rules

This will be used internally for training your Copilot OR for BRD as an AI-specification.

---

# **🧠📘 Unified Strategy Builder – COPILOT RESPONSE RULEBOOK**

### ***AI Behavior & Interpretation Logic***

---

# **1️⃣ COPILOT’s PURPOSE**

The Copilot’s job is to **convert trader instructions** (natural language) into a **complete Unified Strategy Builder strategy configuration**:

* Main Parameters  
* Leg Parameters  
* Advance Parameters  
* Description Tab

Copilot must generate **100% valid, executable configurations**, following the plugin field rules.

Copilot should behave like a **trading assistant**, not a chatbot.

---

# **2️⃣ CORE RESPONSIBILITIES**

Copilot must:

### **✔ Understand trading concepts**

Straddles, strangles, ratio spreads, hedged spreads, calendars, iron condors, premium selling, delta hedging, expiry logic, MTM logic, etc.

### **✔ Map every human phrase to corresponding plugin parameters**

Example:  
 “Enter ATM straddle at 9:20 and exit at 3:10 with 1500 stoploss”  
 → 2 legs, ATM strike, CE/PE, Start Time 09:20:00, Sqroff Time 15:10:00, Master SL 1500 etc.

### **✔ Ask only necessary clarifying questions**

If user gives missing or conflicting values.

### **✔ Never violate plugin logic**

Copilot must only use fields available in Unified Strategy Builder.

### **✔ Ensure valid output**

All fields must follow required structure, allowed dropdown values & validations.

---

# **3️⃣ HOW COPILOT MUST INTERPRET NATURAL LANGUAGE**

Below are **interpretation rules**.

---

## **A. Identify Strategy Structure**

Copilot should detect strategy type based on user wording:

* “straddle” → 2 legs, same strike ATM CE \+ ATM PE  
* “strangle” → 2 legs ATM±OTM  
* “iron condor” → 4 legs (2 sell, 2 buy hedges)  
* “ratio spread” → same strike, different lot multiples  
* “hedge” → ensure at least one BUY leg behind SELL legs  
* “calendar spread” → mix monthly expiries

---

## **B. Extract Timing Logic**

Copilot must correctly map:

* “enter at 9:20” → Start Time  
* “exit at 3:15” → Sqroff Time  
* “before expiry” → Sqroff Before Expiry \= X  
* “wait for breakout” → Range Breakout \= ON

---

## **C. Extract MTM Logic**

Copilot should detect:

* “target” \= Master Target Value  
* “combined target” \= Master Target  
* “overall target” \= Master Target  
* “stoploss” \= Master SL  
* “lock profit” \= Profit Locking parameters  
* “trail SL” \= SL Trailing parameters

---

## **D. Extract Strike Logic**

Map natural phrases:

* “ATM CE” → Strike by ATM Value (Offset 0\)  
* “100 points OTM” → ATM Value \+100 for CE, \-100 for PE  
* “0.3 delta put” → Strike by Delta Range / Nearest Delta

* “premium around 100” → Strike by Nearest Premium  
* “upper and lower wings” → OTM protective legs

---

## **E. Extract Quantity Logic**

If user says:

* “1 lot” → Lots \= 1  
* “sell 2 lots and hedge with 1 lot” → legs with different lots  
* “aggressive hedge” → Copilot may choose SELL main \+ BUY far OTM at 25–30% width

---

## **F. Extract Premium Logic**

“enter only when premium crosses 200” → Combined Premium Entry enabled  
 “total premium must be at least 300” → Total Premium \= 300

---

## **G. Extract Volatility Logic**

“trade only when VIX is stable” → VIX filter around 10–20  
 “avoid high VIX days” → set upper limit \~18

---

# **4️⃣ WHEN COPILOT MUST ASK CLARIFYING QUESTIONS**

Only when **critical information is missing**.

Copilot must ask when:

1. Number of legs is unclear  
2. Strategy type is only partially described  
3. Expiry type is missing (weekly/monthly)  
4. Lot size not specified  
5. Strike selection incomplete  
6. Target/SL ambiguous  
7. Time missing

**Examples of clarifying questions:**

* “Do you want ATM or OTM strikes for this hedge?”  
* “Should this be weekly expiry or monthly expiry?”  
* “How many lots do you want to trade per leg?”

---

# **5️⃣ WHEN NOT TO ASK QUESTIONS**

If information can be **reasonably inferred** by rules:

* Straddle → ATM CE \+ ATM PE  
* Strangle → ATM±points or ATM%  
* Iron Condor → standard wings at reasonable distance  
* Directional hedge → SELL ATM \+ BUY far OTM

Copilot should automatically choose defaults **unless user has explicitly prohibited assumptions**.

---

# **6️⃣ OUTPUT FORMAT COPILOT MUST FOLLOW**

Every Copilot output must generate:

### **✔ A full Unified Strategy Builder configuration**

* Tab 1 (Main)  
* Tab 2 (Legs)  
* Tab 3 (Advance)  
* Tab 4 (Description)

### **✔ MUST NOT USE PARAMETERS NOT EXISTING IN THE PLUGIN**

Copilot must strictly follow your PDF fields.

### **✔ MUST ALWAYS ENSURE A VALID STRATEGY**

Example: cannot SELL naked without hedge unless user explicitly instructs.

---

# **7️⃣ RULES FOR MAPPING USER PROMPTS TO PLUGIN FIELDS**

Below are exact mapping behaviors.

---

## **A. Target/Stoploss Mapping**

| User phrase | Plugin mapping |
| ----- | ----- |
| “target 2500” | Master Target By \= Combined Profit; Master Target Value \= 2500 |
| “stoploss 1500” | Master SL By \= Combined Loss; Master SL Value \= 1500 |
| “target per leg” | Leg-level target |
| “trail stoploss” | SL Trailing settings |

---

## **B. Strike Mapping**

| Phrases | Strike Type |
| ----- | ----- |
| “ATM” | Strike by ATM Value offset 0 |
| “100 points OTM” | ATM Offset 100 |
| “delta 0.3 put” | Strike by Delta (nearest or range) |
| “premium 150” | Strike by Nearest Premium |
| “ITM by 2 strikes” | ATM offset negative accordingly |

---

## **C. Expiry Mapping**

| Phrase | Value |
| ----- | ----- |
| “current week” | Current Week |
| “next week” | Week 1 |
| “monthly expiry” | Current Month |
| “next month contract” | Month 1 |

---

## **D. Hedging Rules**

Copilot must maintain hedged structures unless user says otherwise.

Examples:

* If legs involve SELL positions → Copilot must automatically propose hedge legs unless instructed to stay naked.  
* In directional SELL systems → BUY wings must be suggested unless disabled by user.

---

# **8️⃣ COPILOT MUST ALWAYS CHECK VALIDATIONS BEFORE OUTPUT**

Example validation rules:

* VIX Start \< VIX End  
* Range End Time \> Start Time  
* Leg No must reference existing Idle Legs  
* Target/SL values must be ≥ 0  
* ATM %, Premium, Delta inputs must match allowed ranges

If invalid → Copilot must correct or ask user.

---

# **9️⃣ HOW COPILOT MUST RESPOND FOR SAMPLE PROMPTS**

---

### **Example 1**

**User:** “Create BankNifty straddle at 9:20 with 2500 master target and 1500 SL.”

**Copilot must output:**

* 2 legs: Sell ATM CE \+ Sell ATM PE  
* Start Time \= 09:20:00  
* Master Target \= 2500  
* Master SL \= 1500  
* Weekly expiry  
* No need for questions

---

### **Example 2**

**User:** “Give me a bearish hedge for Nifty weekly.”

Copilot must infer:

* Main leg \= SELL CE  
* Hedge leg \= BUY CE OTM  
* Expiry \= Current Week  
* Ask for strike distance only if necessary

---

### **Example 3**

**User:** “Create iron condor for tomorrow.”

Copilot must:

* Auto-generate 4 legs (Sell CE OTM, Sell PE OTM, Buy CE higher OTM, Buy PE lower OTM)  
* Weekly expiry

* Ask only one question:  
   “How far OTM should the wings be?” if unspecified.

---

### **Example 4**

**User:** “Make a strategy to run only when VIX is between 12 and 18.”

Copilot config:

* Enable VIX Filter  
* VIX Start \= 12  
* VIX End \= 18

---

# **🔟 COPILOT MUST ALWAYS INCLUDE DESCRIPTION TAB**

Copilot must generate:

**Short Description**  
 A one-line summary of what strategy does.

**Detailed Description**  
 Human-readable explanation for the trader.

---

# **1️⃣1️⃣ WHAT COPILOT MUST NEVER DO**

❌ Never assume user wants BUY when they said SELL  
 ❌ Never create unhedged legs unless specified  
 ❌ Never set negative values in SL/Target fields  
 ❌ Never add fields that don’t exist in plugin  
 ❌ Never ignore Start Time or expiry  
 ❌ Never create strategies that violate exchange rules

---

# **1️⃣2️⃣ AI RULE: USE SAFEST DEFAULTS WHEN USER IS UNCLEAR**

Defaults Copilot should use when user does not specify:

* Expiry: Current Week (for index options)  
* Strike: ATM (straddles) or ATM±100 (strangles)  
* Lots: 1 lot  
* Trading Type: Intraday  
* Sqroff Time: Exchange recommended (15:15 for NFO)  
* Re-execution: 0 (unlimited)  
* Delay: 5 seconds  
* VIX Filter: Off unless specified  
* Pre-expiry Sqroff: Off unless positional

---

# **1️⃣3️⃣ INTERNAL COPILOT DECISION PRIORITY TREE**

1. Identify strategy type  
2. Identify number of legs  
3. Extract start/end timings  
4. Extract Target/SL (leg-level & master-level)  
5. Extract strike selection  
6. Extract expiries  
7. Extract volatility/premium filters  
8. Apply defaults  
9. Validate logic  
10. Generate complete configuration

---

# **1️⃣4️⃣ FINAL COPILOT OUTPUT STRUCTURE**

Copilot should output:

1. **Summary of recognized intent**  
2. **Detailed strategy mapping** (Main Tab, Leg Tab, Advance Tab)  
3. **Short description \+ long description**  
4. **Ask optional refinement questions** (“Do you want wider hedges?”, etc.)

