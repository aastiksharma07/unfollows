# Unfollows (web)

This is the **`web`** branch: the static site served by GitHub Pages at **https://unfollows.aastikz.me**.

The Python project (`unfollows.py`, CLI, tests) is on the [`main`](../../tree/main) branch.

The site is plain HTML, CSS and JavaScript with no build step and no dependencies. Everything runs in your browser and your files are never uploaded.

```
index.html   page markup
style.css    styles (light + dark)
app.js       parsing, comparison, UI
favicon.svg  icon
CNAME        custom domain
sample/      example export files
```

Run it locally:

```bash
python3 -m http.server 8000
```

## Deploy

Settings → Pages → Source: **Deploy from a branch**, Branch: **`web`**, folder **`/ (root)`**. Add a DNS `CNAME` record for `unfollows` pointing to `aastiksharma07.github.io`.
