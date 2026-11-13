/* Unfollows — compares Instagram followers/following exports, fully client-side. */
(function () {
    'use strict';

    const $ = (id) => document.getElementById(id);

    /* ---------- Parsing ---------- */

    // Pull a username out of an Instagram profile URL.
    function userFromHref(href) {
        if (!href) return '';
        const m = String(href).match(/instagram\.com\/(?:_u\/)?([^/?#]+)/i);
        return m ? decodeURIComponent(m[1]) : '';
    }

    // Instagram has shipped a few export shapes over the years:
    //   followers_1.json -> [ { string_list_data: [{ href, value, timestamp }] } ]
    //   following.json   -> { relationships_following: [ { title, string_list_data: [{ href, timestamp }] } ] }
    // Newer exports put the username in `title` and drop `value`. Handle all of them.
    // (Mirrors extract_accounts() in unfollows.py on the main branch.)
    function extractEntries(json) {
        let items = [];
        if (Array.isArray(json)) {
            items = json;
        } else if (json && typeof json === 'object') {
            for (const key of Object.keys(json)) {
                if (Array.isArray(json[key])) items = items.concat(json[key]);
            }
        }

        const out = [];
        for (const item of items) {
            if (!item || typeof item !== 'object') continue;
            const data = Array.isArray(item.string_list_data) ? item.string_list_data : [];
            const first = data[0] || {};
            const username = (first.value || item.title || userFromHref(first.href) || '').trim();
            if (!username) continue;
            out.push({ username, timestamp: Number(first.timestamp) || 0 });
        }
        return out;
    }

    function readJson(file) {
        return file.text().then((text) => {
            try {
                return JSON.parse(text);
            } catch (e) {
                throw new Error(`“${file.name}” isn’t valid JSON.`);
            }
        });
    }

    async function readAll(files) {
        const lists = await Promise.all([...files].map(readJson));
        return lists.flatMap(extractEntries);
    }

    /* ---------- Comparison ---------- */

    // People in `following` whose username isn't in `followers`.
    function notFollowingBack(followers, following) {
        const set = new Set(followers.map((f) => f.username.toLowerCase()));
        const seen = new Set();
        const out = [];
        for (const f of following) {
            const key = f.username.toLowerCase();
            if (set.has(key) || seen.has(key)) continue;
            seen.add(key);
            out.push(f);
        }
        return out;
    }


    /* ---------- State ---------- */

    const state = {
        files: { followers: null, following: null },
        ghosts: [],
        done: loadDone(),
    };

    function loadDone() {
        try { return new Set(JSON.parse(localStorage.getItem('done') || '[]')); }
        catch (e) { return new Set(); }
    }

    function saveDone() {
        try { localStorage.setItem('done', JSON.stringify([...state.done])); } catch (e) {}
    }

    /* ---------- Upload UI ---------- */

    const zones = {
        followers: { el: $('dropFollowers'), input: $('followersFile') },
        following: { el: $('dropFollowing'), input: $('followingFile') },
    };

    function setFiles(kind, files) {
        const list = files && files.length ? [...files] : null;
        state.files[kind] = list;
        const { el } = zones[kind];
        const small = el.querySelector('small');
        el.classList.toggle('ready', !!list);
        el.querySelector('use').setAttribute('href', list ? '#i-check' : '#i-file');
        small.textContent = list ? list.map((f) => f.name).join(', ') : small.dataset.default;
        $('compareBtn').disabled = !(state.files.followers && state.files.following);
        showError('');
    }

    // Dropping a single file on the wrong box is common; guess by name.
    function routeByName(files) {
        for (const f of files) {
            const n = f.name.toLowerCase();
            if (n.startsWith('following')) setFiles('following', [f]);
            else if (n.startsWith('followers')) setFiles('followers', [f]);
        }
    }

    for (const [kind, { el, input }] of Object.entries(zones)) {
        input.addEventListener('change', () => setFiles(kind, input.files));

        el.addEventListener('dragover', (e) => { e.preventDefault(); el.classList.add('over'); });
        el.addEventListener('dragleave', () => el.classList.remove('over'));
        el.addEventListener('drop', (e) => {
            e.preventDefault();
            el.classList.remove('over');
            const files = [...e.dataTransfer.files];
            const named = files.some((f) => /^follow(ers|ing)/i.test(f.name));
            if (files.length > 1 && named) routeByName(files);
            else setFiles(kind, files);
        });
    }

    function showError(msg) {
        const el = $('error');
        el.textContent = msg;
        el.hidden = !msg;
    }

    /* ---------- Results UI ---------- */

    const fmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });

    function profileUrl(username) {
        return 'https://www.instagram.com/' + encodeURIComponent(username) + '/';
    }

    function sorted(list) {
        const mode = $('sort').value;
        const copy = list.slice();
        if (mode === 'az') copy.sort((a, b) => a.username.localeCompare(b.username));
        else if (mode === 'oldest') copy.sort((a, b) => a.timestamp - b.timestamp);
        else copy.sort((a, b) => b.timestamp - a.timestamp);
        return copy;
    }

    // Profile picture via unavatar.io (free, open source, no key). Falls back to
    // the first letter if it can't be fetched — Instagram often blocks lookups.
    function avatar(username) {
        const wrap = document.createElement('span');
        wrap.className = 'avatar';
        const letter = document.createElement('span');
        letter.textContent = username.replace(/[^a-z0-9]/gi, '').charAt(0) || '@';
        wrap.append(letter);

        const img = document.createElement('img');
        img.alt = '';
        img.loading = 'lazy';
        img.decoding = 'async';
        img.referrerPolicy = 'no-referrer';
        img.src = 'https://unavatar.io/instagram/' + encodeURIComponent(username) + '?fallback=false';
        img.addEventListener('load', () => img.classList.add('loaded'));
        img.addEventListener('error', () => img.remove());
        wrap.append(img);
        return wrap;
    }

    function row(person) {
        const li = document.createElement('li');
        li.className = 'person' + (state.done.has(person.username) ? ' done' : '');

        li.append(avatar(person.username));

        const who = document.createElement('div');
        who.className = 'who';
        const name = document.createElement('a');
        name.href = profileUrl(person.username);
        name.target = '_blank';
        name.rel = 'noopener noreferrer';
        name.textContent = '@' + person.username;
        who.append(name);
        if (person.timestamp) {
            const since = document.createElement('small');
            since.textContent = 'Followed ' + fmt.format(new Date(person.timestamp * 1000));
            who.append(since);
        }

        const btn = document.createElement('a');
        btn.className = 'btn sm';
        btn.href = profileUrl(person.username);
        btn.target = '_blank';
        btn.rel = 'noopener noreferrer';
        btn.textContent = 'Unfollow';
        btn.setAttribute('aria-label', 'Open @' + person.username + ' on Instagram to unfollow');
        btn.addEventListener('click', () => {
            state.done.add(person.username);
            saveDone();
            li.classList.add('done');
        });

        li.append(who, btn);
        return li;
    }

    function render() {
        const q = $('search').value.trim().replace(/^@/, '').toLowerCase();
        const items = sorted(state.ghosts).filter((p) => p.username.toLowerCase().includes(q));
        const list = $('list');
        list.replaceChildren(...items.map(row));
        if (!items.length) {
            const li = document.createElement('li');
            li.className = 'empty';
            li.textContent = state.ghosts.length ? 'No matches.' : 'Everyone you follow follows you back. 🎉';
            list.append(li);
        }
    }

    $('search').addEventListener('input', render);
    $('sort').addEventListener('change', render);

    /* ---------- Flow ---------- */

    $('form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = $('compareBtn');
        btn.disabled = true;
        btn.textContent = 'Comparing…';
        try {
            const [followers, following] = await Promise.all([
                readAll(state.files.followers),
                readAll(state.files.following),
            ]);
            if (!followers.length) throw new Error('No followers found — is that the right file?');
            if (!following.length) throw new Error('No following found — is that the right file?');

            state.ghosts = notFollowingBack(followers, following);
            $('nFollowers').textContent = new Set(followers.map((f) => f.username.toLowerCase())).size;
            $('nFollowing').textContent = new Set(following.map((f) => f.username.toLowerCase())).size;
            $('nGhosts').textContent = state.ghosts.length;

            render();
            $('intro').hidden = true;
            $('result').hidden = false;
            window.scrollTo({ top: 0 });
        } catch (err) {
            showError(err.message || 'Something went wrong reading those files.');
        } finally {
            btn.textContent = 'Compare';
            btn.disabled = !(state.files.followers && state.files.following);
        }
    });

    $('resetBtn').addEventListener('click', () => {
        for (const [kind, { input }] of Object.entries(zones)) {
            input.value = '';
            setFiles(kind, null);
        }
        $('search').value = '';
        state.ghosts = [];
        $('result').hidden = true;
        $('intro').hidden = false;
    });

    /* ---------- Theme ---------- */

    const meta = document.querySelector('meta[name="theme-color"]');
    function applyTheme(t) {
        document.documentElement.dataset.theme = t;
        meta.content = t === 'dark' ? '#0e1013' : '#f5f6f8';
    }
    applyTheme(document.documentElement.dataset.theme);

    $('themeBtn').addEventListener('click', () => {
        const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        try { localStorage.setItem('theme', next); } catch (e) {}
    });
})();
