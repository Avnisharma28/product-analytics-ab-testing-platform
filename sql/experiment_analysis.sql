
-- Calculate A/B test performance for each group

SELECT
    experiment_group,
    COUNT(*) AS total_users,
    SUM(converted) AS total_conversions,
    ROUND(AVG(converted) * 100, 2) AS conversion_rate

FROM read_csv_auto('data/ab_test_users.csv')

GROUP BY experiment_group

ORDER BY experiment_group;


-- Step 1: Calculate conversion rates for each group
WITH group_metrics AS (
    SELECT
        experiment_group,
        COUNT(*) AS total_users,
        SUM(converted) AS total_conversions,
        AVG(converted) AS conversion_rate
    FROM read_csv_auto('data/ab_test_users.csv')
    GROUP BY experiment_group
)

-- Step 2: Compare Group B against Group A
SELECT
    ROUND(a.conversion_rate * 100, 2) AS group_a_rate,
    ROUND(b.conversion_rate * 100, 2) AS group_b_rate,

    ROUND(
        (b.conversion_rate - a.conversion_rate) * 100, 2
    ) AS absolute_uplift_pp,

    ROUND(
        (b.conversion_rate - a.conversion_rate)
        / NULLIF(a.conversion_rate, 0) * 100, 2
    ) AS relative_uplift_pct

FROM group_metrics a
CROSS JOIN group_metrics b
WHERE a.experiment_group = 'A'
  AND b.experiment_group = 'B';
