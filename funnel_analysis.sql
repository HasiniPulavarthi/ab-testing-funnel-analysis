-- ============================================================
-- funnel_analysis.sql
-- Conversion funnel + drop-off analysis, segmented by device and
-- traffic source. Written for SQLite (portable, zero-setup) --
-- syntax is standard enough to port to Postgres/BigQuery with
-- minimal changes (mainly date functions).
--
-- Assumes a table `events` loaded from data/funnel_events.csv
-- with columns: user_id, session_id, event_time, event_name,
-- device, traffic_source
-- ============================================================

-- 1. Overall funnel: users reaching each stage + stage-to-stage conversion
WITH stage_users AS (
    SELECT
        SUM(CASE WHEN event_name = 'view_product'   THEN 1 ELSE 0 END) AS viewed,
        SUM(CASE WHEN event_name = 'add_to_cart'      THEN 1 ELSE 0 END) AS carted,
        SUM(CASE WHEN event_name = 'begin_checkout'    THEN 1 ELSE 0 END) AS checked_out,
        SUM(CASE WHEN event_name = 'purchase'           THEN 1 ELSE 0 END) AS purchased
    FROM (
        SELECT DISTINCT user_id, event_name FROM events
    )
)
SELECT
    viewed,
    carted,
    checked_out,
    purchased,
    ROUND(100.0 * carted / viewed, 2)        AS view_to_cart_pct,
    ROUND(100.0 * checked_out / carted, 2)    AS cart_to_checkout_pct,
    ROUND(100.0 * purchased / checked_out, 2) AS checkout_to_purchase_pct,
    ROUND(100.0 * purchased / viewed, 2)      AS overall_conversion_pct
FROM stage_users;

-- 2. Funnel segmented by device -- this is where the finding shows up
WITH stage_users_by_device AS (
    SELECT
        device,
        SUM(CASE WHEN event_name = 'view_product'   THEN 1 ELSE 0 END) AS viewed,
        SUM(CASE WHEN event_name = 'add_to_cart'      THEN 1 ELSE 0 END) AS carted,
        SUM(CASE WHEN event_name = 'begin_checkout'    THEN 1 ELSE 0 END) AS checked_out,
        SUM(CASE WHEN event_name = 'purchase'           THEN 1 ELSE 0 END) AS purchased
    FROM (SELECT DISTINCT user_id, event_name, device FROM events)
    GROUP BY device
)
SELECT
    device,
    viewed,
    carted,
    checked_out,
    purchased,
    ROUND(100.0 * carted / viewed, 2)        AS view_to_cart_pct,
    ROUND(100.0 * checked_out / carted, 2)    AS cart_to_checkout_pct,
    ROUND(100.0 * purchased / checked_out, 2) AS checkout_to_purchase_pct,
    ROUND(100.0 * purchased / viewed, 2)      AS overall_conversion_pct
FROM stage_users_by_device
ORDER BY overall_conversion_pct;

-- 3. Funnel segmented by traffic source
WITH stage_users_by_source AS (
    SELECT
        traffic_source,
        SUM(CASE WHEN event_name = 'view_product'   THEN 1 ELSE 0 END) AS viewed,
        SUM(CASE WHEN event_name = 'add_to_cart'      THEN 1 ELSE 0 END) AS carted,
        SUM(CASE WHEN event_name = 'begin_checkout'    THEN 1 ELSE 0 END) AS checked_out,
        SUM(CASE WHEN event_name = 'purchase'           THEN 1 ELSE 0 END) AS purchased
    FROM (SELECT DISTINCT user_id, event_name, traffic_source FROM events)
    GROUP BY traffic_source
)
SELECT
    traffic_source,
    viewed,
    purchased,
    ROUND(100.0 * purchased / viewed, 2) AS overall_conversion_pct
FROM stage_users_by_source
ORDER BY overall_conversion_pct DESC;

-- 4. Biggest single drop-off point (which stage transition loses the most
--    users, in absolute terms) -- identifies where to focus the A/B test
WITH stage_users AS (
    SELECT
        SUM(CASE WHEN event_name = 'view_product'   THEN 1 ELSE 0 END) AS viewed,
        SUM(CASE WHEN event_name = 'add_to_cart'      THEN 1 ELSE 0 END) AS carted,
        SUM(CASE WHEN event_name = 'begin_checkout'    THEN 1 ELSE 0 END) AS checked_out,
        SUM(CASE WHEN event_name = 'purchase'           THEN 1 ELSE 0 END) AS purchased
    FROM (SELECT DISTINCT user_id, event_name FROM events)
)
SELECT 'view_to_cart' AS transition, (viewed - carted) AS users_lost FROM stage_users
UNION ALL
SELECT 'cart_to_checkout', (carted - checked_out) FROM stage_users
UNION ALL
SELECT 'checkout_to_purchase', (checked_out - purchased) FROM stage_users
ORDER BY users_lost DESC;

-- 5. Daily conversion trend (to check for day-of-week effects or drift
--    before designing the test -- avoids running a test during an
--    unusually noisy period)
SELECT
    DATE(event_time) AS day,
    COUNT(DISTINCT CASE WHEN event_name = 'view_product' THEN user_id END) AS viewers,
    COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN user_id END) AS purchasers,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN user_id END)
        / COUNT(DISTINCT CASE WHEN event_name = 'view_product' THEN user_id END), 2) AS daily_conversion_pct
FROM events
GROUP BY DATE(event_time)
ORDER BY day;
