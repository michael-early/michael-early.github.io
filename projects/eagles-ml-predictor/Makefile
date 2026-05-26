.PHONY: install test lint dashboard predict evaluate

install:
	python -m pip install -e '.[dev]'

test:
	python -m pytest

lint:
	python -m ruff check app src tests

dashboard:
	streamlit run app/streamlit_app.py

predict:
	eagles-ml predict-2026 --model best --output outputs/eagles_2026_predictions.csv

evaluate:
	eagles-ml evaluate --dataset data/processed/historical_games.csv
