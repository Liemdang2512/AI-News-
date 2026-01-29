import requests
import json
import time
import os

BASE_URL = "http://localhost:8000/api"

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def test_rss_match():
    print("\n--- Testing RSS Matching ---")
    url = f"{BASE_URL}/rss/match"
    payload = {"newspapers": "dân trí, lao động, nhân dân"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            feeds = data.get("rss_feeds", [])
            has_nhandan = any("nhandan.vn" in feed for feed in feeds)
            print_result("RSS Match Response 200", True)
            print_result("Found Nhan Dan feed", has_nhandan, f"Feeds found: {len(feeds)}")
            return feeds
        else:
            print_result("RSS Match Response 200", False, f"Status: {response.status_code}")
            return []
    except Exception as e:
        print_result("RSS Match Connection", False, str(e))
        return []

def test_rss_fetch_phase2(feeds):
    print("\n--- Testing Phase 2 Features (Dedup & Verification) ---")
    if not feeds:
        print("Skipping - No feeds from previous step")
        return

    url = f"{BASE_URL}/rss/fetch"
    # Use today's date
    from datetime import datetime
    today = datetime.now().strftime("%d/%m/%Y")
    
    payload = {
        # Test with Nhan Dan + others to verify deduplication and Nhan Dan match
        "rss_urls": [
            "https://nhandan.vn/rss/kinhte", 
            "https://vnexpress.net/rss/kinh-doanh.rss",
            "https://dantri.com.vn/rss/kinh-doanh.rss"
        ], 
        "date": today,
        "time_range": "0h00 đến 23h59"
    }
    
    try:
        print(f"Fetching articles for {today}...")
        start_time = time.time()
        # Header for API key if needed
        headers = {}
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            headers["X-Gemini-API-Key"] = api_key
            
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            print_result("Fetch Articles Response 200", True, f"Time: {duration:.2f}s, Articles: {len(articles)}")
            
            # Check Phase 2 fields
            if articles:
                has_group_id = any(a.get("group_id") for a in articles)
                has_official_link = any(a.get("official_source_link") for a in articles)
                has_duplicates = any(a.get("duplicate_count", 0) > 0 for a in articles)
                
                print_result("Has Group IDs (Dedup running)", has_group_id)
                print_result("Has Official Source Links (Verification running)", has_official_link)
                print_result("Found Duplicates", has_duplicates)
                
                # Print sample
                print("\nSample Articles:")
                for a in articles[:5]:
                    badges = []
                    if a.get('official_source_link'): badges.append("✅ Verified")
                    if a.get('duplicate_count'): badges.append(f"🔗 +{a['duplicate_count']} dups")
                    
                    print(f"- [{a.get('source', '?')}] {a['title']}")
                    if badges:
                        print(f"  {' '.join(badges)}")
                    if a.get('event_summary'):
                        print(f"  📌 Event: {a['event_summary']}")
            else:
                 print_result("Articles Found", False, "No articles returned to test Phase 2 features")

        else:
            print_result("Fetch Articles Response 200", False, f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        print_result("Fetch Articles Connection", False, str(e))

if __name__ == "__main__":
    print("🚀 Starting Automated API Tests...")
    # Wait for server to be ready
    time.sleep(5)
    feeds = test_rss_match()
    test_rss_fetch_phase2(feeds)
