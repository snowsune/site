# ❄️ https://snowsune.net

Welcome to **Snowsune.net**, my little website where I post personal projects, 
character data, tools, blog posts, stuff and things!

While this site isn't intended to be forked and turned into a plug-and-play template, 
the code is completely open and reviewable. If you have ideas, find a bug, or just 
want to say hi, I warmly welcome issues and suggestions! 🩵

---

## 🧭 Project Overview

Everything is written in Python and powered by Django, the website is structured with **apps** for 
content categories and i try to be as **modular** as possible. Here's how things are organized:

### 📁 `apps/`
Houses all feature-specific Django apps:

- `blog/` — Blog landing page and future dynamic markdown-powered post system. (WIP!)
- `characters/` — Static character profiles stored as `.md` files and rendered with markdown. (WIP also!)
- `comics/` — Placeholder for comic content.
  
Each app contains its own:
- `templates/` — App-specific templates.
- `static/` — App-specific images or media.
- `urls.py` and `views.py`

### 📁 `snowsune/`
The main Django project config:
- `urls.py` — Routes root paths and includes app URLs.
- `views/` — Generic page views like Home, Tools, etc.
- `templates/` — Shared templates like `base.html`, `404.html`, and errors.
- `context_processors.py` — Injects useful data (like debug state, version info) into templates.
- `settings.py`, `wsgi.py`, `asgi.py` — Standard config.

### 📁 `static/`
Global static assets:
- `css/` — Site-wide styles (mainly `base.css`)
- `background/` — Tiled retro backgrounds
- `logos/` — Logo variants and .kra source files
- `stickers/` — Error page art
- `fonts/`, `placeholders/`, `favicon.ico`

---

## 🐳 Docker Hosting

I use Docker Compose for local development (and deployment). Here’s a minimal setup:

```yaml
services:
  db:
    image: postgres:15
    ...

  snowsunenet:
    depends_on:
      db:
        condition: service_healthy
    image: ghcr.io/snowsune/snowsunenet:latest
    environment:
      DATABASE_URL: postgres://<user>:<password>@db:5432/<dbname>
    ...
```
