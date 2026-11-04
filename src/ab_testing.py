
from statsmodels.stats.proportion import proportions_ztest


def calculate_conversion_rate(conversions, total_users):
    """
    Calculate conversion rate for an experiment group.
    """
    if total_users <= 0:
        raise ValueError("Total users must be greater than zero.")

    if conversions < 0 or conversions > total_users:
        raise ValueError("Invalid number of conversions.")

    return conversions / total_users


def calculate_uplift(control_rate, treatment_rate):
    """
    Calculate relative uplift between treatment and control.
    """
    if control_rate == 0:
        return float("nan")

    return (treatment_rate - control_rate) / control_rate


def calculate_p_value(conversions_a, users_a, conversions_b, users_b):
    """
    Calculate the two-sided p-value for an A/B experiment.
    """
    if users_a <= 0 or users_b <= 0:
        raise ValueError("Both groups must contain users.")

    if not (0 <= conversions_a <= users_a):
        raise ValueError("Invalid conversions for Group A.")

    if not (0 <= conversions_b <= users_b):
        raise ValueError("Invalid conversions for Group B.")

    counts = [conversions_a, conversions_b]
    sample_sizes = [users_a, users_b]

    if sum(counts) in (0, sum(sample_sizes)):
        return 1.0

    _, p_value = proportions_ztest(
        counts,
        sample_sizes,
        alternative="two-sided"
    )

    return float(p_value)

from statsmodels.stats.proportion import confint_proportions_2indep


def calculate_confidence_interval(
    conversions_a,
    users_a,
    conversions_b,
    users_b,
    alpha=0.05
):
    """
    Calculate a confidence interval for the difference
    between Group B and Group A conversion rates.
    """
    if users_a <= 0 or users_b <= 0:
        raise ValueError("Both groups must contain users.")

    if not (0 <= conversions_a <= users_a):
        raise ValueError("Invalid conversions for Group A.")

    if not (0 <= conversions_b <= users_b):
        raise ValueError("Invalid conversions for Group B.")

    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")

    lower, upper = confint_proportions_2indep(
        count1=conversions_b,
        nobs1=users_b,
        count2=conversions_a,
        nobs2=users_a,
        compare="diff",
        method="newcomb",
        alpha=alpha
    )

    return float(lower), float(upper)

from scipy.stats import chisquare


def calculate_srm_p_value(users_a, users_b):
    """
    Test whether users follow an expected 50/50 allocation.
    """
    if users_a < 0 or users_b < 0:
        raise ValueError("User counts cannot be negative.")

    total_users = users_a + users_b

    if total_users == 0:
        raise ValueError("At least one user is required.")

    expected = [total_users / 2, total_users / 2]

    _, p_value = chisquare(
        f_obs=[users_a, users_b],
        f_exp=expected
    )

    return float(p_value)

import math

import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def calculate_sample_size(
    baseline_rate,
    target_rate,
    power=0.80,
    alpha=0.05
):
    """
    Calculate required sample size per experiment group.
    Rates must be proportions between 0 and 1.
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("Baseline rate must be between 0 and 1.")

    if not (0 < target_rate < 1):
        raise ValueError("Target rate must be between 0 and 1.")

    if baseline_rate == target_rate:
        raise ValueError("Baseline and target rates must differ.")

    if not (0 < power < 1 and 0 < alpha < 1):
        raise ValueError("Power and alpha must be between 0 and 1.")

    effect_size = abs(
        proportion_effectsize(baseline_rate, target_rate)
    )

    analysis = NormalIndPower()

    result = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative="two-sided"
    )

    if not np.isfinite(result) or result <= 0:
        raise ValueError("Unable to calculate a valid sample size.")

    return math.ceil(result)
