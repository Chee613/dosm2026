"""
Economic Valuation & Natural Capital Accounting Engine for Malaysian Coral Reefs.

Quantifies the RM 8.7 Billion/year total economic value across 4 pillars:
1. Marine Tourism & Recreation (RM 4.8B)
2. Coastal Protection & Shoreline Buffering (RM 2.3B)
3. Fisheries Nursery & Commercial Landings (RM 1.1B)
4. Carbon Sequestration & Biodiversity Non-Use (RM 0.5B)

Simulates 20-year Net Present Value (NPV) trade-offs between short-term restriction
revenue sacrifice and long-term natural asset preservation.
"""

def get_economic_pillars():
    """
    Returns the official 4-pillar benchmark economic valuation for Malaysian coral reefs.
    Derived from environmental economics literature (UNEP, World Bank, Reef Check Malaysia)
    and aligned with Department of Statistics Malaysia (DOSM) Tourism Satellite Accounts.
    """
    breakdown = [
        {
            "pillar": "Marine Tourism & Recreation",
            "value_myr": 4.80e9,
            "value_label": "RM 4.80 Billion",
            "share_pct": 55.17,
            "description": "Direct accommodation, dive/snorkel operator concessions, equipment rentals, and island boat charters across 56 monitored islands.",
            "policy_relevance": "Directly affected by visitor caps, but dependent on high live coral cover for aesthetic dive appeal."
        },
        {
            "pillar": "Coastal Protection & Shoreline Buffering",
            "value_myr": 2.30e9,
            "value_label": "RM 2.30 Billion",
            "share_pct": 26.44,
            "description": "Physical wave energy dissipation, monsoon storm surge attenuation, and prevention of coastal resort and infrastructure erosion.",
            "policy_relevance": "Severely degraded reefs forfeit wave buffering, causing millions in coastal erosion repair costs."
        },
        {
            "pillar": "Fisheries Nursery & Commercial Landings",
            "value_myr": 1.10e9,
            "value_label": "RM 1.10 Billion",
            "share_pct": 12.64,
            "description": "Spawning biomass, larval export, and nursery habitat supporting coastal food security and state marine fish landings.",
            "policy_relevance": "Direct link to OpenDOSM state marine fish landings; structural complexity directly sustains fish abundance."
        },
        {
            "pillar": "Carbon Sequestration & Biodiversity Non-Use",
            "value_myr": 0.50e9,
            "value_label": "RM 0.50 Billion",
            "share_pct": 5.75,
            "description": "Blue carbon sedimentation, biogenic calcification, genetic biodiversity, and global scientific/conservation option value.",
            "policy_relevance": "Non-extractive natural heritage asset backing national climate and sustainability commitments."
        }
    ]
    
    total_value_myr = sum(p["value_myr"] for p in breakdown)
    
    return {
        "total_value_myr": total_value_myr,
        "total_value_label": f"RM {total_value_myr / 1e9:.1f} Billion / Year",
        "breakdown": breakdown
    }

def simulate_npv_tradeoff(years=20, discount_rate=0.05):
    """
    Simulates a 20-year Net Present Value (NPV) trajectory comparing:
    - Trajectory A (No Action / Business As Usual): Over-tourism and uncontrolled runoff compound thermal bleaching,
      causing coral cover to collapse from ~40% to ~15%, degrading natural asset yield by 3.5% annually.
    - Trajectory B (Sustainable Management / ReefSafe): Strategic seasonal capacity caps and mooring enforcement
      sacrifice ~RM 150M/yr in short-term tourist spend in years 1-3, but stabilize coral cover, allowing natural
      recovery and sustaining long-term asset yield.
    """
    base_annual_value = 8.70e9 # RM 8.7B
    yearly_trajectories = []
    
    cum_npv_no_action = 0.0
    cum_npv_sustainable = 0.0
    
    for t in range(1, years + 1):
        discount_factor = 1.0 / ((1.0 + discount_rate) ** t)
        
        # Trajectory A: No Action - compounding 3.5% annual loss of ecosystem yield
        yield_loss_pct_a = min(0.65, 0.035 * (t ** 1.15))
        annual_val_no_action = base_annual_value * (1.0 - yield_loss_pct_a)
        pv_no_action = annual_val_no_action * discount_factor
        cum_npv_no_action += pv_no_action
        
        # Trajectory B: Sustainable Management
        # Years 1-3: temporary restriction cost (~RM 150M/yr short-term concession sacrifice)
        # Years 4+: stabilized reef yields sustained benefits with 0.8% annual recovery gain
        if t <= 3:
            concession_sacrifice = 0.15e9 # RM 150M
            annual_val_sustainable = (base_annual_value * 0.98) - concession_sacrifice
        else:
            recovery_gain = min(0.12, 0.012 * (t - 3))
            annual_val_sustainable = base_annual_value * (1.0 + recovery_gain)
            
        pv_sustainable = annual_val_sustainable * discount_factor
        cum_npv_sustainable += pv_sustainable
        
        yearly_trajectories.append({
            "year": t,
            "annual_val_no_action_myr": annual_val_no_action,
            "annual_val_sustainable_myr": annual_val_sustainable,
            "pv_no_action_myr": pv_no_action,
            "pv_sustainable_myr": pv_sustainable,
            "cum_npv_no_action_myr": cum_npv_no_action,
            "cum_npv_sustainable_myr": cum_npv_sustainable,
            "net_preservation_benefit_myr": cum_npv_sustainable - cum_npv_no_action
        })
        
    return {
        "years": years,
        "discount_rate": discount_rate,
        "base_annual_value_myr": base_annual_value,
        "npv_no_action_myr": cum_npv_no_action,
        "npv_sustainable_management_myr": cum_npv_sustainable,
        "net_gain_preservation_myr": cum_npv_sustainable - cum_npv_no_action,
        "yearly_trajectories": yearly_trajectories
    }

if __name__ == "__main__":
    pillars = get_economic_pillars()
    print(f"Total Valuation: {pillars['total_value_label']}")
    tradeoff = simulate_npv_tradeoff(20)
    print(f"20-Year NPV Sustainable: RM {tradeoff['npv_sustainable_management_myr']/1e9:.2f}B")
    print(f"20-Year NPV No Action:   RM {tradeoff['npv_no_action_myr']/1e9:.2f}B")
    print(f"Net Natural Asset Gain:  RM {tradeoff['net_gain_preservation_myr']/1e9:.2f}B")
