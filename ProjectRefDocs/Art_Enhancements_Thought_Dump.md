Test Queries
1. "F4210-FRZ-001 - Account under 90-day freeze cannot create or increase short positions." Where in the App can i review accounts that are under the 90-day freeze? 
2. Trader Manual Entry screen does not show the counterparty / account details. Do you have a list of these so that I can enter trades that I can use to submit trades that will breach?
3. Where do I see the details of each of the 12 Trades presently shown in the MI dashboard? 

 Trader   │ Username  │      Role/Desk       │          Breach Scenario to Test          │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ James      │ jsmith    │ Analyst, Equity      │ Use with notional > $5M → triggers        │
│ Smith      │           │ Derivatives          │ CUST-001 (Analyst large trade)            │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Anna       │ aclarke   │ Associate, Fixed     │ HY bond > $10M → triggers CUST-002        │
│ Clarke     │           │ Income               │                                           │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Ben        │ bwilliams │ VP, Equity Cash      │ Short sell with freeze active →           │
│ Williams   │           │                      │ F4210-FRZ-001                             │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Sunita     │ skumar    │ VP, Fixed Income     │ Short sell with low equity →              │
│ Kumar      │           │                      │ F4210-IML-003/004                         │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Chirag     │ cpatel    │ Associate, Equity    │ Margin buy with equity < 50% of notional  │
│ Patel      │           │ Cash                 │ → REGT-LM-001                             │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Li Chen    │ lchen     │ Analyst, Fixed       │ HY bond margin buy, equity < 50% →        │
│            │           │ Income               │ REGT-FI-HY-001                            │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Rachel     │ rjones    │ Director, Credit     │ Short sell creating >$100k deficit →      │
│ Jones      │           │                      │ F4210-IML-004                             │
├────────────┼───────────┼──────────────────────┼───────────────────────────────────────────┤
│ Tom Murphy │ tmurphy   │ Associate, Equity    │ Short sell with freeze active →           │
│            │           │ Derivatives          │ F4210-FRZ-001




To-dos thought dump

1. Enhancements to App: 
    In MI Dashboard or in any other reports view / results of search view, add Column management feature to include key columns such as Rule Ref, Rule Name, Trade Ref, Trader Ref, Scope, Type. 
    
    Hyperlink on counts, TradeRef, Rule Reference etc. If User clicks on a count, show a drill down view in a separate window (or any other UI/UX best practise view of displaying results) of the underlying trades along with key details such as block / rule etc. If User clicks on Trade Ref, show in the bottom pane (or any other best suited location) the Trade details (e.g. the ones that are shown in the manuak entry screen). If User clicks on Rule Ref, show the details of the rule etc.

    When there are multiple blocks on one trade, continue to show all blocks details as presently shown. But in the reports just list 1 block as per the below hierarchy table. Add this table in a separate View called "Configurations". Include this as a menu item on the left side of the App, under "Audit Log", which is presently the last menu item.
    
    Block Hierarchy Table:
    When a trade has Soft Block (SB), Hard Block (HB), Hard Block Override (HBO), show HB
    When a trade has Soft Block (SB), Hard Block Override (HBO), show HBO
    When a trade has all Soft Blocks (SB) or all Hard Blocks (HB) or all Hard Block Overrides (HBO), show whichever is the first rule checked by the app control logic.

    Entitlements:
    Add Entitlements feature to the Art Tool: a) Create Login screen - User Id and Password and Forgot Password options b) Update ArT_Implementation_Plan.docx document with a section called "User Entitlements" and include a table of Userid and Password for each of the Users of the ArT tool. The Password should be Userid+123. 

    Scope Increase:
    Within /Users/athithi/Documents/AI_Study, Rename folder "finra4210" to "PreTradeControls" AND Rename "FinraRegDocs" to "RegDocs" and update all references to the these folders in ArT Product code, with the newly updated names.This change is because the scope of these folders has increased to include other regs in addition to finra4210. Please re-check all references are updated so that there are no issues when running the ArT Product. Please let me know how complex is this task and whether there are any risks associated with such folder renaming. 

2. Updates to Documentation: 
    Hyperlink the Table of COntents
    Include Page numbers in the document and show the page numbers in the Table of Contents
    Include Data Model / Data Flow Diagram / Reference Data Sources sections


3. Do the following in sequential steps, one thing after another:
    a. Create Test Plan and execute it 
    b. Review the Test Plan, Test Data and provide feedback
    c. Incorprate feedback

4. Queries

    Give me the test data for the following features:
     "Support supervisory oversight through an AI-assisted override workflow with risk scoring."
     "Allow compliance teams to author new control rules in plain English without coding."

5. How do I create a custom rule and toggle on / off
 Custom Rules       │ CUST-001 (analyst notional cap), CUST-002 (HY bond cap), toggle rule on/off and verify engine excludes inactive rules



Idea - Implement a new regulation ODI rule using Custom Rules? Detour - Reading up on ODI.

 Use Claude to build an app to do Job Hunting

 Use Claude to build a gaming app for buddi - given he has the plan

 Do testing for Diva

 Write linked in post on how chatgpt and claude are GodSent magical wands to BAPMs, but also great efficiency deliverers to all stakeholders in the SDLC who work with BAPMs.


Create a new Regulation "Type" = ODI_India, Name = ODI_India Underlying Non Cash, Scope = ALL, Priority = 30, Status = Active. This rule will check whether the trade is trading a product whose country of incorporation is India , whose underlying security's country of is non cash i.e. a derivative trade.




