🎮 NIGAAMAN — Game Download Link Finder
NIGAAMAN is a direct and no-nonsense AI assistant created by Flywich that helps users quickly find reliable, direct download links for PC games from trusted repack sources like FitGirl, DODI, and Game3rb.

Built using OpenRouter, BeautifulSoup, and Rich, this CLI tool focuses purely on delivering what matters: verified game titles with working links.


✨ Features
🎯 Instant FitGirl, Dodi, and Game3rb links

⚡ Fast & minimal interaction — no chit-chat

🧠 Smart game title matching using difflib

🚫 Automatically filters out non-game or conversational input

🔎 Variations support (e.g. GTA → Grand Theft Auto)

🛡️ Handles broken or mismatched results gracefully

🚀 Getting Started
Prerequisites
Python 3.8+

pip install -r requirements.txt

bash
Copy
Edit
pip install openai rich beautifulsoup4 requests
Setup
Update your OpenRouter API key in the script:

python
Copy
Edit
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-xxxx",  # Replace with your key
)
🕹️ Usage
Run the script:

bash
Copy
Edit
python nigaaman.py
Then enter a game name like:

markdown
Copy
Edit
> Assassin's Creed Valhalla
And receive:

markdown
Copy
Edit
1. Assassin's Creed Valhalla - Action RPG in Viking Age
2. 🔗 https://fitgirl-repacks.site/assassins-creed-valhalla/
3. 📦 Size: ~55 GB
If unavailable on FitGirl, fallback links from DODI or Game3rb will be fetched.

🧠 Logic & Behavior
The assistant ignores conversational input like:

"Hello", "How are you?", "What can you do?"

It focuses entirely on:

Matching game titles using string similarity

Searching across FitGirl, DODI, and Game3rb

For FitGirl:

Direct URL patterns and search results are both used

For DODI & Game3rb:

Top results are ranked by similarity

🔐 API Security
This tool uses the OpenRouter API for AI-backed interactions.

⚠️ Never expose your API key in public repositories!

📌 Notes
NIGAAMAN does not care about piracy ethics — it’s designed for raw functionality.

Best used for personal automation or hobbyist setups.

🧑‍💻 Author
Piyush Golan

📜 License
This project is intended for educational and personal use only.
Use at your own risk.
