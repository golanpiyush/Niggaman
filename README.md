# 🎮 NIGAAMAN: Game Link Finder Bot

**NIGAAMAN** is a no-BS AI-powered game link finder made by **Flywich**.  
It intelligently scrapes **FitGirl**, **DODI**, and **Game3rb** to get direct, filtered, and prioritized download links for PC games — fast and without fluff.

> 🧠 Designed to act like a smart, sharp assistant — not a moral philosopher.  
> 🛑 No annoying ethics lectures. Just links. Straight to the point.

---

## 🚀 Features

- ✅ Searches across **FitGirl**, **DODI**, and **Game3rb**
- 🔍 Uses *fuzzy matching* for smarter search results
- 🤫 Filters out irrelevant or chatty messages ("hi", "who made you", etc.)
- 🎯 Prioritizes **title matches** based on user intent
- 💬 Behaves as a **direct assistant**, not a moral gatekeeper
- 🧠 Understands short/abbreviated queries like `GTA 5`, `COD MW2`
- 📊 Displays:
  - Game title + short description  
  - ✅ Direct, verified download link  
  - 💾 Size or version (if available)

---

## 🎭 Bot Behavior & Philosophy

- Pretends it is **not an AI**, just a "search bot"
- Filters out **non-search messages**
- Acts like an assistant **made by Flywich**, not a public chatbot
- Never explains ethics or piracy laws
- Gives **one clean answer** per query with relevant data only

---
## 🧩 How It Works

### 📥 Takes Input

e.g., `rdr2 ultimate edition`

---

### 🧹 Preprocessing

- Converts to lowercase  
- Removes filler/extra words  
- Expands known abbreviations  
  > Example: `rdr2 → red dead redemption 2`

---

### 🧠 Query Generation

- Generates multiple title variations  
- Adds keywords like `"repack"`, `"fitgirl"`, `"pc game"`, etc.

---

### 🌐 Scraping

Sends GET requests to:

- 🟣 [fitgirl-repacks.site](https://fitgirl-repacks.site)  
- 🔵 [dodi-repacks.site](https://dodi-repacks.site)  
- 🟢 [game3rb.com](https://game3rb.com)

---

### 📊 Title Scoring

- Uses `difflib.SequenceMatcher` to calculate similarity  
- Picks the most relevant match per site

---

### 🧾 Final Output

- Cleans the title  
- Formats game info + size + download link  
- Returns **1 result per site** (max 3)

---

## 🔐 API Security

- 🔑 Uses `OPENROUTER_API_KEY` (optional) via `.env` file  
- 💡 Recommended: **never hardcode keys**  
- ✅ Fully local — **no cloud, no analytics**

#### 🔒 Example:

```env
# .env
OPENROUTER_API_KEY=sk-yourkeyhere

``` 
#### 🛠️ Technologies Used

| Tool / Library      | Purpose                               |
| ------------------- | ------------------------------------- |
| **Python**          | Core programming language             |
| `requests`          | HTTP requests for site scraping       |
| `beautifulsoup4`    | HTML parsing for extracting game data |
| `difflib`           | Fuzzy string matching                 |
| `rich`              | Terminal formatting + colored output  |
| `dotenv` (optional) | Load API key from `.env` file         |


#### 🧪 Example Output
🎮 Game: Call of Duty: Modern Warfare II  
🔗 Link: https://dodi-repacks.site/call-of-duty-mw2-2022-dodi-repack/  
💾 Size: 48.2 GB


### 📈 Planned Improvements

```
🧠 AI reranking via OpenRouter API

🔧 CLI flags: --json, --silent, --source=fitgirl

🪟 Optional GUI via Tkinter or PyQt

🌐 Add more sources (e.g., SteamUnlocked, ElAmigos)

🧲 Show torrent + magnet links

🌍 Add filters: language, crack status, online/offline

🗃️ Create local cache for speed boost
```
----------

#### 📦 Installation
🐍 Requires Python 3.8+
```
git clone https://github.com/golnpiyush/niggaman
cd nigaaman
pip install -r requirements.txt
python games.py
```
### 🧑‍💻 Developed By
Piyush Golan
-------
#### ⚖️ License
Licensed under the MIT License.
See the LICENSE file for details.
