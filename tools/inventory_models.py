import json
import os
import requests

def get_stanza_inventory():
    print("=== Stanza Constituency Inventory ===")
    # Try to find local resources first (standard Stanza path)
    local_path = os.path.expanduser("~/stanza_resources/resources.json")
    data = None
    
    if os.path.exists(local_path):
        print(f"📂 Reading local resources: {local_path}")
        try:
            with open(local_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading local file: {e}")
            
    if not data:
        # Fallback to remote (using version 1.8.0 structure as baseline, usually compatible)
        # Note: Stanza versions change this URL, but structure is stable.
        url = "https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main/resources_1.8.0.json"
        print(f"🌐 Fetching remote resources: {url}")
        try:
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
            else:
                print(f"❌ Failed to fetch resources: {r.status_code}")
        except Exception as e:
            print(f"❌ Network error: {e}")
            return

    if data:
        langs = []
        for lang, content in data.items():
            if isinstance(content, dict) and 'constituency' in content:
                models = list(content['constituency'].keys())
                langs.append((lang, models))
        
        langs.sort()
        print(f"\nFound {len(langs)} languages with Constituency support in Stanza:")
        for lang, models in langs:
            print(f" - [{lang}]: {', '.join(models)}")
    else:
        print("Could not load Stanza resources.")

def get_benepar_inventory():
    print("\n=== Benepar (spaCy) Inventory ===")
    print("Official models (NLTK/Benepar Registry):")
    # Static list based on Benepar documentation (no dynamic registry API available)
    official = {
        "en": "English (benepar_en3)",
        "zh": "Chinese (benepar_zh)",
        "ar": "Arabic",
        "eu": "Basque",
        "fr": "French (benepar_fr2)",
        "de": "German (benepar_de2)",
        "he": "Hebrew",
        "hu": "Hungarian",
        "ko": "Korean",
        "pl": "Polish",
        "ru": "Russian",
        "sv": "Swedish"
    }
    for lang, desc in official.items():
        print(f" - [{lang}]: {desc}")
    print(f"Total Official Languages: {len(official)}")
    print("Note: Spanish (es) is NOT official. Requires Hugging Face community models.")

if __name__ == "__main__":
    get_stanza_inventory()
    get_benepar_inventory()