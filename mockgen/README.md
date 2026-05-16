# mockgen

Mock data generator for the travel demo. Seeds the SQLite databases consumed by `sam-sql-database`-backed agents (Weather, Itinerary) and the JSON file consumed by the Python `lookup_flight` tool.

## Layout

- `generate.py` — CLI entrypoint with subcommands: `all`, `weather`, `itinerary`, `flights`.
- `seeds/` — input YAML defining the demo storyline (cities, flights, itinerary days, weather profiles). Edit these to tweak the narrative without touching code.
- Default output paths land inside `../sam-project/db/` and `../sam-project/mock/`. Override with `--output-dir`.

## Usage

From this directory:

```shell
uv run python generate.py all
uv run python generate.py weather --output-db ../sam-project/db/weather.db
uv run python generate.py itinerary --output-db ../sam-project/db/itinerary.db
uv run python generate.py flights --output-json ../sam-project/mock/flights.json
```
