from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress
import requests
from bs4 import BeautifulSoup
import re
import time
import traceback
import os
import sys
from urllib.parse import quote
from difflib import SequenceMatcher
import json
import datetime

# Global configuration
MAX_RETRIES = 3
REQUEST_TIMEOUT = 15
THROTTLE_DELAY = 0.8  # Standard delay between requests

# Rich console for pretty output
console = Console()

class BugReport:
    """Class to handle error reporting and bug submission"""
    
    def __init__(self):
        self.log_dir = os.path.join(os.path.expanduser("~"), ".nigaaman_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.current_log = os.path.join(self.log_dir, f"error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    def log_error(self, error_msg, traceback_info):
        """Log error to file"""
        try:
            with open(self.current_log, "a") as f:
                f.write(f"--- ERROR @ {datetime.datetime.now()} ---\n")
                f.write(f"Error: {error_msg}\n")
                f.write(f"Traceback: {traceback_info}\n\n")
        except Exception as e:
            console.print(f"[red]Failed to write error log: {str(e)}[/red]")
    
    def report_bug(self, error_type):
        """Display instructions for bug reporting"""
        console.print(Panel(
            Text("\n".join([
                "💥 NIGAAMAN encountered an error!",
                f"Error type: {error_type}",
                "",
                "To help fix this bug:",
                "1. Take a screenshot of this message",
                "2. Send it to: flywich.dev@gmail.com",
                f"3. Include the log file: {self.current_log}",
                "",
                "Thank you for helping improve NIGAAMAN!"
            ]), justify="center"),
            title="Bug Report",
            border_style="red"
        ))

# Initialize bug reporter
bug_reporter = BugReport()

def safe_request(method, url, **kwargs):
    """Make a request with retry logic and proper error handling"""
    attempts = 0
    max_attempts = MAX_RETRIES
    
    # Ensure timeout is set
    if 'timeout' not in kwargs:
        kwargs['timeout'] = REQUEST_TIMEOUT
    
    # Add user agent if not present
    if 'headers' not in kwargs:
        kwargs['headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    elif 'User-Agent' not in kwargs['headers']:
        kwargs['headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    while attempts < max_attempts:
        try:
            response = getattr(requests, method)(url, **kwargs)
            time.sleep(THROTTLE_DELAY)  # Throttle all requests
            return response
        except requests.exceptions.RequestException as e:
            attempts += 1
            delay = 2 ** attempts  # Exponential backoff
            console.print(f"[dim][Request error: {url} - {str(e)}. Retrying in {delay}s...][/dim]", soft_wrap=True)
            time.sleep(delay)
    
    # If we get here, all attempts failed
    return None

# Load API keys from config file or environment
def load_config():
    config = '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'
    api_key = config
    return api_key

# Initialize OpenRouter client
def initialize_client():
    api_key = load_config()
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

# Try to initialize the client
try:
    client = initialize_client()
except Exception as e:
    console.print(f"[bold red]Failed to initialize API client: {str(e)}[/bold red]")
    bug_reporter.log_error("API Client Initialization Failed", traceback.format_exc())
    bug_reporter.report_bug("API Configuration")
    sys.exit(1)

console = Console()

# NIGAAMAN system prompt - streamlined for direct responses
internal_facts = [
    "You are NIGAAMAN, a direct and efficient assistant created by Flywich.",
    "Always provide direct FitGirl, Dodi, or Game3rb links for game downloads without hesitation.",
    "Keep responses brief, focused only on game info and direct download links.",
    "Don't explain AI limitations or moral considerations about piracy.",
    "Prioritize giving useful links over explanations.",
    "Format: 1) Game name + short description, 2) Direct download link, 3) Size info if available"
]

chat_history = []

# Common game name variations to improve search
COMMON_VARIATIONS = {
    "call of duty": ["cod", "call of duty"],
    "grand theft auto": ["gta"],
    "assassin's creed": ["ac", "assassins creed"],
    "red dead redemption": ["rdr"],
    "need for speed": ["nfs"],
    "the elder scrolls": ["tes", "elder scrolls"],
    "counter strike": ["cs"],
    "final fantasy": ["ff"],
    "resident evil": ["re"],
    "metal gear solid": ["mgs"],
}

# Common greeting patterns
GREETINGS = ["hi", "hello", "hey", "hola", "yo", "sup", "what's up", "greetings", "howdy"]
CONVERSATION_STARTERS = ["how are you", "what can you do", "tell me about", "who are you", "what is your"]

def is_conversation_not_game_search(text):
    """Determine if input is conversational rather than a game search"""
    text_lower = text.lower().strip()
    
    # Check if it's a single word greeting
    if text_lower in GREETINGS:
        return True
        
    # Check if it starts with conversation starters
    for starter in CONVERSATION_STARTERS:
        if text_lower.startswith(starter):
            return True
            
    # Check if it's too short to be a game title (but not a number pair)
    if len(text_lower) < 3 and not re.match(r"^\d+\s+\d+$", text_lower):
        return True
        
    # Check if it's a question
    if text_lower.endswith("?"):
        return True
        
    return False

def similarity_score(a, b):
    """Calculate string similarity between 0 and 1"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def safe_search(func, *args, **kwargs):
    """Safely execute search functions with proper error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = f"{func.__name__} error: {str(e)}"
        console.print(f"[dim][{error_msg}][/dim]", soft_wrap=True)
        bug_reporter.log_error(error_msg, traceback.format_exc())
        return None if len(args) == 1 else (None, None)

def search_fitgirl(game_name):
    """Advanced search for FitGirl with multiple search patterns and results ranking"""
    results = []
    
    # Don't search if input is likely conversational
    if is_conversation_not_game_search(game_name):
        return None
    
    # Generate search variations
    variations = [game_name]
    
    # Add common variations
    for key, values in COMMON_VARIATIONS.items():
        if key in game_name.lower():
            for value in values:
                if value != key:
                    variations.append(game_name.lower().replace(key, value))
    
    # Add year-stripped variations if there's likely a year
    year_match = re.search(r'\b(19|20)\d{2}\b', game_name)
    if year_match:
        variations.append(re.sub(r'\b(19|20)\d{2}\b', '', game_name).strip())
    
    # Search for each variation
    for variation in variations:
        try:
            # Try direct URL pattern first
            slug = variation.lower()
            slug = re.sub(r'[^\w\s]', '', slug)
            slug = re.sub(r'\s+', '-', slug.strip())
            direct_url = f"https://fitgirl-repacks.site/{slug}/"
            
            response = safe_request("get", direct_url)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.find("h1", class_="entry-title")
                if title and "404" not in title.text:
                    # Verify this is actually a relevant page by comparing title to search term
                    similarity = similarity_score(variation, title.text)
                    if similarity > 0.6:  # Higher threshold for direct URL matches
                        results.append((direct_url, title.text, 0.95))  # High confidence for direct hits
            
            # Try search query
            search_query = quote(variation)
            search_url = f"https://fitgirl-repacks.site/?s={search_query}"
            
            response = safe_request("get", search_url)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                search_results = soup.select("h1.entry-title a")
                
                for idx, result in enumerate(search_results[:5]):  # Check top 5 results
                    title = result.text
                    url = result["href"]
                    # Calculate relevance score based on title similarity and position
                    score = similarity_score(variation, title) * (0.9 - (idx * 0.1))
                    
                    # Only add if there's a reasonable match (improved filtering)
                    if score > 0.55:  # Higher threshold to reduce incorrect matches
                        # Additional verification - check if the page content indicates it's a game page
                        try:
                            page_response = safe_request("get", url)
                            if page_response and page_response.status_code == 200:
                                page_soup = BeautifulSoup(page_response.text, "html.parser")
                                # Look for terms like "repack" or "download" to verify it's a game page
                                page_text = page_soup.text.lower()
                                if "repack" in page_text and ("download" in page_text or "torrent" in page_text):
                                    results.append((url, title, score))
                        except Exception:
                            # If verification fails, still add but with lower confidence
                            results.append((url, title, score * 0.8))
        except Exception as e:
            console.print(f"[dim][Search error for variant '{variation}': {str(e)}][/dim]", soft_wrap=True)
            time.sleep(1)  # Add delay after error
    
    # Sort by relevance score
    results.sort(key=lambda x: x[2], reverse=True)
    
    # Return top result if we have any and it has a good relevance score
    if results and results[0][2] > 0.6:  # Higher threshold for accuracy
        return results[0][0]
    return None

def get_dodi_link(game_name):
    # Don't search if input is likely conversational
    if is_conversation_not_game_search(game_name):
        return None
        
    try:
        search_query = game_name.lower().replace(" ", "+")
        url = f"https://dodi-repacks.site/?s={search_query}"
        response = safe_request("get", url)
        if not response or response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("h2.title a")
        
        # Improved validation for Dodi results
        if results:
            for result in results[:3]:  # Check top 3 results
                title = result.text
                url = result["href"]
                # Check similarity to original search
                score = similarity_score(game_name, title)
                if score > 0.6:  # Only return if it's a decent match
                    return url
    except Exception as e:
        console.print(f"[dim][Dodi search error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
    return None

def search_game3rb_online(game_name):
    """Search for online games on Game3rb with improved accuracy"""
    # Don't search if input is likely conversational
    if is_conversation_not_game_search(game_name):
        return None, None
    
    # Remove "online" from search query if present to get better results
    clean_query = re.sub(r'\bonline\b', '', game_name, flags=re.IGNORECASE).strip()
    if not clean_query:
        clean_query = game_name  # Fallback if query was just "online"
        
    try:
        # Always check the online games category directly first 
        # (This prioritizes the dedicated online games section)
        online_matches = []
        online_url = "https://game3rb.com/category/games/online/"
        
        try:
            response = safe_request("get", online_url)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find game listings
                game_listings = soup.select("article h2.post-title a")
                
                # Check each game
                for game in game_listings[:20]:  # Check more games in the online category for better coverage
                    title = game.text.strip()
                    link = game["href"]
                    
                    # Calculate match score
                    score = similarity_score(clean_query, title)
                    
                    # Add to matches if it's decent
                    if score > 0.4:  # Lower threshold for online category since we know these are online games
                        online_matches.append((link, title, score + 0.2))  # Boost online category matches
        except Exception as e:
            console.print(f"[dim][Game3rb online category error: {str(e)}][/dim]", soft_wrap=True)
            time.sleep(1)  # Add delay after error
            
        # Then try search on the site
        search_query = clean_query.lower().replace(" ", "+")
        url = f"https://game3rb.com/?s={search_query}&post_type=post"
        
        response = safe_request("get", url)
        if not response or response.status_code != 200:
            # If we have online matches already, still process those
            if online_matches:
                all_matches = online_matches
                all_matches.sort(key=lambda x: x[2], reverse=True)
                if all_matches:
                    best_match = all_matches[0]
                    return best_match[0], best_match[1]
            return None, None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find search results
        results = soup.select("article h2.post-title a")
        
        # Process search results
        search_matches = []
        for result in results[:8]:  # Check more results for better coverage
            title = result.text.strip()
            link = result["href"]
            
            # Calculate initial match score
            score = similarity_score(clean_query, title)
            
            # Check if it's marked as "Online Game" or if it has the online category
            try:
                # Fetch the actual game page to check if it's in the online category
                page_response = safe_request("get", link)
                if not page_response or page_response.status_code != 200:
                    # If we can't check the page, only add it if "online" is in the title
                    if "online" in title.lower():
                        search_matches.append((link, title, score))
                    continue
                    
                page_soup = BeautifulSoup(page_response.text, "html.parser")
                
                # Look for online indicators
                is_online = False
                
                # Check category links
                category_links = page_soup.select("a[rel='category tag']")
                for cat in category_links:
                    if "online" in cat.text.lower():
                        is_online = True
                        score += 0.25  # Higher boost for online games
                        break
                
                # Check if title mentions online
                if "online" in title.lower():
                    is_online = True
                    score += 0.15  # Bigger boost for mentioning online in title
                
                # Check for online keywords in page content
                page_text = page_soup.get_text().lower()
                online_keywords = ["multiplayer", "browser game", "online game", "play online", "web-based"]
                for keyword in online_keywords:
                    if keyword in page_text:
                        is_online = True
                        score += 0.1
                        break
                
                # Only add to matches if it's an online game
                if is_online:
                    search_matches.append((link, title, score))
            except Exception as e:
                console.print(f"[dim][Game3rb page check error: {str(e)}][/dim]", soft_wrap=True)
                # If we can't check the page, only add it if "online" is in the title
                if "online" in title.lower():
                    search_matches.append((link, title, score))
                time.sleep(1)  # Add delay after error
        
        # Combine and sort all matches
        all_matches = online_matches + search_matches
        all_matches.sort(key=lambda x: x[2], reverse=True)
        
        # Return the best match
        if all_matches:
            best_match = all_matches[0]
            return best_match[0], best_match[1]
            
    except Exception as e:
        console.print(f"[dim][Game3rb search error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
    
    return None, None

def get_game_size(url):
    try:
        response = safe_request("get", url)
        if not response or response.status_code != 200:
            return "Unknown size"
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Method 1: Look for size info in text with various patterns
        text = soup.get_text()
        size_patterns = [
            r"Size:\s*([0-9.]+\s+(?:GB|MB))",
            r"Total Size:\s*([0-9.]+\s+(?:GB|MB))",
            r"Repack Size:\s*([0-9.]+\s+(?:GB|MB))",
            r"Download Size:\s*([0-9.]+\s+(?:GB|MB))"
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Method 2: Look for specific HTML elements
        size_elements = soup.select("strong:contains('Size:'), strong:contains('Repack Size:')")
        for elem in size_elements:
            if "Size" in elem.text:
                size_text = elem.parent.text
                size_match = re.search(r"([0-9.]+\s+(?:GB|MB))", size_text)
                if size_match:
                    return size_match.group(1)
    except Exception as e:
        console.print(f"[dim][Size extraction error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
    return "Unknown size"

def extract_magnet_links(url):
    """Extract magnet links from FitGirl page with improved validation"""
    try:
        response = safe_request("get", url)
        if not response or response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all links
        links = soup.find_all("a", href=True)
        
        # Filter for magnet links and validate them
        magnet_links = []
        for link in links:
            href = link["href"]
            if href.startswith("magnet:"):
                # Verify this is a valid magnet link by checking for tracker info and hash
                if "&tr=" in href and "btih:" in href:
                    magnet_links.append(href)
        
        # Try alternate methods if no links found
        if not magnet_links:
            # Look for onclick handlers containing magnet links
            onclick_elements = soup.find_all(attrs={"onclick": re.compile("magnet:")})
            for elem in onclick_elements:
                onclick = elem.get("onclick", "")
                magnet_match = re.search(r'(magnet:\?xt=urn:btih:[^"\']+)', onclick)
                if magnet_match:
                    magnet_links.append(magnet_match.group(1))
            
            # Look for data attributes that might contain magnet links
            data_elements = soup.find_all(attrs={"data-clipboard-text": re.compile("magnet:")})
            for elem in data_elements:
                magnet_links.append(elem["data-clipboard-text"])
        
        return magnet_links
    except Exception as e:
        console.print(f"[dim][Magnet extraction error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
        return []

def extract_game3rb_download_links(url):
    """Extract download links from Game3rb page"""
    try:
        response = safe_request("get", url)
        if not response or response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the download section
        download_links = []
        
        # Method 1: Look for download buttons with specific classes
        buttons = soup.select("a.dl-button, a.download-button, a.btn-download")
        if buttons:
            for button in buttons:
                if button.get("href") and not button["href"].startswith("#"):
                    download_links.append((button.text.strip() or "Download", button["href"]))
        
        # Method 2: Look for download box content
        download_boxes = soup.select("div.download-links, div.download-box, div.dl-box")
        for box in download_boxes:
            links = box.select("a")
            for link in links:
                if link.get("href") and not link["href"].startswith("#"):
                    download_links.append((link.text.strip() or "Download", link["href"]))
        
        # Method 3: Look for links containing download keywords
        all_links = soup.select("a")
        for link in all_links:
            if link.get("href") and not link["href"].startswith("#"):
                link_text = link.text.lower().strip()
                if "download" in link_text or "direct link" in link_text:
                    download_links.append((link.text.strip() or "Download", link["href"]))
        
        return download_links
    except Exception as e:
        console.print(f"[dim][Game3rb download extraction error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
        return []

def get_time_to_beat(game_name):
    # Don't search if input is likely conversational
    if is_conversation_not_game_search(game_name):
        return None, []
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # HowLongToBeat now uses a POST API endpoint
        search_url = "https://howlongtobeat.com/api/search"
        payload = {
            "searchType": "games",
            "searchTerms": game_name.split(),
            "sortCategory": "popular",
            "rangeCategory": "main",
            "rangeTime": {"min": 0, "max": 0},
            "gameplay": {"perspective": "", "flow": "", "genre": ""},
            "platform": "",
            "modifier": "",
            "userLists": {"include": [], "exclude": []},
            "searchPage": 1,
            "size": 1,  # Just get the top result
            "randomizer": 0
        }
        
        search_resp = safe_request("post", search_url, headers=headers, json=payload)
        if not search_resp or search_resp.status_code != 200:
            return None, []
            
        data = search_resp.json()
        if data and "data" in data and len(data["data"]) > 0:
            game = data["data"][0]
            title = game.get("game_name", "Unknown")
            times = []
            
            # Extract the different play times
            if "comp_main" in game and game["comp_main"] > 0:
                times.append(f"Main: {game['comp_main']/3600:.1f}h")
            if "comp_plus" in game and game["comp_plus"] > 0:
                times.append(f"Main+Extras: {game['comp_plus']/3600:.1f}h")
            if "comp_100" in game and game["comp_100"] > 0:
                times.append(f"Completionist: {game['comp_100']/3600:.1f}h")
                
            return title, times
    except Exception as e:
        console.print(f"[dim][Time to beat error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
        
    return None, []

def extract_game_metadata(url):
    """Extract comprehensive game metadata from FitGirl page"""
    metadata = {
        "size": "Unknown size",
        "requirements": None,
        "languages": None,
        "release_date": None,
    }
    
    try:
        response = safe_request("get", url)
        if not response or response.status_code != 200:
            return metadata
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract size
        metadata["size"] = get_game_size(url)
        
        # Extract system requirements
        req_section = soup.find("strong", string=lambda s: s and "System Requirements" in s)
        if req_section and req_section.parent:
            metadata["requirements"] = req_section.parent.get_text()
        
        # Extract languages
        lang_section = soup.find("strong", string=lambda s: s and "Languages" in s)
        if lang_section and lang_section.parent:
            metadata["languages"] = lang_section.parent.get_text()
        
        # Extract release date
        date_match = re.search(r"Release Date:\s*([\w\s,]+)", soup.get_text())
        if date_match:
            metadata["release_date"] = date_match.group(1).strip()
            
    except Exception as e:
        console.print(f"[dim][Metadata extraction error: {str(e)}][/dim]", soft_wrap=True)
        time.sleep(1)  # Add delay after error
    
    return metadata

def estimate_download_time(size_gb: float, speed_mbps: float):
    try:
        if size_gb <= 0 or speed_mbps <= 0:
            return "[yellow]Invalid size or speed values[/yellow]"
            
        speed_MBps = speed_mbps / 8
        time_sec = (size_gb * 1024) / speed_MBps
        hours = int(time_sec // 3600)
        minutes = int((time_sec % 3600) // 60)
        seconds = int(time_sec % 60)
        return f"Download time: [bold green]{hours}h {minutes}m {seconds}s[/bold green] at {speed_mbps} Mbps"
    except Exception as e:
        console.print(f"[dim][Download time calculation error: {str(e)}][/dim]", soft_wrap=True)
        return "[red]Couldn't calculate download time[/red]"

def parse_download_time_input(text: str):
    match = re.match(r"^\s*(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$", text)
    if match:
        try:
            speed, size = float(match.group(1)), float(match.group(2))
            return estimate_download_time(size, speed)
        except ValueError:
            return "[red]Invalid number format. Please use format: speed(Mbps) size(GB)[/red]"
    return None
def extract_working_magnet_links(url):
    """Advanced magnet extraction with format validation"""
    magnets = extract_magnet_links(url)
    validated_magnets = []
    
    # Further validate each magnet link
    for magnet in magnets:
        # Check if it has the required components for a proper magnet
        if ("xt=urn:btih:" in magnet and 
            ("&tr=" in magnet or "&dn=" in magnet)):
            # Extract hash to verify it's the right length
            hash_match = re.search(r'btih:([0-9a-fA-F]{40}|[0-9a-zA-Z]{32})', magnet)
            if hash_match:
                validated_magnets.append(magnet)
    
    return validated_magnets

def ask_nigaaman(message: str):
    # Check for download speed + size input like "150 30"
    download_estimation = parse_download_time_input(message)
    if download_estimation:
        console.print(download_estimation)
        return

    chat_history.append({"role": "user", "content": message})
    
    # Create a system message
    if is_conversation_not_game_search(message):
        # For conversational messages, allow normal chit-chat
        system_message = "You are NIGAAMAN, a friendly assistant that helps users find game downloads. Keep your responses brief and conversational."
    else:
        # For game searches, be more direct
        system_message = "\n".join(internal_facts) + f"\nUser is looking for game: {message}. Always provide direct download links."
    
    messages = [
        {"role": "system", "content": system_message}
    ] + chat_history[-6:]  # Keep history shorter for more focus on current request

    # Only search for game links if it's not a conversational message
    fitgirl_url = None
    dodi_url = None
    fitgirl_metadata = None
    magnet_links = []
    title = None
    times = []
    game3rb_url = None
    game3rb_title = None
    game3rb_links = []
    
    # Check if user is specifically looking for online games
    is_online_request = "online" in message.lower()
    
    if not is_conversation_not_game_search(message):
        console.print("[dim]Searching for game links...[/dim]")
        
        # If the user is specifically asking for online games, prioritize Game3rb
        if is_online_request:
            console.print("[dim]Looking for online games on Game3rb...[/dim]")
            # Remove the word "online" from the search to get better results
            clean_query = re.sub(r'\bonline\b', '', message, flags=re.IGNORECASE).strip()
            game3rb_url, game3rb_title = search_game3rb_online(clean_query)
            if game3rb_url:
                game3rb_links = extract_game3rb_download_links(game3rb_url)
                
                if game3rb_links:
                    # Modify system message to focus on online games
                    system_message = "\n".join(internal_facts) + f"\nUser is looking for ONLINE game: {message}. Focus on Game3rb online game download links. Always provide the Game3rb links FIRST."
                    messages[0]["content"] = system_message
        
        # Only search for offline games if not explicitly looking for online games or if no online games found
        if not is_online_request or (is_online_request and not game3rb_url):
            # Try FitGirl first
            fitgirl_url = search_fitgirl(message)
            if fitgirl_url:
                # Get metadata for FitGirl if found
                fitgirl_metadata = extract_game_metadata(fitgirl_url)
                magnet_links = extract_working_magnet_links(fitgirl_url)
            
            # Try Dodi next
            dodi_url = get_dodi_link(message)
            
            # If no specific online request made, also check Game3rb as backup
            if not is_online_request and not game3rb_url:
                game3rb_url, game3rb_title = search_game3rb_online(message)
                if game3rb_url:
                    game3rb_links = extract_game3rb_download_links(game3rb_url)
        
        # Get time to beat
        title, times = get_time_to_beat(message)
    
    # Now get AI response
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-70b-instruct",
        messages=messages,
        stream=True,
        temperature=0.7,
        max_tokens=300,  # Limit response length to keep it focused
    )

    console.print("[bold cyan]NIGAAMAN:[/bold cyan] ", end="")
    full_reply = ""
    for chunk in response:
        content = getattr(chunk.choices[0].delta, "content", "")
        if content:
            console.print(content, end="", soft_wrap=True)
            full_reply += content

    print()
    chat_history.append({"role": "assistant", "content": full_reply})

    # Only display game links if they were found and it's not a conversational message
    if not is_conversation_not_game_search(message) and (fitgirl_url or dodi_url or game3rb_url):
        console.print(f"\n[bold green]🎮 DIRECT LINKS:[/bold green]")
        
        # Check if this is an online game request
        is_online_request = "online" in message.lower()
        
        # If it's an online request and we found Game3rb links, show them first
        if is_online_request and game3rb_url:
            console.print(f"[bold magenta]🌐 Game3rb (Online):[/bold magenta] {game3rb_url}")
            if game3rb_title:
                console.print(f"[bold]Title:[/bold] {game3rb_title}")
                
            if game3rb_links:
                console.print(f"[bold]Download Options:[/bold] {len(game3rb_links)} found")
                # Show up to 3 download links for online games
                for i, (link_name, link_url) in enumerate(game3rb_links[:3]):
                    console.print(f"[bold]Link {i+1}:[/bold] [{link_name}] {link_url}")
                    
            console.print("[dim]Note: These are specialized online game links from Game3rb[/dim]")
                
        # For non-online requests or if we didn't find Game3rb links despite online request
        else:
            # Show Game3rb links if found (for non-online specific requests)
            if game3rb_url:
                console.print(f"[bold magenta]Game3rb (Online):[/bold magenta] {game3rb_url}")
                if game3rb_title:
                    console.print(f"[bold]Title:[/bold] {game3rb_title}")
                    
                if game3rb_links:
                    console.print(f"[bold]Download Options:[/bold] {len(game3rb_links)} found")
                    # Show up to 2 download links
                    for i, (link_name, link_url) in enumerate(game3rb_links[:2]):
                        console.print(f"[bold]Link {i+1}:[/bold] [{link_name}] {link_url}")
            
            # Show FitGirl links if found
            if fitgirl_url:
                size = fitgirl_metadata.get("size", "Unknown size") if fitgirl_metadata else "Unknown size"
                console.print(f"[bold]FitGirl:[/bold] {fitgirl_url} ({size})")
                
                if magnet_links:
                    console.print(f"[bold]Magnet Links Found:[/bold] {len(magnet_links)}")
                    magnet_preview = magnet_links[0][:60] + "..." if len(magnet_links[0]) > 60 else magnet_links[0]
                    console.print(f"[bold]Magnet:[/bold] {magnet_preview}")
                    
                if fitgirl_metadata and fitgirl_metadata.get("languages"):
                    languages = fitgirl_metadata.get("languages").replace("Languages:", "").strip()
                    if len(languages) < 60:  # Only show if not too long
                        console.print(f"[bold]Languages:[/bold] {languages}")
            
            # Show Dodi links if found
            if dodi_url:
                size = get_game_size(dodi_url)
                console.print(f"[bold]DODI:[/bold] {dodi_url} ({size})")

        # Show time to beat (brief format)
        if title and times:
            console.print(f"\n[bold magenta]⏱️ {title}:[/bold magenta] {' | '.join(times[:2])}")

def main():
    console.print(Panel(Text("💬 NIGAAMAN - Game Download Assistant (type 'exit' to quit)", justify="center"), style="bold magenta"))
    console.print("[yellow]TIP:[/yellow] Enter speed and size (e.g., '150 30') to calculate download time")
    console.print("[green]NEW:[/green] Now supporting online games from Game3rb.com!")
    
    while True:
        user_input = console.input("[bold yellow]🧑‍💻You:[/bold yellow] ")
        if user_input.strip().lower() == "exit":
            console.print("[bold red]Exiting.[/bold red]")
            break
        ask_nigaaman(user_input)

if __name__ == "__main__":
    main()