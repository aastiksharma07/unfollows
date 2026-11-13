# Unfollows

See who you follow on Instagram that doesn’t follow you back.

**Live:** https://unfollows.aastikz.me

A tiny, private, single-page web app. Upload the `followers` and `following` JSON files from your Instagram data export and get a clean list of accounts that don’t follow you back, each with a button that opens their profile so you can unfollow.

## Privacy

Everything runs in your browser. There’s no server, no login, no tracking, and your files never leave your device.

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
- No build step and no dependencies

## Run locally

It’s just static files, so you can open `index.html` directly, or serve the folder:

```bash
python3 -m http.server 8000
```

Then visit http://localhost:8000.

## Project structure

```
index.html   page markup
style.css    styles (light + dark)
app.js       parsing, comparison, UI
favicon.svg  icon
CNAME        custom domain for GitHub Pages
sample/      example export files
```

## Deploy

Hosted on GitHub Pages from the `main` branch root. The `CNAME` file points it at `unfollows.aastikz.me`. Add a DNS `CNAME` record for `unfollows` pointing to `<github-username>.github.io`.

## Disclaimer

Not affiliated with, endorsed by, or connected to Instagram or Meta.

## License

[MIT](LICENSE)
