
# Product Analytics & A/B Testing Platform

An end-to-end product analytics and experimentation platform built using Python, SQL, statistical hypothesis testing, and Streamlit.

## Project Overview

This project demonstrates how product analytics teams evaluate experiments, measure conversion performance, assess statistical significance, and make data-driven product decisions.

The platform provides an interactive dashboard for analyzing A/B tests and monitoring experiment health.

## Key Features

- A/B test performance analysis for control and treatment groups
- Conversion rate comparison and uplift measurement
- Statistical significance testing using two-proportion z-tests
- Confidence interval visualization
- Statistical power and sample size estimation
- Interactive experiment planning
- Sample size sensitivity analysis
- Experiment data quality validation
- Experiment health monitoring
- Executive experiment summaries and downloadable reports

## Technology Stack

- **Python:** Data processing and statistical analysis
- **Pandas & NumPy:** Data manipulation
- **SciPy & Statsmodels:** Statistical testing and power analysis
- **Streamlit:** Interactive dashboard
- **Plotly:** Data visualization
- **SQL:** Experiment data analysis

## Dashboard Sections

### 1. Experiment Overview
Displays experiment participation, conversion performance, and key metrics.

### 2. A/B Test Analysis
Evaluates conversion uplift, statistical significance, confidence intervals, and sample size requirements.

### 3. Data Quality
Validates experiment datasets and identifies potential data quality issues.

### 4. Experiment Monitoring
Tracks experiment health, allocation, and statistical readiness.

### 5. Decision Intelligence
Summarizes experiment outcomes and provides decision-support information.

## Project Structure

```text
product-analytics-ab-testing-platform/
├── dashboard/
│   └── app_fixed.py
├── data/
│   └── ab_test_users.csv
├── sql/
│   └── experiment_analysis.sql
├── src/
│   ├── generate_data.py
│   └── run_sql.py
├── notebooks/
├── reports/
├── tests/
├── requirements.txt
└── README.md
```

## Running the Application

1. Clone the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the Streamlit dashboard:

```bash
python -m streamlit run dashboard/app_fixed.py
```

## Experiment Methodology

The platform compares control group A with treatment group B to estimate changes in user conversion.

Statistical analysis includes:

- Absolute and relative conversion uplift
- Two-sided hypothesis testing
- P-value interpretation
- 95% confidence intervals at the default significance level
- Statistical power and sample size calculations

Experiment results are evaluated alongside data quality and sample size requirements before making rollout decisions.

## Future Improvements

- Integration with production data warehouses
- Automated experiment monitoring
- Multiple experiment support
- Sequential testing capabilities
- Automated reporting pipelines

## Project Purpose

Built as a portfolio project to demonstrate practical skills in product analytics, experimentation, statistical analysis, Python, SQL, and data visualization.
