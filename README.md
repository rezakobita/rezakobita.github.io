# রেজার কবিতা

The poetry website of **মোঃ রেজাউল করিম (রেজা)**, published at
**https://rezakobita.github.io**.

Each poem is a small text file in the `poems/` folder. When you add or
change a file on GitHub, the site rebuilds itself and updates in about a minute.

---

## ✍️ Adding a new poem (works from a phone too)

1. Open the repository on GitHub and go into the **`poems`** folder.
2. Click **Add file → Create new file**.
3. Name the file in **English letters**, ending in `.txt`, for example `notun-bhor.txt`.
   This name becomes the web address: `rezakobita.github.io/kobita/notun-bhor/`.
4. Paste this at the top, then the poem:

```
---
title: নতুন ভোর
section: prokriti
date: ১৩/১১/২০২৬
---
প্রথম লাইন
দ্বিতীয় লাইন
তৃতীয় লাইন
চতুর্থ লাইন

পরের স্তবক…
```

5. Click **Commit changes**. That's it. Check the site after a minute or two.

**Stanzas:** leave **one empty line** between stanzas. The lines appear exactly as written.

### The lines at the top

| Line | Required? | What it does |
|---|---|---|
| `title:` | yes | The poem's name |
| `section:` | yes | Which section it goes in (codes below) |
| `date:` | no | When it was written, e.g. `১৪/০৫/২০২৪` or `14/05/2024`. Dated poems appear under "নতুন কবিতা" on the home page, newest first |
| `place:` | no | Where it was written, e.g. `ঢাকা` |
| `dedication:` | no | A line shown above the poem, e.g. `শুভ জন্মদিন দাদাভাই` |
| `signoff:` | no | A line shown below the poem, e.g. `রেজা দাদা` |
| `hidden: yes` | no | Keeps the poem off the website (see below) |

### Section codes

| Code | Section |
|---|---|
| `gram` | গ্রাম ও স্মৃতি |
| `shishu` | শিশুতোষ ছড়া |
| `prokriti` | প্রকৃতি ও ঋতু |
| `prem` | প্রেম ও বিরহ |
| `hasya` | হাস্যরস |
| `shomaj` | ব্যঙ্গ ও সমাজ |
| `poribar` | পরিবার ও উৎসব |
| `jibon` | জীবন ও দর্শন |
| `desh` | দেশ ও রাজনীতি |

Section names and descriptions can be changed in `site.json`. A section only
appears on the site once it has at least one visible poem.

---

## 🙈 Hidden poems (political & religious)

The poems in **`poems/on-hold/`** each have `hidden: yes` at the top, so they
are **not** on the website.

- **To publish one:** open the file, click the ✏️ pencil, delete the line
  `hidden: yes`, and commit.
- **To hide any poem:** add the line `hidden: yes` at the top (between the `---` lines).

The folder is only for keeping them together; moving a file doesn't change anything.

---

## ✏️ Editing or removing

- **Fix a poem:** open its file → ✏️ → edit → Commit.
- **Remove a poem:** open it → `⋯` menu → **Delete file**, or just add `hidden: yes`.
- **About the poet page:** edit `about.txt`. Empty lines start new paragraphs.
- **Photo:** upload a square-ish photo named `kobi.jpg` to the main folder.

---

## ⚙️ One-time setup (already done once, kept for reference)

1. Push this folder to `rezakobita/rezakobita.github.io`.
2. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Open the **Actions** tab and wait for "Publish site" to turn green.

If a build ever fails (red ✗ in the Actions tab), the usual cause is a missing
`---` line at the top of a poem file. The previous version of the site stays online.

### Technical notes

- `build.py` turns `poems/*.txt` into the website in `_site/`. It needs only Python 3, with no packages to install.
- Run `python3 build.py` locally, then open `_site/index.html` through any local web server to preview.
- `theme/` holds the stylesheet, scripts and fonts (Galada, Tiro Bangla and Anek Bangla, all under the SIL Open Font License).
- Files in `poems/` starting with `_` (like `_template.txt`) are ignored.
