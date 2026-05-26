from eagles_ml.projections import load_priors, load_schedule, project_eagles_games


def test_schedule_contains_17_games_and_bye() -> None:
    schedule = load_schedule()
    assert len(schedule[schedule["site"] != "bye"]) == 17
    assert len(schedule[schedule["site"] == "bye"]) == 1


def test_priors_include_all_scheduled_opponents() -> None:
    schedule = load_schedule()
    priors = load_priors()
    teams = set(priors["team"])
    opponents = set(schedule.loc[schedule["site"] != "bye", "opponent"])
    assert "PHI" in teams
    assert opponents <= teams


def test_projection_outputs_probabilities_for_all_games() -> None:
    predictions = project_eagles_games()
    assert len(predictions) == 17
    assert predictions["eagles_win_probability"].between(0, 1).all()
    assert set(predictions["projected_result"]) <= {"W", "L"}
