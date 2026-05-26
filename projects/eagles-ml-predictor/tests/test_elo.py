from eagles_ml.elo import Matchup, prior_elo_from_record, win_probability_from_diff


def test_win_probability_is_symmetric() -> None:
    favorite = win_probability_from_diff(100)
    underdog = win_probability_from_diff(-100)
    assert round(favorite + underdog, 10) == 1.0


def test_record_prior_orders_stronger_team_above_weaker_team() -> None:
    strong = prior_elo_from_record(12, 5, 0)
    weak = prior_elo_from_record(5, 12, 0)
    assert strong > weak


def test_home_field_raises_probability() -> None:
    home = Matchup(1500, 1500, "home").team_probability()
    away = Matchup(1500, 1500, "away").team_probability()
    assert home > 0.5
    assert away < 0.5
