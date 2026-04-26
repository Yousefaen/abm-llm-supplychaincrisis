"""Mapping from sim agent_id to public-filing source spec.

Two source types are wired up:

* ``EDGAR_SOURCES`` — SEC filers (US exchange listings).  Used for TSMC
  (20-F), NXP (10-K), Toyota (20-F), Ford (10-K).
* ``IR_SOURCES`` — non-SEC filers (Korea/Germany).  Direct PDF URLs to
  each company's annual report, fetched and text-extracted via pypdf.
  Used for Samsung, Infineon, Continental, Bosch, VW.

Together these cover all 9 sim agents.  ``ROLE_CONTEXT`` carries the
narrative-role prompt slot (e.g. "CPO" vs "CEO") and supply-chain
neighbours used by build_personas.py.
"""

EDGAR_SOURCES: dict[str, dict] = {
    "TaiwanSemi":   {"cik": 1046179, "form": "20-F", "ticker": "TSM"},
    "AmeriSemi":    {"cik": 1413447, "form": "10-K", "ticker": "NXPI"},
    "ToyotaMotors": {"cik": 1094517, "form": "20-F", "ticker": "TM"},
    "FordAuto":    {"cik": 37996,    "form": "10-K", "ticker": "F"},
}

# Direct annual-report PDF URLs for non-SEC filers.  Each url should be
# the FY2019 report so personas reflect pre-COVID baseline posture
# (matches the EDGAR FY2019 pattern).  Verified working 2026-04-26.
# If a URL breaks, replace it with the equivalent in the company's IR
# archive — most companies keep multi-year archives indefinitely.
IR_SOURCES: dict[str, dict] = {
    "KoreaSilicon": {
        "fy2019_url": "https://images.samsung.com/is/content/samsung/p5/global/ir/docs/2019_Business_Report.pdf",
        "company_name": "Samsung Electronics",
    },
    "EuroChip": {
        # Infineon's own dgdl URL serves a 404 to urllib (likely UA/referer
        # gating).  AnnualReports.com hosts an unmodified mirror and accepts
        # plain User-Agent strings.
        "fy2019_url": "https://www.annualreports.com/HostedData/AnnualReportArchive/i/infineon-technologies_2019.pdf",
        "company_name": "Infineon Technologies",
    },
    "ContiParts": {
        "fy2019_url": "https://www.continental.com/fileadmin/__imported/sites/corporate/_international/english/hubpages/30_20investors/30_20reports/annual_20reports/downloads/annual_20report_202019.pdf",
        "company_name": "Continental AG",
    },
    "BoschAuto": {
        "fy2019_url": "https://assets.bosch.com/media/en/global/bosch_group/our_figures/publication_archive/pdf_1/GB2019.pdf",
        "company_name": "Robert Bosch GmbH",
    },
    "VolkswagenAG": {
        # VW's annualreport2019.volkswagenag.com microsite returns 404 for
        # the advertised entire-AR PDF as of 2026.  AnnualReports.com hosts
        # the same document as a stable mirror.
        "fy2019_url": "https://www.annualreports.com/HostedData/AnnualReportArchive/v/OTC_VWAGY_2019.pdf",
        "company_name": "Volkswagen AG",
    },
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
    "KoreaSilicon": {
        "role": "Head of the Foundry Business Division",
        "company": "Samsung Electronics' Foundry Business",
        "upstream_desc": "none (top of the chip supply chain)",
        "downstream_desc": "chip designers like Infineon and NXP",
    },
    "EuroChip": {
        "role": "CEO",
        "company": "Infineon Technologies",
        "upstream_desc": "foundries like TSMC and Samsung",
        "downstream_desc": "Tier-1 automotive suppliers like Bosch and Continental",
    },
    "AmeriSemi": {
        "role": "CEO",
        "company": "NXP Semiconductors",
        "upstream_desc": "foundries like TSMC and Samsung",
        "downstream_desc": "Tier-1 automotive suppliers like Bosch and Continental",
    },
    "BoschAuto": {
        "role": "Head of Automotive Electronics / Mobility Solutions",
        "company": "Robert Bosch GmbH (automotive division)",
        "upstream_desc": "chip designers like Infineon and NXP",
        "downstream_desc": "OEMs like Toyota, Ford, and Volkswagen",
    },
    "ContiParts": {
        "role": "Head of Automotive Group / Powertrain",
        "company": "Continental AG",
        "upstream_desc": "chip designers like Infineon and NXP",
        "downstream_desc": "OEMs like Toyota, Ford, and Volkswagen",
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
    "VolkswagenAG": {
        "role": "Chief Procurement Officer",
        "company": "Volkswagen Group",
        "upstream_desc": "Tier-1 automotive suppliers like Bosch and Continental",
        "downstream_desc": "none (end of the chain — sells finished vehicles)",
    },
}
