"""Product Analytics & A/B Testing Platform — corrected five-tab Streamlit dashboard."""
from pathlib import Path
from datetime import date, timedelta
import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import chisquare
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (
    confint_proportions_2indep, proportion_effectsize, proportions_ztest,
)

st.set_page_config(page_title="A/B Testing Analytics", page_icon="📊", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1380px; padding-top: 2rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {background: rgba(128,128,128,.075); border: 1px solid rgba(128,128,128,.15); border-radius: 12px; padding: 16px; min-height: 105px;}
[data-testid="stMetricLabel"] {font-size: .9rem;}
[data-testid="stMetricValue"] {font-size: clamp(1.25rem, 2vw, 2rem);}
</style>""", unsafe_allow_html=True)
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "ab_test_users.csv"

@st.cache_data
def load_data(path):
    return pd.read_csv(path)

with st.sidebar:
    st.header("Experiment Configuration")
    st.subheader("Conversion Rate Assumptions")
    baseline_rate = st.number_input("Baseline Conversion Rate (%)", min_value=0.01, max_value=99.99, value=11.0, step=0.5, format="%.2f")
    target_rate = st.number_input("Target Conversion Rate (%)", min_value=0.01, max_value=99.99, value=13.0, step=0.5, format="%.2f")
    st.subheader("Statistical Settings")
    power = st.selectbox("Statistical Power", [0.80, 0.85, 0.90, 0.95], format_func=lambda x: f"{x:.0%}")
    alpha = st.selectbox("Significance Level", [0.05, 0.01, 0.10], format_func=lambda x: f"{x:.0%}")
    if target_rate <= baseline_rate:
        st.warning("Set target conversion above baseline for uplift sample-size planning.")

st.title("Product Analytics & A/B Testing Platform")
st.write("Analyze experiments, compare conversion rates, and evaluate product performance.")
if not DATA_PATH.exists():
    st.error(f"Dataset not found: {DATA_PATH}. Keep app_fixed.py in the dashboard folder and ab_test_users.csv in the data folder.")
    st.stop()
try:
    users_df = load_data(str(DATA_PATH))
except Exception as exc:
    st.error(f"Could not read experiment dataset: {exc}")
    st.stop()
required_columns = {"user_id", "experiment_group", "converted"}
missing_columns = required_columns - set(users_df.columns)
if missing_columns:
    st.error(f"Missing required columns: {', '.join(sorted(missing_columns))}")
    st.stop()

# Validate before statistical analysis; show data-quality details in tab 3.
missing_values = int(users_df.isna().sum().sum())
duplicate_users = int(users_df["user_id"].duplicated().sum())
invalid_conversions = int((~users_df["converted"].isin([0, 1])).sum())
invalid_groups = int((~users_df["experiment_group"].isin(["A", "B"])).sum())
if missing_values or duplicate_users or invalid_conversions or invalid_groups:
    st.error("Dataset validation failed. Correct missing values, duplicate user IDs, invalid conversions, or experiment groups before interpreting results.")
    st.write({"Missing values": missing_values, "Duplicate users": duplicate_users, "Invalid conversions": invalid_conversions, "Invalid groups": invalid_groups})
    st.stop()

metrics = users_df.groupby("experiment_group").agg(
    total_users=("user_id", "count"), total_conversions=("converted", "sum"), conversion_rate=("converted", "mean")
)
if not {"A", "B"}.issubset(metrics.index) or (metrics.loc[["A", "B"], "total_users"] == 0).any():
    st.error("Both Group A and Group B must contain users.")
    st.stop()
A, B = metrics.loc["A"], metrics.loc["B"]
rate_a, rate_b = float(A["conversion_rate"]), float(B["conversion_rate"])
uplift = rate_b - rate_a
absolute_uplift = uplift * 100
relative_uplift = (uplift / rate_a * 100) if rate_a > 0 else float("nan")
counts = [int(A["total_conversions"]), int(B["total_conversions"])]
ns = [int(A["total_users"]), int(B["total_users"])]
if sum(counts) in (0, sum(ns)):
    z_stat, p_value = 0.0, 1.0
else:
    z_stat, p_value = proportions_ztest(counts, ns)
    z_stat, p_value = float(z_stat), float(p_value)
try:
    ci_lower, ci_upper = confint_proportions_2indep(count1=counts[1], nobs1=ns[1], count2=counts[0], nobs2=ns[0], compare="diff", method="newcomb", alpha=alpha)
except ValueError:
    ci_lower, ci_upper = float("nan"), float("nan")

power_analysis = NormalIndPower()
def sample_size_per_group(base, target, selected_power, significance):
    if not (0 < base < 1 and 0 < target < 1) or base == target:
        return None
    effect = abs(proportion_effectsize(base, target))
    try:
        result = power_analysis.solve_power(effect_size=effect, alpha=significance, power=selected_power, ratio=1.0, alternative="two-sided")
        return math.ceil(result) if np.isfinite(result) and result > 0 else None
    except (ValueError, ZeroDivisionError, OverflowError):
        return None

required_per_group = sample_size_per_group(baseline_rate / 100, target_rate / 100, power, alpha)
total_required_users = required_per_group * 2 if required_per_group is not None else None
current_users = len(users_df)
remaining_users = max(0, total_required_users - current_users) if total_required_users is not None else None
progress = min(current_users / total_required_users, 1.0) if total_required_users else 0.0
n_a, n_b = ns
group_a_percentage = n_a / current_users * 100
group_b_percentage = n_b / current_users * 100
srm_statistic, srm_p_value = chisquare([n_a, n_b], f_exp=[current_users / 2] * 2)
srm_statistic, srm_p_value = float(srm_statistic), float(srm_p_value)
quality_checks = {"Missing Values": missing_values == 0, "Duplicate Users": duplicate_users == 0,
                  "Invalid Conversions": invalid_conversions == 0, "Valid Experiment Groups": invalid_groups == 0,
                  "Sample Ratio Mismatch": srm_p_value >= 0.001}
data_quality_healthy = all(list(quality_checks.values())[:4])
allocation_healthy = srm_p_value >= 0.001
sample_size_healthy = total_required_users is not None and current_users >= total_required_users
if not data_quality_healthy or not allocation_healthy:
    decision = "Investigate Experiment"
elif not sample_size_healthy:
    decision = "Sample Size Target Not Reached"
elif p_value < alpha and uplift > 0:
    decision = "Consider Launching Group B"
elif p_value < alpha and uplift < 0:
    decision = "Keep Group A"
else:
    decision = "Inconclusive Result"

(tab1, tab2, tab3, tab4, tab5) = st.tabs(["Overview", "A/B Test Analysis", "Data Quality", "Experiment Monitoring", "Decision Intelligence"])

with tab1:
    st.header("Experiment Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Users", f"{current_users:,}")
    c2.metric("Group A Users", f"{n_a:,}")
    c3.metric("Group B Users", f"{n_b:,}")
    st.caption("Control (A) vs treatment (B) · Two-sided comparison of conversion rates")
    st.subheader("Conversion Snapshot")
    c1, c2, c3 = st.columns(3)
    c1.metric("Control Conversion", f"{rate_a:.2%}")
    c2.metric("Treatment Conversion", f"{rate_b:.2%}")
    c3.metric("Observed Uplift", f"{absolute_uplift:+.2f} pp")
    st.info(f"Decision status: **{decision}**. The observed difference is {'not ' if p_value >= alpha else ''}statistically significant at α={alpha:.0%} (p={p_value:.4f}).")
    st.subheader("Group Summary")
    summary = metrics.reset_index().rename(columns={"experiment_group":"Group", "total_users":"Users", "total_conversions":"Conversions", "conversion_rate":"Conversion Rate"})
    st.dataframe(summary.style.format({"Users":"{:,.0f}", "Conversions":"{:,.0f}", "Conversion Rate":"{:.2%}"}), use_container_width=True, hide_index=True)
    with st.expander("Preview experiment dataset"):
        st.dataframe(users_df.head(20), use_container_width=True, hide_index=True)

with tab2:
    st.header("A/B Test Performance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Group A Conversion", f"{rate_a:.2%}")
    c2.metric("Group B Conversion", f"{rate_b:.2%}")
    c3.metric("Absolute Uplift", f"{absolute_uplift:+.2f} pp")
    c4.metric("Relative Uplift", f"{relative_uplift:+.2f}%" if np.isfinite(relative_uplift) else "N/A")
    st.caption("Conversion rates are observed outcomes. Statistical significance and practical impact are evaluated separately below.")
    st.subheader("Conversion Rate Comparison")
    chart_df = metrics.reset_index()[["experiment_group", "conversion_rate"]].copy()
    chart_df["conversion_rate"] *= 100
    fig = px.bar(chart_df, x="experiment_group", y="conversion_rate", color="experiment_group", text="conversion_rate", labels={"experiment_group": "Experiment Group", "conversion_rate": "Conversion Rate (%)"})
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(showlegend=False, yaxis_range=[0, max(15, chart_df["conversion_rate"].max() * 1.2)])
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Statistical Significance Analysis")
    c1, c2 = st.columns(2)
    c1.metric("Z-Statistic", f"{z_stat:.4f}")
    c2.metric("P-Value", f"{p_value:.4f}")
    if p_value < alpha:
        st.success(f"Statistically significant at α = {alpha:.0%} (two-sided test).")
    else:
        st.warning(f"Not statistically significant at α = {alpha:.0%}.")
    st.subheader(f"{(1-alpha):.0%} Confidence Interval")
    c1, c2 = st.columns(2)
    c1.metric("Lower Bound", f"{ci_lower * 100:.2f} pp")
    c2.metric("Upper Bound", f"{ci_upper * 100:.2f} pp")
    st.info(f"Estimated Group B − Group A conversion difference: {absolute_uplift:+.2f} percentage points; {(1-alpha):.0%} CI [{ci_lower*100:.2f}, {ci_upper*100:.2f}] pp.")
    if ci_lower <= 0 <= ci_upper:
        st.caption("The confidence interval includes zero; the data are compatible with both a negative and positive treatment effect.")
    st.subheader("Experiment Decision Engine")
    st.info(f"Current assessment: {decision}. Review data quality, planned sample size and business guardrails before rollout.")
    st.divider()
    st.subheader("Sample Size & Power Analysis")
    if total_required_users:
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Users", f"{current_users:,}")
        c2.metric("Required Users", f"{total_required_users:,}")
        c3.metric("Additional Users Needed", f"{remaining_users:,}")
        st.progress(progress)
        st.caption(f"Sample size progress: {progress:.1%}. Assumes two equally sized groups, two-sided test, α={alpha:.0%}, power={power:.0%}.")
    else:
        st.warning("For sample-size planning, choose different baseline and target conversion rates.")
    st.subheader("Interactive Experiment Planner")
    c1, c2, c3 = st.columns(3)
    baseline_input = c1.slider("Planner Baseline Conversion (%)", 1.0, 50.0, float(max(1, min(50, baseline_rate))), 0.5)
    target_input = c2.slider("Planner Target Conversion (%)", 1.0, 50.0, float(max(1, min(50, target_rate))), 0.5)
    power_input = c3.slider("Planner Statistical Power (%)", 70, 95, int(power * 100), 5)
    baseline, target, selected_power = baseline_input / 100, target_input / 100, power_input / 100
    if target <= baseline:
        st.warning("Set the target conversion rate above the baseline conversion rate.")
    else:
        interactive_sample_size = sample_size_per_group(baseline, target, selected_power, alpha)
        if interactive_sample_size:
            c1, c2 = st.columns(2)
            c1.metric("Users Per Group", f"{interactive_sample_size:,}")
            c2.metric("Total Users Required", f"{interactive_sample_size*2:,}")
            st.info("Estimates assume equal group sizes and a two-sided test.")
    st.subheader("Sample Size Sensitivity Analysis")
    st.write("Explore how sample size changes as the target conversion rate increases.")
    target_rates = [baseline + i / 100 for i in range(1, 11) if baseline + i / 100 < 1]
    sensitivity_rows = []
    for rate in target_rates:
        n = sample_size_per_group(baseline, rate, selected_power, alpha)
        if n is not None:
            sensitivity_rows.append({"Target Conversion Rate (%)": round(rate * 100, 2), "Total Required Users": n * 2})
    if sensitivity_rows:
        sensitivity_df = pd.DataFrame(sensitivity_rows)
        fig = px.line(sensitivity_df, x="Target Conversion Rate (%)", y="Total Required Users", markers=True, title="Required Sample Size vs. Target Conversion Rate")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid sensitivity scenarios for these assumptions.")
    st.subheader(f"{(1-alpha):.0%} Confidence Interval Visualization")
    fig_ci = go.Figure()
    fig_ci.add_trace(go.Scatter(x=[ci_lower*100, ci_upper*100], y=["Conversion Uplift"]*2, mode="lines", line=dict(color="skyblue", width=8), name="Confidence Interval"))
    fig_ci.add_trace(go.Scatter(x=[absolute_uplift], y=["Conversion Uplift"], mode="markers", marker=dict(color="royalblue", size=16), name="Observed Uplift"))
    fig_ci.add_vline(x=0, line_dash="dash", line_color="red")
    fig_ci.update_layout(xaxis_title="Conversion Uplift (Percentage Points)", height=320)
    st.plotly_chart(fig_ci, use_container_width=True)

with tab3:
    st.header("Experiment Data Quality Report")
    st.write("Validate the experiment dataset before interpreting statistical results.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", f"{current_users:,}")
    c2.metric("Missing Values", missing_values)
    c3.metric("Duplicate Users", duplicate_users)
    c4.metric("Invalid Conversions", invalid_conversions)
    st.subheader("Experiment Group Balance Analysis")
    c1, c2, c3 = st.columns(3)
    c1.metric("Group A Users", f"{n_a:,}")
    c2.metric("Group B Users", f"{n_b:,}")
    c3.metric("Group Balance Difference", f"{abs(group_a_percentage-group_b_percentage):.2f} pp")
    balance_fig = px.bar(
        pd.DataFrame({
            "Experiment Group": ["A", "B"],
            "Users": [n_a, n_b]
        }),
        x="Experiment Group",
        y="Users",
        color="Experiment Group",
        text="Users"
    )

    balance_fig.update_yaxes(range=[0, 600])
    balance_fig.update_traces(textposition="outside")

    balance_fig.update_layout(
        showlegend=False,
        yaxis_title="Users",
        xaxis_title="Experiment Group"
    )

    st.plotly_chart(balance_fig, use_container_width=True)


    st.subheader("Sample Ratio Mismatch (SRM) Detection")
    c1, c2 = st.columns(2)
    c1.metric("SRM Chi-Square Statistic", f"{srm_statistic:.4f}")
    c2.metric("SRM P-Value", f"{srm_p_value:.4f}")

    if not allocation_healthy:
        st.error("Sample ratio mismatch detected (p < 0.001).")
    else:
        st.success("No sample ratio mismatch detected at the 0.001 threshold.")
    st.caption("SRM tests whether observed assignment matches the expected 50/50 allocation; a passing check does not establish that randomization was implemented correctly.")
    st.subheader("Automated Data Quality Assessment")
    for name, passed in quality_checks.items():
        (st.success if passed else st.error)(f"{'PASS' if passed else 'FAIL'}: {name}")
    c1, c2 = st.columns(2)
    c1.metric("Checks Passed", f"{sum(quality_checks.values())}/{len(quality_checks)}")
    c2.metric("Data Quality Score", f"{sum(quality_checks.values())/len(quality_checks):.0%}")

with tab4:
    st.header("Experiment Health Monitoring")
    c1, c2, c3 = st.columns(3)
    c1.metric("Data Quality", "Healthy" if data_quality_healthy else "Needs Attention")
    c2.metric("Sample Allocation", "Healthy" if allocation_healthy else "Needs Attention")
    c3.metric("Sample Size", "Ready" if sample_size_healthy else "Insufficient")
    st.subheader("Overall Experiment Health Assessment")
    health_checks = [data_quality_healthy, allocation_healthy, sample_size_healthy]
    health_score = sum(health_checks) / len(health_checks)
    c1, c2 = st.columns(2)
    c1.metric("Health Checks Passed", f"{sum(health_checks)}/{len(health_checks)}")
    c2.metric("Experiment Health Score", f"{health_score:.1%}")
    st.progress(health_score)
    st.caption("Health score is a simple fraction of three checks, not a validated probability of experiment success.")
    st.subheader("Experiment Readiness Decision")
    st.info(decision)
    st.divider()
    st.header("Experiment Progress Forecasting")
    daily_traffic = st.number_input("Expected Daily Experiment Users", min_value=1, value=200, step=50)
    if remaining_users is None:
        st.warning("Set a valid sample-size target in the sidebar to enable forecasts.")
    else:
        estimated_days = math.ceil(remaining_users / daily_traffic)
        estimated_completion_date = date.today() + timedelta(days=estimated_days)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Users", f"{current_users:,}")
        c2.metric("Remaining Users", f"{remaining_users:,}")
        c3.metric("Estimated Days Remaining", estimated_days)
        c4.metric("Estimated Completion Date", estimated_completion_date.strftime("%b %d, %Y"))
        st.progress(progress)
        st.caption(f"Experiment sample size progress: {progress:.1%}. Forecast assumes constant daily traffic.")
        st.subheader("Traffic Scenario Simulator")
        scenario_df = pd.DataFrame([{"Daily Users": traffic, "Estimated Days Remaining": math.ceil(remaining_users / traffic)} for traffic in [100, 200, 300, 500, 1000]])
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
        st.plotly_chart(px.line(scenario_df, x="Daily Users", y="Estimated Days Remaining", markers=True, title="Impact of Daily Traffic on Experiment Duration"), use_container_width=True)
        st.subheader("Custom Traffic Simulation")
        custom_traffic = st.number_input("Custom Expected Daily Users", min_value=1, max_value=100000, value=400, step=50)
        custom_days = math.ceil(remaining_users / custom_traffic)
        c1, c2 = st.columns(2)
        c1.metric("Estimated Days Remaining", custom_days)
        c2.metric("Estimated Completion Date", (date.today() + timedelta(days=custom_days)).strftime("%b %d, %Y"))
        st.subheader("Traffic Sensitivity Analysis")
        traffic_variations = {"50% Lower Traffic": max(1, int(custom_traffic*.5)), "25% Lower Traffic": max(1, int(custom_traffic*.75)), "Expected Traffic": custom_traffic, "25% Higher Traffic": max(1, int(custom_traffic*1.25)), "50% Higher Traffic": max(1, int(custom_traffic*1.5))}
        traffic_sensitivity = pd.DataFrame([{"Scenario": name, "Daily Users": traffic, "Estimated Days": math.ceil(remaining_users / traffic)} for name, traffic in traffic_variations.items()])
        st.dataframe(traffic_sensitivity, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(traffic_sensitivity, x="Scenario", y="Estimated Days", text="Estimated Days", title="Impact of Traffic Changes on Experiment Duration"), use_container_width=True)
        st.subheader("Automated Traffic Insights")
        high_days = math.ceil(remaining_users / max(1, custom_traffic*1.5))
        low_days = math.ceil(remaining_users / max(1, custom_traffic*.5))
        st.write(f"At {custom_traffic:,} users per day, approximately {custom_days} days remain.")
        st.success(f"50% higher traffic could save approximately {custom_days-high_days} days.")
        st.warning(f"50% lower traffic could increase the estimate to approximately {low_days} days.")
        st.caption("Forecasts are illustrative and assume constant traffic and eligibility.")

with tab5:
    st.header("Executive Experiment Summary")
    st.write("Evaluate whether Group B improves user conversion compared with Group A.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Observed Uplift", f"{absolute_uplift:+.2f} pp")
    c2.metric("P-Value", f"{p_value:.4f}")
    c3.metric("Experiment Status", "Statistically Significant" if p_value < alpha else "Inconclusive")
    st.subheader("Key Findings")
    st.write(f"Group B conversion: {rate_b:.2%}; Group A conversion: {rate_a:.2%}; relative uplift: {relative_uplift:+.2f}%" if np.isfinite(relative_uplift) else f"Group B conversion: {rate_b:.2%}; Group A conversion: {rate_a:.2%}. Relative uplift is undefined when Group A has zero conversions.")
    st.write(f"Two-sided significance test at α={alpha:.0%}: {'significant' if p_value < alpha else 'not significant'}.")
    st.subheader("Business Recommendation")
    (st.success if decision == "Consider Launching Group B" else st.warning)(decision)
    st.write("Review allocation, data quality, experiment timing and business guardrails before rollout.")
    st.caption("This is a decision-support prototype, not an automated launch authorization. Sample-size targets depend on the assumptions in the sidebar.")
    st.subheader("Download Experiment Report")
    report_df = pd.DataFrame({"Metric": ["Total Users", "Group A Conversion Rate (%)", "Group B Conversion Rate (%)", "Absolute Uplift (pp)", "Relative Uplift (%)", "P-Value", "Significance Level", "Experiment Status"], "Value": [current_users, round(rate_a*100, 2), round(rate_b*100, 2), round(absolute_uplift, 2), round(relative_uplift, 2) if np.isfinite(relative_uplift) else "N/A", round(p_value, 6), alpha, decision]})
    st.download_button("Download Experiment Report (CSV)", report_df.to_csv(index=False), file_name="ab_test_experiment_report.csv", mime="text/csv")
    st.divider()
    st.header("Experiment Decision Summary")
    st.info(f"Readiness: {decision}." + (f" {remaining_users:,} additional users estimated." if remaining_users is not None else ""))
    st.subheader("Recommended Next Actions")
    if not allocation_healthy:
        st.error("Investigate sample ratio mismatch before making a rollout decision.")
    elif not sample_size_healthy:
        st.warning("Sample size target has not been reached. Follow the predefined experiment plan.")
    elif p_value < alpha and uplift > 0:
        st.success("Evaluate business impact and guardrails before considering Group B rollout.")
    else:
        st.warning("Current evidence does not support launching Group B.")
    st.header("Experiment Guardrail Monitoring")
    st.caption("These are allocation and conversion checks, not a substitute for independent product guardrail metrics.")
    guardrail_df = metrics.reset_index().rename(columns={"total_users": "users", "total_conversions": "conversions"})
    guardrail_df["conversion_rate"] *= 100
    st.dataframe(guardrail_df, use_container_width=True, hide_index=True)
    fig = px.bar(guardrail_df, x="experiment_group", y="conversion_rate", color="experiment_group", text="conversion_rate", title="Conversion Rate by Experiment Group")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(showlegend=False, yaxis_title="Conversion Rate (%)")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Automated Conversion Monitoring")
    if uplift > 0:
        st.success(f"Group B conversion is {absolute_uplift:.2f} percentage points higher than Group A.")
    elif uplift < 0:
        st.warning(f"Group B conversion is {abs(absolute_uplift):.2f} percentage points lower than Group A.")
    else:
        st.info("Both groups have identical observed conversion rates.")
    st.info(f"Observed difference is {'statistically significant' if p_value < alpha else 'not statistically significant'} (p={p_value:.4f}, α={alpha:.0%}).")
