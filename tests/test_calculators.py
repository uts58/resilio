import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.tools.calculators import (
    calc_it_budget,
    calc_sle,
    calc_aro,
    calc_ale,
    calc_rosi,
    calc_risk,
    calc_risk_reduction,
    calc_safeguard_value,
    calc_payback_period,
    calc_it_risk_score,
)


def test_calc_it_budget():
    assert float(calc_it_budget(1_000_000)) == pytest.approx(14_700.0)


def test_calc_it_budget_zero():
    assert float(calc_it_budget(0)) == 0.0


def test_calc_sle():
    assert float(calc_sle(100_000, 0.5)) == pytest.approx(50_000.0)


def test_calc_sle_full_loss():
    assert float(calc_sle(200_000, 1.0)) == pytest.approx(200_000.0)


def test_calc_aro():
    assert float(calc_aro(2.5)) == pytest.approx(2.5)


def test_calc_ale():
    assert float(calc_ale(50_000, 2.0)) == pytest.approx(100_000.0)


def test_calc_rosi():
    # ROSI = ((exposure * loss_reduction) - cost) / cost * 100
    result = float(calc_rosi(100_000, 0.8, 20_000))
    assert result == pytest.approx(300.0)


def test_calc_risk():
    assert float(calc_risk(0.8, 0.5, 0.9)) == pytest.approx(0.36)


def test_calc_risk_reduction():
    # (100 - 40) / 100 * 100 = 60%
    assert float(calc_risk_reduction(100, 40)) == pytest.approx(60.0)


def test_calc_risk_reduction_zero_before():
    assert float(calc_risk_reduction(0, 40)) == 0.0


def test_calc_safeguard_value():
    assert float(calc_safeguard_value(80_000, 30_000)) == pytest.approx(50_000.0)


def test_calc_payback_period():
    assert float(calc_payback_period(100_000, 25_000)) == pytest.approx(4.0)


def test_calc_payback_period_zero_savings():
    assert float(calc_payback_period(100_000, 0)) == float("inf")


def test_calc_it_risk_score_clamped_high():
    # Max possible: 1*1*1*(1-0)*20 = 20 → clamped to 100
    assert float(calc_it_risk_score(1, 1, 1, 0)) == pytest.approx(20.0)


def test_calc_it_risk_score_with_safeguard():
    # 0.8 * 0.7 * 0.9 * (1-0.5) * 20 = 0.252 * 10 = 5.04
    assert float(calc_it_risk_score(0.8, 0.7, 0.9, 0.5)) == pytest.approx(5.04)


def test_calc_it_risk_score_clamped_low():
    assert float(calc_it_risk_score(0, 0, 0, 1)) == 0.0
