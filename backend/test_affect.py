"""Unit tests for the emotion-driven affect system.

These tests are pure (no LLM calls) and exercise the numeric / structural
contracts we rely on: grudge buildup, contagion, behavior coupling,
serialization bounds, and mood-congruent memory retrieval.

Run directly:
    python backend/test_affect.py
or with pytest:
    pytest backend/test_affect.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script from repo root or from backend/
_BACKEND = Path(__file__).resolve().parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from affect import AffectState  # noqa: E402
from memory import (  # noqa: E402
    AgentSignal,
    MemoryRecord,
    MemoryStream,
    generate_affect_memory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_affect_bounds() -> None:
    """All fields stay in their documented ranges after repeated extremes."""
    a = AffectState.for_persona("VolkswagenAG")
    for _ in range(50):
        a.update_from_outcome(
            fill_rate=0.1,
            profit=-5000,
            partner_fills={"BoschAuto": 0.0, "ContiParts": 0.1},
            partner_seeking_alternatives={"BoschAuto": True},
        )
        a.update_from_event_valence(fear=0.5, stress=0.5, morale=-0.5)
        a.accumulate_fatigue()
        a.decay()
    for name in ["fear", "anger", "trust_joy", "pride", "shame", "greed",
                "stress", "fatigue", "morale"]:
        v = getattr(a, name)
        _assert(0.0 <= v <= 1.0, f"{name} out of [0,1]: {v}")
    _assert(-1.0 <= a.valence <= 1.0, f"valence out of [-1,1]: {a.valence}")
    _assert(0.0 <= a.arousal <= 1.0, f"arousal out of [0,1]: {a.arousal}")
    for pid, g in a.grudge.items():
        _assert(0.0 <= g <= 1.0, f"grudge[{pid}] out of [0,1]: {g}")


def test_grudge_buildup_from_starvation() -> None:
    """A supplier that starves us two rounds in a row should accrue a grudge."""
    a = AffectState.for_persona("ToyotaMotors")
    # Round 1: KoreaSilicon delivers only 20% of what we wanted
    a.update_from_outcome(
        fill_rate=0.3,
        partner_fills={"BoschAuto": 0.25, "ContiParts": 0.95},
    )
    a.decay()
    # Round 2: same story
    a.update_from_outcome(
        fill_rate=0.35,
        partner_fills={"BoschAuto": 0.30, "ContiParts": 0.90},
    )
    a.decay()

    _assert(
        a.grudge.get("BoschAuto", 0.0) > 0.25,
        f"expected grudge[BoschAuto] > 0.25, got {a.grudge.get('BoschAuto', 0.0):.2f}",
    )
    _assert(
        a.grudge.get("ContiParts", 0.0) < 0.1,
        f"expected grudge[ContiParts] small, got {a.grudge.get('ContiParts', 0.0):.2f}",
    )
    # Fear should have risen
    _assert(a.fear > 0.15, f"expected fear > 0.15, got {a.fear:.2f}")


def test_grudge_penalty_shapes_orders() -> None:
    """Grudge above threshold should shave the per-supplier price penalty."""
    a = AffectState()
    a.grudge["KoreaSilicon"] = 0.8
    a.grudge["TaiwanSemi"] = 0.2  # below threshold
    _assert(
        a.grudge_price_penalty("KoreaSilicon") > 0.2,
        f"expected penalty > 0.2, got {a.grudge_price_penalty('KoreaSilicon'):.2f}",
    )
    _assert(
        a.grudge_price_penalty("TaiwanSemi") == 0.0,
        f"expected 0.0 for low grudge, got {a.grudge_price_penalty('TaiwanSemi'):.2f}",
    )


def test_panic_and_hoard_multipliers_monotonic() -> None:
    """More fear => larger order/hoard amplifiers; must be bounded."""
    low = AffectState()
    low.fear = 0.0
    high = AffectState()
    high.fear = 0.9

    _assert(low.panic_order_multiplier() < high.panic_order_multiplier(),
            "panic multiplier should increase with fear")
    _assert(high.panic_order_multiplier() <= 1.75,
            f"panic multiplier should be bounded, got {high.panic_order_multiplier():.2f}")

    high.greed = 0.9
    _assert(low.hoard_multiplier() < high.hoard_multiplier(),
            "hoard multiplier should increase with fear+greed")
    _assert(high.hoard_multiplier() <= 2.5,
            f"hoard multiplier should be bounded, got {high.hoard_multiplier():.2f}")


def test_allocation_emotional_factor() -> None:
    """Angry supplier with grudge penalizes offender; trust_joy helps everyone."""
    a = AffectState()
    a.anger = 0.7
    a.grudge["FordAuto"] = 0.9
    a.trust_joy = 0.0
    penalty = a.allocation_emotional_factor("FordAuto")
    _assert(penalty < 0.5,
            f"expected allocation factor < 0.5 for grudged buyer, got {penalty:.2f}")

    a2 = AffectState()
    a2.trust_joy = 0.8
    boost = a2.allocation_emotional_factor("ToyotaMotors")
    _assert(boost > 1.0,
            f"expected trust_joy to boost above 1.0, got {boost:.2f}")


def test_contagion_panic_from_trusted_sender() -> None:
    """A high-trust panicking sender should raise the receiver's fear."""
    receiver = AffectState()
    before_fear = receiver.fear
    receiver.update_from_signal(
        sender_valence=-0.8, sender_arousal=0.9, alpha=0.20,
    )
    _assert(receiver.fear > before_fear + 0.01,
            f"expected fear to rise from {before_fear:.2f}, got {receiver.fear:.2f}")
    _assert(receiver.valence < 0.0,
            f"expected valence to go negative, got {receiver.valence:.2f}")


