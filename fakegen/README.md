# fakegen

Faker + YAML driven mock data generator. SQLAlchemy under the hood so SQLite today, PostgreSQL whenever.

## Install

```shell
cd fakegen
uv sync
```

## Generate

```shell
uv run python main.py generate \
  --db-config configs/weather.db.yaml \
  --schema configs/weather.schema.yaml
```

## Refresh

Re-materialises any `date_from_offset` column against the current date. Use this before a demo so dates stay anchored at today.

```shell
uv run python main.py refresh \
  --db-config configs/weather.db.yaml \
  --schema configs/weather.schema.yaml
```

## Config

### DB config

```yaml
url: sqlite:///../profiles/sam-project/db/weather.db
create_if_missing: true
truncate: true
```

Postgres later: `url: postgresql+psycopg://user:pass@host/db`. Install `psycopg` first.

### Schema config

Each column has a `generator` plus `args`:

- Any Faker provider method (`random_int`, `random_element`, `sentence`, `pyfloat`, `name`, ...).
- Internal: `date_from_offset` reads a sibling column and returns `date.today() + timedelta(days=value)`.
- Internal: `datetime_from_offset` reads a sibling column and returns `now() + timedelta(unit=value)` where `unit` is one of `days`, `hours`, `minutes`, `seconds` (default `hours`). Picks the granularity of the dataset.

Supported types: `integer`, `string`, `date`, `datetime`, `float`, `boolean`.

### Choosing granularity

Daily series (e.g., flight schedule):

```yaml
- {name: offset_days,    generator: random_int, args: {min: -7, max: 14}}
- {name: scheduled_date, type: date, generator: date_from_offset, args: {source: offset_days}}
```

Hourly series (e.g., weather):

```yaml
- {name: offset_hours,   generator: random_int, args: {min: -24, max: 168}}
- {name: forecast_time,  type: datetime, generator: datetime_from_offset, args: {source: offset_hours, unit: hours}}
```

Minutely (e.g., live transit ETA):

```yaml
- {name: offset_minutes, generator: random_int, args: {min: 0, max: 180}}
- {name: eta,            type: datetime, generator: datetime_from_offset, args: {source: offset_minutes, unit: minutes}}
```
