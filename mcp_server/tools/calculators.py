from mcp.server.fastmcp import FastMCP


def calc_it_budget(revenue: float) -> str:
    """Estimate IT budget as ≈1.47% of annual revenue."""
    return str(revenue * 0.0147)


def calc_sle(asset_value: float, exposure_factor: float) -> str:
    """Single Loss Expectancy = Asset Value × Exposure Factor."""
    return str(asset_value * exposure_factor)


def calc_aro(incidents_per_year: float) -> str:
    """Annual Rate of Occurrence (pass-through; use as input to calc_ale)."""
    return str(incidents_per_year)


def calc_ale(sle: float, aro: float) -> str:
    """Annualized Loss Expectancy = SLE × Annual Rate of Occurrence."""
    return str(sle * aro)


def calc_rosi(exposure: float, loss_reduction: float, cost: float) -> str:
    """Return on Security Investment = ((Exposure × Loss Reduction) − Cost) / Cost × 100."""
    return str(((exposure * loss_reduction) - cost) / cost * 100)


def calc_risk(threat: float, vulnerability: float, impact: float) -> str:
    """Basic risk score = Threat × Vulnerability × Impact."""
    return str(threat * vulnerability * impact)


def calc_risk_reduction(risk_before: float, risk_after: float) -> str:
    """Risk reduction % = (Risk_before − Risk_after) / Risk_before × 100."""
    if not risk_before:
        return "0"
    return str((risk_before - risk_after) / risk_before * 100)


def calc_safeguard_value(ale_before: float, ale_after: float) -> str:
    """Safeguard value = ALE_before − ALE_after."""
    return str(ale_before - ale_after)


def calc_payback_period(investment_cost: float, annual_savings: float) -> str:
    """Payback period in years = Investment Cost ÷ Annual Savings."""
    if not annual_savings:
        return str(float("inf"))
    return str(investment_cost / annual_savings)


def calc_it_risk_score(
    threat: float,
    vulnerability: float,
    impact: float,
    safeguard_effectiveness: float,
) -> str:
    """Normalized cybersecurity risk score (0–100). All inputs should be in [0, 1]."""
    raw = threat * vulnerability * impact * (1 - safeguard_effectiveness) * 20
    return str(max(0.0, min(100.0, raw)))


_CALCULATORS = [
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
]


def register(mcp: FastMCP) -> None:
    for fn in _CALCULATORS:
        mcp.tool()(fn)