def test_contagion_low_trust_barely_moves() -> None:
    """Low alpha (low trust) => minimal contagion."""
    receiver = AffectState()
    before_val = receiver.valence
    receiver.update_from_signal(
        sender_valence=-0.9, sender_arousal=0.9, alpha=0.02,
    )
    # Should move slightly but not dramatically
    _assert(abs(receiver.valence - before_val) < 0.05,
            f"expected small valence shift, got {receiver.valence - before_val:.3f}")


def test_dominant_emotion_matches_signal_shape() -> None:
    """to_prompt_brief reflects the dominant emotion."""
    a = AffectState()
    a.fear = 0.7
    dom = a.dominant_emotion()
    _assert(dom in ("panicked", "anxious"),
            f"expected fear to dominate, got {dom}")
    brief = a.to_prompt_brief()
    _assert("Fear" in brief, f"expected Fear in brief, got:\n{brief}")


def test_decay_fades_transient_emotions() -> None:
    """Transient emotions decay across many quiet rounds; grudges linger."""
    a = AffectState()
    a.fear = 0.8
    a.anger = 0.7
    a.grudge["X"] = 0.7
    for _ in range(8):
        a.decay()
    _assert(a.fear < 0.25, f"fear should have faded, got {a.fear:.2f}")
    _assert(a.anger < 0.25, f"anger should have faded, got {a.anger:.2f}")
    _assert(a.grudge.get("X", 0.0) > 0.25,
            f"grudge should linger more than transient anger, "
            f"got {a.grudge.get('X', 0.0):.2f}")


def test_mood_congruent_memory_retrieval() -> None:
    """Fearful agents should surface more negative-tagged memories."""
    stream = MemoryStream("test")
    # Mix of tagged memories all in the same round
    stream.add(MemoryRecord(round=1, category="transaction",
                            description="positive 1", importance=5,
                            tags=["transaction", "reliable_delivery"]))
    stream.add(MemoryRecord(round=1, category="transaction",
                            description="positive 2", importance=5,
                            tags=["transaction", "reliable_delivery"]))
    stream.add(MemoryRecord(round=1, category="consequence",
                            description="negative 1", importance=5,
                            tags=["consequence", "severe_shortage"]))
    stream.add(MemoryRecord(round=1, category="consequence",
                            description="negative 2", importance=5,
                            tags=["consequence", "severe_shortage", "trust_break"]))

    calm = AffectState()
    calm.fear = 0.0
    calm.trust_joy = 0.7
    fearful = AffectState()
    fearful.fear = 0.9
    fearful.trust_joy = 0.0

    calm_hits = stream.retrieve(current_round=2, k=2, mood=calm)
    fearful_hits = stream.retrieve(current_round=2, k=2, mood=fearful)

    neg_in_fearful = sum(
        1 for m in fearful_hits if "severe_shortage" in m.tags
    )
    neg_in_calm = sum(
        1 for m in calm_hits if "severe_shortage" in m.tags
    )
    _assert(neg_in_fearful >= neg_in_calm,
            f"fearful should surface >= negative memories; "
            f"calm={neg_in_calm}, fearful={neg_in_fearful}")


def test_signal_carries_affect() -> None:
    """AgentSignal should serialize affective payload."""
    sig = AgentSignal(
        sender="X", recipient="Y", signal_type="warning",
        content="panic", round=3,
        affect_valence=-0.6, affect_arousal=0.8,
    )
    d = sig.to_dict()
    _assert(d["affect_valence"] == -0.6, f"lost affect_valence: {d}")
    _assert(d["affect_arousal"] == 0.8, f"lost affect_arousal: {d}")


def test_affect_memory_factory() -> None:
    """generate_affect_memory produces a usable MemoryRecord."""
    mem = generate_affect_memory(
        round_num=5,
        agent_id="ToyotaMotors",
        dominant_emotion="panicked",
        trigger="low fill from BoschAuto",
        involved_agents=["BoschAuto"],
        intensity=0.8,
    )
    _assert(mem.category == "own_decision", f"unexpected category: {mem.category}")
    _assert("feeling_panicked" in mem.tags, f"missing feeling tag: {mem.tags}")
    _assert("affect_change" in mem.tags, f"missing affect_change tag: {mem.tags}")
    _assert(mem.importance >= 8, f"strong feeling should be high importance: {mem.importance}")


def test_to_dict_shape() -> None:
    """Serialization keeps a predictable shape for the frontend."""
    a = AffectState.for_persona("TaiwanSemi")
    d = a.to_dict()
    for key in ["valence", "arousal", "fear", "anger", "trust_joy", "pride",
                "shame", "greed", "stress", "fatigue", "morale", "grudge",
                "dominant_emotion"]:
        _assert(key in d, f"missing key {key} in {list(d.keys())}")
    _assert(isinstance(d["grudge"], dict), f"grudge must be dict, got {type(d['grudge'])}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _all_tests() -> list:
    return [v for k, v in globals().items()
            if k.startswith("test_") and callable(v)]


def main() -> int:
    tests = _all_tests()
    failures: list[tuple[str, str]] = []
    for t in tests:
        name = t.__name__
        try:
            t()
        except AssertionError as exc:
            failures.append((name, str(exc)))
            print(f"FAIL  {name}: {exc}")
        except Exception as exc:  # pragma: no cover - surface unexpected errors
            failures.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok    {name}")

    print(f"\n{len(tests) - len(failures)}/{len(tests)} tests passed.")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
