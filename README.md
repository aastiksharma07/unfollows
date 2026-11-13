# Unfollows

See who you follow on Instagram that doesn’t follow you back.

**Live:** https://unfollows.aastikz.me

![tests](https://github.com/aastiksharma07/unfollows/actions/workflows/tests.yml/badge.svg)

A tiny, private Python project with a web front end. Upload the `followers` and `following` JSON files from your Instagram data export and get a clean list of accounts that don’t follow you back, each with a button that opens their profile so you can unfollow.

## How it works

All the logic is in **[`unfollows.py`](unfollows.py)**, a standard-library-only Python module that:

1. parses Instagram’s export files (it handles both the old and new JSON layouts),
2. works out who is in *following* but not in *followers* (case-insensitive, de-duplicated),
3. sorts the result.

That one file runs in two places:

- **In the browser**, through [Pyodide](https://pyodide.org) (Python compiled to WebAssembly). `app.js` only handles the UI. It hands the uploaded files to `unfollows.compare_json()` and renders what comes back. Pyodide is about 6 MB and the browser caches it after the first visit.
- **On the command line**, as a normal Python script.

## Privacy

Everything runs in your browser, Python included. There’s no server, no login, no tracking, and your files never leave your device.

The one exception is profile pictures: for each account in the result list, the username is sent to [unavatar.io](https://unavatar.io) (a free, open-source avatar service) to fetch the picture. If a picture can’t be loaded, a letter avatar is shown instead. It doesn’t touch your Instagram account. The **Unfollow** button just opens the person’s profile, and you unfollow them yourself.

## How to use

1. **Get your data from Instagram**
   - Go to **Accounts Center → Your information and permissions → Download your information**.
   - Choose **Some of your information → Followers and following**.
   - Pick **Download to device**, format **JSON**, date range **All time**.
2. **Unzip** the download and open `connections/followers_and_following/`.
3. **Open** [unfollows.aastikz.me](https://unfollows.aastikz.me) and upload:
   - `followers_1.json` (plus `followers_2.json`, … if you have several; you can select them all at once)
   - `following.json`
4. Press **Compare**.

No export handy? Try the files in [`sample/`](sample/).

## Features

- Works with both old and new Instagram export formats
- Profile pictures via [unavatar.io](https://unavatar.io), no API key needed
- Search, and sort by newest, oldest, or A–Z
- Remembers which profiles you’ve already opened
- Light and dark theme
- No build step, and no Python dependencies

## Command line

Requires Python 3.9+, with no dependencies.

```bash
python unfollows.py followers_1.json following.json
```

```
Following 5 · Followers 3 · Don't follow back 3

@coffee.daily  09 Mar 2024  https://www.instagram.com/coffee.daily/
@mira.designs  11 Jan 2024  https://www.instagram.com/mira.designs/
@nasa          14 Aug 2023  https://www.instagram.com/nasa/
```

Options: `--sort recent|oldest|az` and `--json`. Pass several `followers_*.json` files if your export is split. Or install it:

```bash
pip install .
unfollows followers_1.json following.json --sort az
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests run on every push via GitHub Actions.

## Run the web app locally

The page fetches `unfollows.py`, so serve the folder rather than opening the file directly:

```bash
python3 -m http.server 8000
```

Then visit http://localhost:8000.

## Project structure

```
unfollows.py      parsing + comparison + CLI (the core)
tests/            unit tests (unittest)
index.html        page markup
style.css         styles (light + dark)
app.js            UI; runs unfollows.py via Pyodide
pyproject.toml    packaging, `unfollows` console script
favicon.svg       icon
CNAME             custom domain for GitHub Pages
sample/           example export files
```

## Deploy

Hosted on GitHub Pages from the `main` branch root. The `CNAME` file points it at `unfollows.aastikz.me`. Add a DNS `CNAME` record for `unfollows` pointing to `<github-username>.github.io`.

## Disclaimer

Not affiliated with, endorsed by, or connected to Instagram or Meta.

## License

[MIT](LICENSE)
