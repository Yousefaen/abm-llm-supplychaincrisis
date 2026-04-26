"""Run EDGAR fetch + persona generation end-to-end for all wired agents.

Outputs:
  backend/personas_cache/docs/<agent_id>/<form>.txt    -- cached filing
  backend/personas_cache/personas/<agent_id>.txt        -- generated persona

After generation, prints a hand-crafted vs auto-generated comparison so the
two can be eyeballed side-by-side.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import anthropic

from agents import PERSONAS, SONNET_INPUT_COST_PER_M, SONNET_OUTPUT_COST_PER_M
from fetch_filings import fetch_filing
from persona_builder import build_persona
from persona_sources import EDGAR_SOURCES, ROLE_CONTEXT

OUT_DIR = Path(__file__).parent / "personas_cache" / "personas"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = list(sys.argv[1:])
    fiscal_year: int | None = None
    if "--fy" in args:
        i = args.index("--fy")
        fiscal_year = int(args.pop(i + 1))
        args.pop(i)
    targets = args or list(EDGAR_SOURCES)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()
    total_in = 0
    total_out = 0
    t0 = time.time()

    fy_label = f"FY{fiscal_year}" if fiscal_year else "latest"
    print(f"Generating {fy_label} personas for {len(targets)} agent(s): {', '.join(targets)}\n")

    for agent_id in targets:
        if agent_id not in EDGAR_SOURCES:
            print(f"  [{agent_id}] no EDGAR source wired; skipping")
            continue

        src = EDGAR_SOURCES[agent_id]
        ctx = ROLE_CONTEXT[agent_id]

        # 1. Fetch the filing (cached after first run)
        doc_path = fetch_filing(agent_id, src["cik"], src["form"], fiscal_year)

        # 2. Generate persona — cache partitioned by fiscal year so 2019 and
        #    latest can coexist for side-by-side review.
        suffix = f"_fy{fiscal_year}" if fiscal_year else ""
        out_file = OUT_DIR / f"{agent_id}{suffix}.txt"
        if out_file.exists():
            print(f"  [{agent_id}] persona cached -> {out_file.name}; delete to regenerate\n")
            continue

        print(f"  [{agent_id}] generating persona via Sonnet...")
        persona, usage = build_persona(
            agent_id=agent_id,
            role=ctx["role"],
            company=ctx["company"],
            upstream_desc=ctx["upstream_desc"],
            downstream_desc=ctx["downstream_desc"],
            doc_path=doc_path,
            client=client,
        )
        out_file.write_text(persona, encoding="utf-8")
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        print(
            f"  [{agent_id}] saved {len(persona)} chars  "
            f"(in={usage['input_tokens']} out={usage['output_tokens']} tokens)\n"
        )

    cost = (
        total_in * SONNET_INPUT_COST_PER_M / 1_000_000
        + total_out * SONNET_OUTPUT_COST_PER_M / 1_000_000
    )
    elapsed = time.time() - t0
    print(
        f"=== generation complete: {elapsed:.1f}s, "
        f"{total_in} in / {total_out} out tokens, ${cost:.4f} ===\n"
    )

    # Side-by-side comparison: hand-crafted, latest auto, FY-specific auto
    suffix = f"_fy{fiscal_year}" if fiscal_year else ""
    print("\n" + "=" * 78)
    if fiscal_year:
        print(f"HAND-CRAFTED  vs  LATEST-AUTO  vs  FY{fiscal_year}-AUTO  (eyeball comparison)")
    else:
        print("HAND-CRAFTED  vs  LATEST-AUTO  (eyeball comparison)")
    print("=" * 78)
    for agent_id in targets:
        if agent_id not in EDGAR_SOURCES:
            continue
        latest_file = OUT_DIR / f"{agent_id}.txt"
        fy_file = OUT_DIR / f"{agent_id}{suffix}.txt"
        print(f"\n----- {agent_id} -----")
        print(f"\n>>> HAND-CRAFTED ({len(PERSONAS[agent_id])} chars):\n")
        print(PERSONAS[agent_id])
        if latest_file.exists() and latest_file != fy_file:
            print(f"\n>>> LATEST-AUTO ({latest_file.stat().st_size} chars):\n")
            print(latest_file.read_text(encoding="utf-8"))
        if fy_file.exists():
            label = f"FY{fiscal_year}-AUTO" if fiscal_year else "AUTO"
            print(f"\n>>> {label} ({fy_file.stat().st_size} chars):\n")
            print(fy_file.read_text(encoding="utf-8"))
        print()


if __name__ == "__main__":
    main()
