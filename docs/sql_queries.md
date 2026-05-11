# SQL Queries

## Objective

Extract insights from the data warehouse.

---

## Top Destinations in term of weather forecast over a period (using pre-computed table)

```sql
SELECT  DEST.destination, DEST_SCORE.weather_rank, DEST_SCORE.avg_temp,DEST_SCORE.start_date, DEST_SCORE.end_date
FROM public.destination_weather_score_period AS DEST_SCORE
INNER JOIN public.destination AS DEST 
	ON DEST.destination_id = DEST_SCORE.destination_id
WHERE DEST_SCORE.start_date>= '2026-04-15 18:00:00+00' AND DEST_SCORE.start_date < '2026-04-15 18:01:00+00'
	AND DEST_SCORE.end_date>= '2026-04-20 15:00:00+00' AND DEST_SCORE.end_date <= '2026-04-20 15:00:01+00'
ORDER BY DEST_SCORE.weather_rank ASC
LIMIT 5;
```


## Top Destinations in term of weather forecast over a period (computing aggregates on primary dataset)

```sql
WITH w_score AS (
	SELECT 
		destination_id,
		dt,
		temp,
        CASE weather_main
            WHEN 'Clear' THEN 10
            WHEN 'Clouds' THEN 6
            WHEN 'Mist' THEN 4
            WHEN 'Snow' THEN 4
            WHEN 'Rain' THEN 4
            WHEN 'Thunderstorm' THEN 2
            ELSE 0
        END AS weather_score
	FROM public.destination_weather_forecast 
    WHERE dt >= '2026-04-15 18:00:00+00'
      AND dt <= '2026-04-20 15:00:00+00' 
	
),
dest_w_aggregations AS (
    SELECT
        destination_id,
        PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY weather_score) AS weather_median_score,
        AVG(temp) AS avg_temp
    FROM w_score
    GROUP BY destination_id
),
dest_w_rank AS (
	SELECT 
		*,
		DENSE_RANK() OVER (
			ORDER BY weather_median_score DESC, avg_temp DESC
		) AS weather_rank
	FROM dest_w_aggregations
)

SELECT DEST.destination, DEST_AGG.*
FROM dest_w_rank AS DEST_AGG 
	INNER JOIN destination AS DEST 
		ON DEST.destination_id=DEST_AGG.destination_id
ORDER BY weather_rank
LIMIT 5;
```

---

## Top Hotels per Destination

```sql
WITH TOP_DEST_WSCORE_PERIOD AS
(
	SELECT  
	 DEST.destination_id
	, DEST.destination
	, DEST_SCORE.weather_rank AS dest_weather_rank
	, DEST_SCORE.avg_temp
	, DEST_SCORE.start_date
	, DEST_SCORE.end_date
	FROM public.destination_weather_score_period AS DEST_SCORE
	INNER JOIN public.destination AS DEST 
		ON DEST.destination_id = DEST_SCORE.destination_id
	WHERE DEST_SCORE.start_date>= '2026-04-15 18:00:00+00' AND DEST_SCORE.start_date < '2026-04-15 18:01:00+00'
		AND DEST_SCORE.end_date>= '2026-04-20 15:00:00+00' AND DEST_SCORE.end_date <= '2026-04-20 15:00:01+00'
	ORDER BY DEST_SCORE.weather_rank ASC
	LIMIT 5
)
,TOP_HOTELS_DEST AS
(
	SELECT 
		HSR.destination_id,
		TOP_DEST.destination,
		TOP_DEST.dest_weather_rank,
		HSR.hotel_name,
		HSR.address,
		HSR.score as hotel_score,
		DENSE_RANK() OVER ( PARTITION BY HSR.destination_id ORDER BY HSR.score DESC) AS dest_hotel_rank
	FROM public.hotel_search_result AS HSR
	INNER JOIN public.hotel_search_param PARAM 
			ON PARAM.search_id = HSR.search_id 
	INNER JOIN TOP_DEST_WSCORE_PERIOD AS TOP_DEST
			ON TOP_DEST.destination_id= HSR.destination_id
	WHERE PARAM.checkin_date >= TOP_DEST.start_date::date
		AND PARAM.checkout_date <= TOP_DEST.end_date::date
	--HSR.score IS NOT NULL
)
SELECT * 
FROM TOP_HOTELS_DEST
WHERE dest_hotel_rank <= 5
ORDER BY dest_weather_rank ASC, dest_hotel_rank ASC;
```

---



## Concepts Used

* Window functions (DENSE_RANK)
* Percentiles (median)
* Joins and filtering
