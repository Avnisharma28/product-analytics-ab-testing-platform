
import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportions_ztest

# Set up a reproducible random number generator
rng = np.random.default_rng(42)

# Create 1,000 unique user IDs
user_ids = np.arange(1, 1001)

# Create a table containing those users
users_df = pd.DataFrame({
    "user_id": user_ids
})

# Display the first five rows
print(users_df.head())

# Display the total number of users
print("Total users:", len(users_df))


# Randomly assign users to Groups A or B

users_df["experiment_group"] = rng.choice(
    ["A", "B"],
    size=len(users_df),
    p=[0.5, 0.5]
)


#Display the first 10 users
print(users_df.head(10))

#count users in each experiment group
print('\nUsers per experiment group:')
print(users_df["experiment_group"].value_counts())

# Define Conversion probabilities 
conversion_rates = {
    "A": 0.10,  # 10% conversion rate for Group A
    "B": 0.13   # 13
}
#Assign each user a conversion probability
users_df["conversion_probability"] = users_df[
    "experiment_group"
    ].map(conversion_rates)

# Simulate whether each user makes a purchase
users_df["converted"] = rng.binomial(
    n=1,  # number of trials (1 for each user)
    p=users_df["conversion_probability"]  # probability of success
)

#Calculate the conversion rate for each group
print('\nConversion rates by group:')
print(users_df.groupby("experiment_group")["converted"].mean())

#calculate conversion eates for both the groups
group_rates = users_df.groupby("experiment_group")["converted"].mean()

#Extract conversion rates
rate_a = group_rates["A"]
rate_b = group_rates["B"]

#Calculate absolute difference
absolute_uplift = rate_b - rate_a

#Calculate relative difference
relative_uplift = (absolute_uplift / rate_a) * 100

#Display the results
print("\nA/B Test Results:")
print(f"Conversion Rate for Group A: {rate_a:.2%}")
print(f"Conversion Rate for Group B: {rate_b:.2%}")
print(f"Absolute Uplift: {absolute_uplift:.2%}")
print(f"Relative Uplift: {relative_uplift:.2f}%")

#Calculate how many times users converted in each group
conversions = users_df.groupby("experiment_group")["converted"].sum()

#Count total users in each group
sample_sizes = users_df["experiment_group"].value_counts()

#Perform a two proportion z test
group_order = ["A", "B"]

z_stat, p_value = proportions_ztest(
    count=conversions.reindex(group_order).values,
    nobs=sample_sizes.reindex(group_order).values
)
print("\nStatistical Significance Results:")
print(f"Z-statistic: {z_stat:.4f}")
print(f"P-value: {p_value:.4f}")

#Interpret the results
if p_value < 0.05:
    print("Result: Statistical Significant")
else:
    print("Result: Not Statistically Significant")

# Calculate the 95% confidence interval

from statsmodels.stats.proportion import confint_proportions_2indep

# Count conversions and users in Group A
conversions_a = users_df.loc[
    users_df["experiment_group"] == "A", "converted"
].sum()

users_a = (users_df["experiment_group"] == "A").sum()

# Count conversions and users in Group B
conversions_b = users_df.loc[
    users_df["experiment_group"] == "B", "converted"
].sum()

users_b = (users_df["experiment_group"] == "B").sum()

# Calculate confidence interval for B minus A
ci_lower, ci_upper = confint_proportions_2indep(
    count1=conversions_b,
    nobs1=users_b,
    count2=conversions_a,
    nobs2=users_a,
    compare="diff",
    method="newcomb",
    alpha=0.05
)

print("\n95% Confidence Interval Results:")
print(f"Lower bound: {ci_lower * 100:.2f} percentage points")
print(f"Upper bound: {ci_upper * 100:.2f} percentage points")

# Step 9: Statistical Power and Sample Size Analysis

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
import math

# Define expected conversion rates
baseline_rate = 0.11
target_rate = 0.13

# Calculate standardized effect size
effect_size = proportion_effectsize(
    baseline_rate,
    target_rate
)

# Create the power analysis model
power_analysis = NormalIndPower()

# Calculate required sample size per group
required_sample_size = power_analysis.solve_power(
    effect_size=effect_size,
    alpha=0.05,
    power=0.80,
    ratio=1.0,
    alternative="two-sided"
)

required_sample_size = math.ceil(required_sample_size)

print("\nSample Size Analysis:")
print(f"Baseline conversion rate: {baseline_rate:.2%}")
print(f"Target conversion rate: {target_rate:.2%}")
print(f"Required sample size per group: {required_sample_size:,}")
print(f"Total required users: {required_sample_size * 2:,}")

# Step 10: Save experiment data to a CSV file

users_df.to_csv(
    "data/ab_test_users.csv",
    index=False
)

print("\nExperiment data saved successfully!")
# Step 12: Validate our dataset

print("\nData Validation Results:")

# Check the number of rows and columns
print("Dataset shape:", users_df.shape)

# Check for duplicate user IDs
print("Duplicate users:", users_df["user_id"].duplicated().sum())

# Check for missing values
print("\nMissing values:")
print(users_df.isnull().sum())