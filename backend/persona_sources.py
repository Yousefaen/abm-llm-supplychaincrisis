"""Mapping from sim agent_id to public-filing source spec.

Currently wires up only SEC EDGAR filers. Of the 9 sim agents, four are listed
on US exchanges and file with the SEC: TSMC (TSM, 20-F), NXP (NXPI, 10-K),
Toyota (TM, 20-F), Ford (F, 10-K). The other five (Samsung, Infineon,
Continental, Bosch, VW) file in Korea/Germany only and are deferred to a
follow-up that fetches from each company's IR website.
"""

EDGAR_SOURCES: dict[str, dict] = {
    "TaiwanSemi":   {"cik": 1046179, "form": "20-F", "ticker": "TSM"},
    "AmeriSemi":    {"cik": 1413447, "form": "10-K", "ticker": "NXPI"},
    "ToyotaMotors": {"cik": 1094517, "form": "20-F", "ticker": "TM"},
    "FordAuto":    {"cik": 37996,    "form": "10-K", "ticker": "F"},
}

# Sim-context metadata used when prompting the persona builder.  Keeps the
# narrative role (e.g. "CPO" vs "CEO") and supply-chain neighbours in one
# place so build_personas.py stays declarative.
ROLE_CONTEXT: dict[str, dict] = {
    "TaiwanSemi": {
        "role": "CEO",
        "company": "TSMC (Taiwan Semiconductor Manufacturing Company)",
        "upstream_desc": "none (top of the chip supply chain)",
        "downstream_desc": "chip designers like Infineon and NXP",
    },
    "AmeriSemi": {
        "role": "CEO",
        "company": "NXP Semiconductors",
        "upstream_desc": "foundries like TSMC and Samsung",
        "downstream_desc": "Tier-1 automotive suppliers like Bosch and Continental",
    },
    "ToyotaMotors": {
        "role": "Chief Procurement Officer",
        "company": "Toyota Motor Corporation",
        "upstream_desc": "Tier-1 automotive suppliers like Bosch and Continental",
        "downstream_desc": "none (end of the chain — sells finished vehicles)",
    },
    "FordAuto": {
        "role": "Chief Procurement Officer",
        "company": "Ford Motor Company",
        "upstream_desc": "Tier-1 automotive suppliers like Bosch and Continental",
        "downstream_desc": "none (end of the chain — sells finished vehicles)",
    },
}
