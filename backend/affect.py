"""Persistent multi-dimensional affect (emotion) state for supply-chain agents.

Replaces the single ``emotional_state: str`` with a state that actually drives
behavior — fear nudges hoarding, anger shows up as punitive allocation, grudges
persist across rounds, signals carry affective valence/arousal for contagion.

Design goals
------------
* Dimensional core (valence/arousal) for interpretability and contagion math.
* Specific emotions with intensity 0..1 for behavioral coupling.
* Slow-moving physiological traits (stress, fatigue, morale) distinct from
  transient emotions.
* Per-partner ``grudge`` that accumulates from insults (starvation, hoarding,
  alternative-seeking) and decays slowly.
* Pure data + numeric helpers; no LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Tunable constants — kept in one place so balancing is easy
# ---------------------------------------------------------------------------

_DECAY_PER_ROUND = 0.15          # emotion intensity decay per round (multiplicative)
_STRESS_DECAY = 0.10             # slower decay for physio state
_FATIGUE_RECOVERY = 0.08
_GRUDGE_DECAY = 0.08

_DEFAULT_MORALE = 0.65
_DEFAULT_STRESS = 0.20
_DEFAULT_FATIGUE = 0.10

# Mapping of specific emotions to (valence, arousal) contribution for the
# dimensional projection.  Used both for prompt brief and for signal contagion.
_EMO_TO_VA: dict[str, tuple[float, float]] = {
    "fear": (-0.7, 0.7),
    "anger": (-0.6, 0.8),
    "trust_joy": (0.7, 0.4),
    "pride": (0.6, 0.5),
    "shame": (-0.6, 0.3),
    "greed": (0.2, 0.6),
}


# ---------------------------------------------------------------------------
# Persona seed traits — gives each agent a distinct emotional baseline
# ---------------------------------------------------------------------------

# These nudge the starting AffectState; they're not a full personality model,
# just enough to differentiate how agents react emotionally.
PERSONA_AFFECT_SEEDS: dict[str, dict[str, float]] = {
    # Foundries — confident, high pride, moderate stress from complexity
    "TaiwanSemi":   {"pride": 0.6, "stress": 0.35, "morale": 0.75, "greed": 0.35},
    "KoreaSilicon": {"pride": 0.4, "stress": 0.5,  "morale": 0.60, "greed": 0.6, "anger": 0.15},

    # Chip designers — sandwiched, higher baseline stress
    "EuroChip":     {"fear": 0.35, "stress": 0.45, "morale": 0.55},
    "AmeriSemi":    {"pride": 0.35, "greed": 0.45, "stress": 0.35, "morale": 0.70},

    # Tier-1 suppliers — squeezed between OEMs and chip designers
    "BoschAuto":    {"stress": 0.55, "fear": 0.30, "pride": 0.50, "morale": 0.55},
    "ContiParts":   {"stress": 0.60, "anger": 0.20, "greed": 0.35, "morale": 0.50},

    # OEMs — disciplined Toyota, bold Ford, reactive VW
    "ToyotaMotors": {"pride": 0.55, "trust_joy": 0.30, "stress": 0.20, "morale": 0.80},
    "FordAuto":     {"pride": 0.40, "anger": 0.20, "stress": 0.40, "morale": 0.60, "greed": 0.30},
    "VolkswagenAG": {"fear": 0.50, "anger": 0.30, "stress": 0.65, "morale": 0.35, "shame": 0.35},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _clip11(x: float) -> float:
    return max(-1.0, min(1.0, x))


# ---------------------------------------------------------------------------
# AffectState
# ---------------------------------------------------------------------------

@dataclass
class AffectState:
    """Mutable affective/psychological state for a single agent."""

    # Dimensional core (derived most of the time, but stored so contagion can
    # directly move it even when no specific emotion fits).
    valence: float = 0.1          # -1 (unpleasant) .. +1 (pleasant)
    arousal: float = 0.3          # 0 (calm) .. 1 (activated)

    # Specific emotions (intensity 0..1)
    fear: float = 0.10
    anger: float = 0.05
    trust_joy: float = 0.30       # warm feelings toward partners generally
    pride: float = 0.30
    shame: float = 0.05
    greed: float = 0.20

    # Physiological / slow-moving traits (0..1)
    stress: float = _DEFAULT_STRESS
    fatigue: float = _DEFAULT_FATIGUE
    morale: float = _DEFAULT_MORALE

    # Per-partner grudge (0..1) — persistent, decays slowly.
    grudge: dict[str, float] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def for_persona(cls, agent_id: str) -> "AffectState":
        """Create a new AffectState seeded from a persona's emotional profile."""
        state = cls()
        seed = PERSONA_AFFECT_SEEDS.get(agent_id, {})
        for key, value in seed.items():
            if hasattr(state, key):
                setattr(state, key, _clip01(float(value)))
        state._recompute_va()
        return state

    # ------------------------------------------------------------------
    # Dimensional projection
    # ------------------------------------------------------------------
    def _recompute_va(self) -> None:
        """Recompute valence/arousal from specific emotions + morale/stress.

        Uses a weighted average of each emotion's V/A contribution, weighted
        by its intensity, with morale pulling valence up and stress pulling
        arousal up.
        """
        numer_v = 0.0
        numer_a = 0.0
        weight = 0.0
        for name, (v, a) in _EMO_TO_VA.items():
            intensity = getattr(self, name, 0.0)
            if intensity <= 0.0:
                continue
            numer_v += v * intensity
            numer_a += a * intensity
            weight += intensity

        if weight > 0:
            emo_v = numer_v / weight
            emo_a = numer_a / weight
        else:
            emo_v, emo_a = 0.0, 0.0

        # Morale adds a steady pleasant tone; stress raises arousal baseline.
        morale_tilt = (self.morale - 0.5) * 0.4
        stress_tilt = self.stress * 0.3

        self.valence = _clip11(emo_v * min(1.0, weight) + morale_tilt)
        self.arousal = _clip01(max(emo_a * min(1.0, weight), stress_tilt))

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    def decay(self) -> None:
        """Per-round decay of transient emotions and grudges."""
        for name in _EMO_TO_VA:
            setattr(self, name, _clip01(getattr(self, name) * (1 - _DECAY_PER_ROUND)))
        self.stress = _clip01(self.stress * (1 - _STRESS_DECAY))
        self.fatigue = _clip01(self.fatigue * (1 - _FATIGUE_RECOVERY))
        # Morale drifts gently back toward default so it doesn't collapse permanently.
        self.morale = _clip01(self.morale + 0.5 * _STRESS_DECAY * (_DEFAULT_MORALE - self.morale))
        # Grudges fade but linger
        self.grudge = {
            pid: v * (1 - _GRUDGE_DECAY)
            for pid, v in self.grudge.items()
            if v * (1 - _GRUDGE_DECAY) > 0.02
        }
        self._recompute_va()

    def update_from_outcome(
        self,
        *,
        fill_rate: float | None = None,
        profit: float | None = None,
        partner_fills: dict[str, float] | None = None,
        partner_hoarding: dict[str, int] | None = None,
        partner_seeking_alternatives: dict[str, bool] | None = None,
    ) -> None:
        """Adjust affect based on this round's realized outcomes.

        Everything is additive with clipping — designed to be called once per
        round before ``decay()``.
        """
        # Own fill rate (buyer perspective)
        if fill_rate is not None:
            if fill_rate < 0.8:
                shortfall = 0.8 - fill_rate
                self.fear = _clip01(self.fear + 0.45 * shortfall)
                self.anger = _clip01(self.anger + 0.35 * shortfall)
                self.stress = _clip01(self.stress + 0.40 * shortfall)
                self.morale = _clip01(self.morale - 0.30 * shortfall)
                self.pride = _clip01(self.pride - 0.20 * shortfall)
            elif fill_rate >= 0.95:
                self.trust_joy = _clip01(self.trust_joy + 0.15)
                self.pride = _clip01(self.pride + 0.10)
                self.fear = _clip01(self.fear - 0.10)
                self.morale = _clip01(self.morale + 0.05)

        if profit is not None:
            if profit < 0:
                self.shame = _clip01(self.shame + 0.12)
                self.stress = _clip01(self.stress + 0.10)
                self.morale = _clip01(self.morale - 0.10)
            elif profit > 0:
                self.pride = _clip01(self.pride + 0.05)
                self.morale = _clip01(self.morale + 0.03)

        # Per-partner grudges from their behavior toward us
        if partner_fills:
            for pid, fill in partner_fills.items():
                if fill < 0.6:
                    # They starved us — grudge scales with how badly
                    shortfall = (0.6 - fill) / 0.6
                    self._bump_grudge(pid, 0.35 * shortfall)
                    self.anger = _clip01(self.anger + 0.20 * (0.6 - fill))
                elif fill >= 0.95:
                    # They came through — soften the grudge
                    self._relax_grudge(pid, 0.10)
                    self.trust_joy = _clip01(self.trust_joy + 0.05)

        if partner_hoarding:
            for pid, held in partner_hoarding.items():
                if held > 50:
                    self._bump_grudge(pid, 0.10)
                    self.anger = _clip01(self.anger + 0.05)

        if partner_seeking_alternatives:
            for pid, seeking in partner_seeking_alternatives.items():
                if seeking:
                    # Seen as betrayal by the supplier looking at this buyer
                    self._bump_grudge(pid, 0.30)
                    self.anger = _clip01(self.anger + 0.15)
                    self.shame = _clip01(self.shame + 0.08)

        self._recompute_va()

    def update_from_event_valence(
        self,
        *,
        fear: float = 0.0,
        greed: float = 0.0,
        stress: float = 0.0,
        morale: float = 0.0,
    ) -> None:
        """Apply a scenario-wide emotional nudge (positive or negative).

        Values are deltas, not absolutes — typically in [-0.5, 0.5].
        """
        self.fear = _clip01(self.fear + fear)
        self.greed = _clip01(self.greed + greed)
        self.stress = _clip01(self.stress + stress)
        self.morale = _clip01(self.morale + morale)
        self._recompute_va()

    def update_from_signal(
        self,
        *,
        sender_valence: float,
        sender_arousal: float,
        alpha: float = 0.1,
    ) -> None:
        """Contagion: drift valence/arousal toward the sender's, weighted by alpha.

        ``alpha`` is typically driven by trust in the sender (0..1).  Also
        drags specific emotions in the sign-appropriate direction.
        """
        alpha = _clip01(alpha)
        if alpha <= 0:
            return
        self.valence = _clip11(self.valence + alpha * (sender_valence - self.valence))
        self.arousal = _clip01(self.arousal + alpha * (sender_arousal - self.arousal))

        # High-arousal negative affect -> spreads fear/anger proportional to alpha
        if sender_valence < -0.2 and sender_arousal > 0.5:
            self.fear = _clip01(self.fear + alpha * 0.30 * sender_arousal)
            self.anger = _clip01(self.anger + alpha * 0.15 * sender_arousal)
        # Positive arousal -> boosts trust_joy/morale
        elif sender_valence > 0.3:
            self.trust_joy = _clip01(self.trust_joy + alpha * 0.20 * sender_valence)
            self.morale = _clip01(self.morale + alpha * 0.10 * sender_valence)

    def accumulate_fatigue(self) -> None:
        """Call once per round — fatigue rises proportional to stress."""
        self.fatigue = _clip01(self.fatigue + 0.5 * self.stress * (1 - self.fatigue))

    # ------------------------------------------------------------------
    # Grudge helpers
    # ------------------------------------------------------------------
    def _bump_grudge(self, pid: str, amount: float) -> None:
        current = self.grudge.get(pid, 0.0)
        self.grudge[pid] = _clip01(current + amount)

    def _relax_grudge(self, pid: str, amount: float) -> None:
        current = self.grudge.get(pid, 0.0)
        new = max(0.0, current - amount)
        if new > 0.02:
            self.grudge[pid] = new
        else:
            self.grudge.pop(pid, None)

    # ------------------------------------------------------------------
    # Behavior modifiers — pure numeric knobs the mechanics layer uses
    # ------------------------------------------------------------------
    def panic_order_multiplier(self) -> float:
        """Buyer-side: scale for orders when the agent is panicking.

        Returns a value in ~[1.0, 1.6].  Pure fear bumps orders; grudges
        against the whole supply base do *not* bump the total (they shift
        distribution, handled separately).
        """
        return 1.0 + 0.50 * self.fear + 0.25 * self.stress * self.arousal

    def hoard_multiplier(self) -> float:
        """Supplier-side: scale for held_in_reserve.  Returns ~[1.0, 2.0]."""
        return 1.0 + 0.60 * self.fear + 0.40 * self.greed * (1 - self.trust_joy)

    def grudge_price_penalty(self, pid: str) -> float:
        """Buyer-side: fraction to shave off max_price_willing_to_pay for a
        disliked supplier.  Returns 0..0.4."""
        g = self.grudge.get(pid, 0.0)
        if g < 0.4:
            return 0.0
        return _clip01(0.4 * (g - 0.4) / 0.6)

    def allocation_emotional_factor(self, pid: str) -> float:
        """Supplier-side: multiplier on the per-buyer allocation score.

        Grudge and general anger reduce it; trust_joy raises it slightly.
        Returns ~[0.2, 1.3].
        """
        g = self.grudge.get(pid, 0.0)
        anger_pen = 1.0 - 0.5 * self.anger
        grudge_pen = 1.0 - 0.8 * g
        positive = 1.0 + 0.15 * self.trust_joy
        return max(0.2, anger_pen * grudge_pen * positive)

    def cognitive_load(self) -> float:
        """Combined stress+fatigue metric in 0..1; used for attention narrowing."""
        return _clip01(0.6 * self.fatigue + 0.4 * self.stress)

    # ------------------------------------------------------------------
    # Human-readable summary (for LLM prompts + UI)
    # ------------------------------------------------------------------
    def dominant_emotion(self) -> str:
        """Return a short label for the top-intensity specific emotion.

        Kept for backward compatibility with callers still expecting a single
        ``emotional_state`` string.
        """
        emos = {name: getattr(self, name) for name in _EMO_TO_VA}
        if not emos:
            return "confident"
        top_name, top_val = max(emos.items(), key=lambda kv: kv[1])
        if top_val < 0.15:
            # Fall back to dimensional reading
            if self.valence > 0.3 and self.arousal < 0.5:
                return "confident"
            if self.valence > 0.3:
                return "opportunistic"
            if self.arousal > 0.6 and self.valence < 0:
                return "panicked"
            if self.valence < -0.2:
                return "anxious"
            return "cautious"
        mapping = {
            "fear": "panicked" if top_val > 0.6 else "anxious",
            "anger": "vindictive" if top_val > 0.6 else "angry",
            "trust_joy": "loyal",
            "pride": "confident",
            "shame": "cautious",
            "greed": "opportunistic",
        }
        return mapping.get(top_name, "cautious")

    def to_prompt_brief(self) -> str:
        """A compact, LLM-friendly description of psychological state.

        Only surfaces emotions/grudges that are actually salient so the prompt
        doesn't get cluttered with noise.
        """
        lines: list[str] = []

        # Specific emotions above threshold
        sorted_emos = sorted(
            ((name, getattr(self, name)) for name in _EMO_TO_VA),
            key=lambda kv: kv[1],
            reverse=True,
        )
        for name, val in sorted_emos:
            if val < 0.20:
                continue
            lines.append(f"- {name.replace('_', ' ').title()} ({val:.2f}): {self._emotion_guidance(name, val)}")

        if self.stress >= 0.45:
            lines.append(
                f"- Stress ({self.stress:.2f}): focus is tight; you may overreact to bad news."
            )
        if self.fatigue >= 0.40:
            lines.append(
                f"- Fatigue ({self.fatigue:.2f}): cognitive bandwidth is limited; simplify your reasoning."
            )
        if self.morale <= 0.35:
            lines.append(
                f"- Morale ({self.morale:.2f}): you feel demoralized; hard to make bold moves."
            )

        salient_grudges = sorted(
            ((pid, v) for pid, v in self.grudge.items() if v >= 0.3),
            key=lambda kv: kv[1],
            reverse=True,
        )
        for pid, g in salient_grudges:
            lines.append(
                f"- Grudge toward {pid} ({g:.2f}): you feel wronged and may want to punish them "
                f"even at some cost to yourself."
            )

        if not lines:
            lines.append("- You feel emotionally neutral and composed.")

        header = (
            f"YOUR CURRENT PSYCHOLOGICAL STATE "
            f"(valence {self.valence:+.2f}, arousal {self.arousal:.2f}):"
        )
        return header + "\n" + "\n".join(lines)

    def _emotion_guidance(self, name: str, intensity: float) -> str:
        """Short behavioral guidance per emotion for the prompt."""
        if name == "fear":
            if intensity > 0.6:
                return "urge to hoard inventory and over-order beyond real demand."
            return "caution and a slight bias toward safety stock."
        if name == "anger":
            if intensity > 0.6:
                return "desire to punish those who wronged you, even at cost."
            return "reduced willingness to accommodate difficult partners."
        if name == "trust_joy":
            return "warmth toward reliable partners; willingness to be generous."
        if name == "pride":
            return "confidence in your strategy; inclination to stand firm."
        if name == "shame":
            return "self-doubt; tendency to second-guess recent choices."
        if name == "greed":
            if intensity > 0.5:
                return "strong pull to maximize price/margin even if it strains relationships."
            return "alertness to margin opportunities."
        return ""

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "fear": round(self.fear, 3),
            "anger": round(self.anger, 3),
            "trust_joy": round(self.trust_joy, 3),
            "pride": round(self.pride, 3),
            "shame": round(self.shame, 3),
            "greed": round(self.greed, 3),
            "stress": round(self.stress, 3),
            "fatigue": round(self.fatigue, 3),
            "morale": round(self.morale, 3),
            "grudge": {k: round(v, 3) for k, v in self.grudge.items()},
            "dominant_emotion": self.dominant_emotion(),
        }
