# Unfollows

![tests](https://github.com/aastiksharma07/unfollows/actions/workflows/tests.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

A small Python tool that finds the Instagram accounts you follow that don’t follow you back, using the JSON files from Instagram’s official data export. No login, no scraping, no API keys.

**Web version:** https://unfollows.aastikz.me (source on the [`web`](../../tree/web) branch)

## Features

- Reads both the old and new Instagram export formats
- Handles split exports (`followers_1.json`, `followers_2.json`, …)
- Case-insensitive, de-duplicated comparison
- Sort by newest, oldest, or A–Z
- Plain-text or `--json` output
- Standard library only, with type hints and unit tests

## Usage

Requires Python 3.9+.

```bash
python unfollows.py followers_1.json following.json
```

```
Following 5 · Followers 3 · Don't follow back 3

@coffee.daily  09 Mar 2024  https://www.instagram.com/coffee.daily/
@mira.designs  11 Jan 2024  https://www.instagram.com/mira.designs/
@nasa          14 Aug 2023  https://www.instagram.com/nasa/
```

| Option | Description |
| --- | --- |
| `--sort recent\|oldest\|az` | Order of results (default `recent`) |
| `--json` | Print machine-readable JSON |

Files are recognised by name, so any number of `followers*.json` and `following*.json` files can be passed in any order.

### Install as a command

```bash
pip install .
unfollows followers_1.json following.json --sort az
```

### Use as a library

```python
import json
from unfollows import compare

followers = json.load(open("followers_1.json"))
following = json.load(open("following.json"))

result = compare([followers], [following], sort="az")
print(result["not_following_back"])
```

Try it with the files in [`sample/`](sample/).

## Getting your Instagram data

1. Go to **Accounts Center → Your information and permissions → Download your information**.
2. Choose **Some of your information → Followers and following**.
3. Pick **Download to device**, format **JSON**, date range **All time**.
4. Unzip it. The files are in `connections/followers_and_following/`.

## How it works

`unfollows.py` is organised as small, testable functions:

- `extract_accounts()` normalises each export record into an `Account(username, timestamp)`. Newer exports keep the username in `title`, older ones in `string_list_data[].value`, and the profile `href` is the fallback.
- `not_following_back()` does a set difference keyed on the lower-cased username, keeping follow order and removing duplicates.
- `sort_accounts()` and `compare()` sort the result and return a summary.
- `main()` is the `argparse` CLI.

## Tests

```bash
python -m unittest discover -s tests -v
```

They run on every push via GitHub Actions on Python 3.9 and 3.12.

## Project structure

```
unfollows.py          core logic + CLI
tests/                unit tests
sample/               example export files
pyproject.toml        packaging (`unfollows` console script)
.github/workflows/    CI
```

## Privacy

Everything runs locally. Your export files are never sent anywhere.

## Disclaimer

Not affiliated with, endorsed by, or connected to Instagram or Meta.

## License

[MIT](LICENSE)
