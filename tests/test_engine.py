# Just run pytest tests/ later
import pytest
from app.engine import DecisionEngine

def test_happy_path():
    engine = DecisionEngine({"loan_approval": {"stages": [...]}})  # simplified
    # ... (I kept it short but you can expand)s