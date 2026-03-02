# 🚀 VNR Vanguard: Results Engine

**VNR Vanguard** is a high-performance academic analytics suite built for students of VNRVJIET. It transforms the raw, static data from the college results portal into a dynamic, searchable, and insightful leaderboard with real-time analytics.

## 🌟 Key Features

* **⚡ High-Speed Scraping:** Utilizes `ThreadPoolExecutor` (Multi-threading) to fetch and parse an entire section's results (60+ students) in under 20 seconds.
* **🏆 Subject Topper Sorting:** A custom-built sorting engine that allows users to re-rank the leaderboard based on performance in a specific subject.
* **📊 Class Analytics:** Deep-dive statistics page featuring grade distribution (O through F) and subject-wise pass/fail percentages.
* **💎 Premium UI:** A modern dark-mode interface built with "Plus Jakarta Sans," featuring Neon Blue accents, hover effects, and 🏆 icons for perfect scores.
* **💾 Smart Caching:** MD5-hashed FileSystem caching persists results for 24 hours, significantly reducing redundant load on college servers.
* **🛡️ Production-Grade Security:** Integrated **Rate Limiting** to prevent IP blacklisting and a password-protected admin dashboard for cache management.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+ / Flask
* **Scraping:** BeautifulSoup4 / Requests / Concurrency
* **Frontend:** HTML5 / CSS3 (Grid & Flexbox) / JavaScript (ES6+)
* **Caching:** Flask-Caching (FileSystem)
* **Security:** Flask-Limiter
* **Deployment:** Render / Gunicorn

---

## 📂 Project Structure

```text
/vnr-vanguard
├── app/                   # Root application directory
│   ├── app.py             # App Factory, Configuration & Rate Limiting
│   ├── scraper/           # Multi-threaded scraping engine & utils
│   ├── routes/            # Blueprint routing & Analytics logic
│   ├── templates/         # Jinja2 HTML templates
│   └── flask_cache/       # Persistent serialized data
├── Procfile               # Deployment instructions for Render
└── requirements.txt       # Production dependencies
```

---

## 🚀 Deployment Guide (Render)

### 1. Repository Setup
Push the code to GitHub. Ensure `flask_cache/`, `logs/`, and `.env` are added to your `.gitignore` to keep student data and your secret keys private.

### 2. Render Settings
1. Create a new **Web Service** on Render and connect your repository.
2. Configure the build environment:
   * **Root Directory:** *(Leave blank)*
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r app/requirements.txt`
   * **Start Command:** `gunicorn --chdir app app:app`

### 3. Environment Variables
Add the following in the **Environment** tab on Render:
* `MY_SECRET_KEY`: Your admin password for cache flushing (used in `/status` and `/refresh`).
* `YEAR_PREFIX`: The default batch year (e.g., `23`).

---

## 🛡️ Security & Ethics

This project is built with a strict **"Respect the Portal"** philosophy:
1. **Rate Limiting:** Users are strictly limited to 5 scrape requests per minute to prevent overwhelming the college network.
2. **On-Demand Scraping:** The application only fetches data when explicitly requested by a user; no background "crawling" or mass data harvesting occurs.
3. **Anonymity:** No personal credentials (passwords) are collected, requested, or stored by the application.

---

## 📈 System Monitoring

The engine includes a `/status` dashboard to track system health:
* **Cache Hits:** Requests served instantly from existing disk data.
* **Cache Scrapes:** Fresh fetches triggered from the college portal.
* **Disk Health:** Monitoring the number of unique cached batches currently stored on the server.

---

**Developed with 💻 by Anurag Kosuri** *Computer Science & Business Systems, VNRVJIET*