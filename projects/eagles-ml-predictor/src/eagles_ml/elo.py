from __future__ import annotations

from dataclasses import dataclass
from math import log10

DEFAULT_ELO = 1500.0


def win_probability_from_diff(rating_diff: float) -> float:
    """Convert an Elo rating difference to expected win probability."""
    return 1.0 / (1.0 + 10.0 ** (-rating_diff / 400.0))


def rating_diff_from_probability(probability: float) -> float:
    """Convert a win probability to an Elo rating gap."""
    clipped = min(max(probability, 0.001), 0.999)
    return 400.0 * log10(clipped / (1.0 - clipped))


def smoothed_win_pct(
    wins: float,
    losses: float,
    ties: float = 0.0,
    prior_games: float = 8.0,
) -> float:
    """Shrink last-season record toward league average before converting to team strength."""
    games = wins + losses + ties
    return (wins + 0.5 * ties + 0.5 * prior_games) / (games + prior_games)


def prior_elo_from_record(
    wins: float,
    losses: float,
    ties: float = 0.0,
    *,
    league_average: float = DEFAULT_ELO,
    scale: float = 0.55,
) -> float:
    """Build a conservative preseason Elo prior from last season's record.

    The scale keeps a single-season record from becoming too certain. NFL outcomes are noisy,
    and offseason roster/coaching changes mean record-only priors should be shrunk heavily.
    """
    pct = smoothed_win_pct(wins, losses, ties)
    return league_average + scale * rating_diff_from_probability(pct)


@dataclass(frozen=True)
class Matchup:
    team_rating: float
    opponent_rating: float
    site: str
    home_field_elo: float = 55.0
    situational_elo: float = 0.0

    def team_probability(self) -> float:
        diff = self.team_rating - self.opponent_rating + self.situational_elo
        if self.site == "home":
            diff += self.home_field_elo
        elif self.site == "away":
            diff -= self.home_field_elo
        elif self.site in {"neutral", "bye"}:
            diff += 0.0
        else:
            raise ValueError(f"Unknown site: {self.site}")
        return win_probability_from_diff(diff)
