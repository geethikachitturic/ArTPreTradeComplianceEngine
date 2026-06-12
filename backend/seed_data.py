"""
Seed script — run once after database creation.
Populates: users, built-in Reg T and FINRA 4210 rules.

Usage: python seed_data.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import User, Rule
from app.models.user import UserRole, SeniorityLevel
from app.models.rule import AssetClassScope, BlockType, RuleType

Base.metadata.create_all(bind=engine)


def seed_users(db):
    if db.query(User).count() > 0:
        print("Users already seeded, skipping.")
        return

    users = [
        # Traders
        User(username="jsmith", full_name="James Smith", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.ANALYST, desk="Equity Derivatives"),
        User(username="aclarke", full_name="Anna Clarke", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.ASSOCIATE, desk="Fixed Income"),
        User(username="bwilliams", full_name="Ben Williams", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.VP, desk="Equity Cash"),
        User(username="skumar", full_name="Sunita Kumar", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.VP, desk="Fixed Income"),
        User(username="cpatel", full_name="Chirag Patel", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.ASSOCIATE, desk="Equity Cash"),
        User(username="lchen", full_name="Li Chen", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.ANALYST, desk="Fixed Income"),
        User(username="rjones", full_name="Rachel Jones", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.DIRECTOR, desk="Credit"),
        User(username="tmurphy", full_name="Tom Murphy", role=UserRole.TRADER,
             seniority_level=SeniorityLevel.ASSOCIATE, desk="Equity Derivatives"),

        # Supervisors
        User(username="dgraham", full_name="David Graham", role=UserRole.SUPERVISOR,
             seniority_level=SeniorityLevel.VP, desk="Equity Cash"),
        User(username="sthompson", full_name="Sarah Thompson", role=UserRole.SUPERVISOR,
             seniority_level=SeniorityLevel.DIRECTOR, desk="Fixed Income"),

        # Head of Desk / MD
        User(username="mfoster", full_name="Michael Foster", role=UserRole.HEAD_OF_DESK,
             seniority_level=SeniorityLevel.MANAGING_DIRECTOR, desk="Equity"),
        User(username="klee", full_name="Katherine Lee", role=UserRole.MANAGING_DIRECTOR,
             seniority_level=SeniorityLevel.MANAGING_DIRECTOR, desk="Fixed Income"),

        # Controls team
        User(username="controls_admin", full_name="Controls Team", role=UserRole.CONTROLS_TEAM,
             seniority_level=SeniorityLevel.VP, desk="Market Risk Controls"),
    ]

    db.add_all(users)
    db.commit()
    print(f"Seeded {len(users)} users.")


def seed_rules(db):
    if db.query(Rule).count() > 0:
        print("Rules already seeded, skipping.")
        return

    rules = [
        # ----------------------------------------------------------------
        # Regulation T — built-in rules (documented, not evaluated in engine
        # since reg_t_checks.py handles them programmatically — these exist
        # for the Rules Manager UI to display)
        # ----------------------------------------------------------------
        Rule(
            rule_code="REGT-LM-001",
            name="Reg T Initial Margin — Long Equity Purchase",
            description="Customer must provide at least 50% of the purchase price for marginable equity securities.",
            natural_language_description="Block any margin purchase of equity securities where the customer's available equity is below 50% of the trade notional.",
            rule_type=RuleType.REG_T,
            asset_class_scope=AssetClassScope.EQUITY,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=10,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="REGT-SS-001",
            name="Reg T Short Sale — 150% Collateral",
            description="Short sales require 150% of the short sale value as collateral (100% proceeds + 50% margin).",
            natural_language_description="Block short sales where account equity is below 150% of the short sale notional value.",
            rule_type=RuleType.REG_T,
            asset_class_scope=AssetClassScope.EQUITY,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=10,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="REGT-CA-001",
            name="Cash Account — Full Payment Required",
            description="Cash accounts must be paid in full. No margin extension is permitted.",
            natural_language_description="Block any purchase in a cash account where available cash is less than the full trade notional.",
            rule_type=RuleType.REG_T,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=5,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="REGT-FI-IG-001",
            name="Reg T Initial Margin — IG Corporate Bond",
            description="Investment grade corporate bonds require 30% initial margin.",
            natural_language_description="Soft block margin purchases of investment grade corporate bonds where account equity is below 30% of trade notional.",
            rule_type=RuleType.REG_T,
            asset_class_scope=AssetClassScope.FIXED_INCOME,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=10,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="REGT-FI-HY-001",
            name="Reg T Initial Margin — HY Corporate Bond",
            description="Non-investment grade (high yield) corporate bonds require 50% initial margin.",
            natural_language_description="Block margin purchases of high yield corporate bonds where account equity is below 50% of trade notional.",
            rule_type=RuleType.REG_T,
            asset_class_scope=AssetClassScope.FIXED_INCOME,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=10,
            created_by="SYSTEM",
        ),

        # ----------------------------------------------------------------
        # FINRA Rule 4210 — built-in rules
        # ----------------------------------------------------------------
        Rule(
            rule_code="F4210-IML-001",
            name="Intraday Margin Deficit — Safe Harbour Warning",
            description="IML-reducing transaction creates a small intraday deficit within the Reg 4210(d)(2) safe harbour.",
            natural_language_description="Warn trader when an IML-reducing transaction creates an intraday margin deficit below the lesser of $1,000 or 5% of account equity.",
            rule_type=RuleType.FINRA_4210,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.SOFT_BLOCK,
            conditions=None,
            priority=20,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="F4210-IML-002",
            name="Intraday Margin Deficit — Moderate",
            description="IML-reducing transaction creates a moderate intraday deficit under FINRA Rule 4210(d)(2).",
            natural_language_description="Soft block when intraday margin deficit is moderate. Alert trader of 5-day satisfaction deadline and 90-day freeze risk.",
            rule_type=RuleType.FINRA_4210,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.SOFT_BLOCK,
            conditions=None,
            priority=20,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="F4210-IML-003",
            name="Intraday Margin Deficit — Large (Override Required)",
            description="Large intraday deficit (>$25k) requiring supervisory approval per FINRA Rule 4210(d)(2).",
            natural_language_description="Hard block with supervisory override required when intraday margin deficit exceeds $25,000.",
            rule_type=RuleType.FINRA_4210,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.HARD_BLOCK_WITH_OVERRIDE,
            conditions=None,
            priority=15,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="F4210-IML-004",
            name="Intraday Margin Deficit — Critical (Hard Block)",
            description="Critical intraday deficit (>$100k) — outright hard block, no override.",
            natural_language_description="Hard block when intraday margin deficit exceeds $100,000. No override permitted.",
            rule_type=RuleType.FINRA_4210,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=5,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="F4210-FRZ-001",
            name="90-Day Freeze — Short Position Prohibited",
            description="Account under 90-day freeze cannot create or increase short positions.",
            natural_language_description="Hard block any short sale or short option position where account has active 90-day freeze under FINRA Rule 4210(d)(2)(D).",
            rule_type=RuleType.FINRA_4210,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.HARD_BLOCK,
            conditions=None,
            priority=5,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="F4210-PM-001",
            name="Portfolio Margin — Sub-$5M Equity Intraday Check",
            description="Portfolio margin accounts with equity < $5M must maintain intraday margin equivalent to end-of-day per Rule 4210(g)(1)(K).",
            natural_language_description="Soft block portfolio margin accounts with equity below $5 million on IML-reducing transactions, requiring intraday margin verification.",
            rule_type=RuleType.FINRA_4210,
            asset_class_scope=AssetClassScope.ALL,
            block_type=BlockType.SOFT_BLOCK,
            conditions=None,
            priority=25,
            created_by="SYSTEM",
        ),

        # ----------------------------------------------------------------
        # Custom firm-level rules (examples)
        # ----------------------------------------------------------------
        Rule(
            rule_code="CUST-001",
            name="Large Notional Equity Trade — Analyst Override Required",
            description="Equity trades with notional over $5M from Analyst-level traders require supervisory sign-off.",
            natural_language_description="Require supervisory override for any equity trade where notional exceeds $5,000,000 and the trader is at Analyst level.",
            rule_type=RuleType.CUSTOM,
            asset_class_scope=AssetClassScope.EQUITY,
            block_type=BlockType.HARD_BLOCK_WITH_OVERRIDE,
            conditions={
                "type": "AND",
                "rules": [
                    {"field": "notional", "operator": ">", "value": 5_000_000, "label": "Notional > $5,000,000"},
                    {"field": "trader_seniority", "operator": "<", "value": "ASSOCIATE", "label": "Trader seniority below Associate"},
                ],
            },
            priority=30,
            created_by="SYSTEM",
        ),
        Rule(
            rule_code="CUST-002",
            name="High Yield Bond — Notional Cap",
            description="High yield bond purchases exceeding $10M require Head of Desk approval.",
            natural_language_description="Override required for high yield corporate bond purchases exceeding $10,000,000 notional.",
            rule_type=RuleType.CUSTOM,
            asset_class_scope=AssetClassScope.FIXED_INCOME,
            block_type=BlockType.HARD_BLOCK_WITH_OVERRIDE,
            conditions={
                "type": "AND",
                "rules": [
                    {"field": "notional", "operator": ">", "value": 10_000_000, "label": "Notional > $10,000,000"},
                ],
            },
            priority=30,
            created_by="SYSTEM",
        ),
    ]

    db.add_all(rules)
    db.commit()
    print(f"Seeded {len(rules)} rules.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("Running ArT seed data...")
        seed_users(db)
        seed_rules(db)
        print("Seed complete.")
    finally:
        db.close()
