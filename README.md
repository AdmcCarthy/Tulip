# Tulip

A SubScout data story on the Norwegian continental shelf's remaining reserves, 1971 to today, told
through one vertical stream graph: every field's remaining volume (today's Sodir estimate walked back
through monthly production), stacked so the shelf draws a tulip bulb. Giants found early, a peak in
2000, a long drawdown, gas at the heart, and exploration still adding late (Johan Sverdrup).

Status: **first pass** (prototype page in `prototype/`, not yet a SubScout build).

```
uv sync --all-groups
uv run python scripts/fetch_sodir.py      # -> data/raw (Sodir FactPages + FactMaps)
uv run python scripts/build_data.py       # -> data/
uv run python scripts/build_prototype.py  # -> prototype/index.html
uv run pytest
```
