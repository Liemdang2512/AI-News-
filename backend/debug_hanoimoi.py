from services.secure_fetcher import secure_fetcher
from services.summarizer import summarizer
import asyncio

async def test_fetch():
    url = "https://hanoimoi.vn/phuong-hai-ba-trung-mong-som-dua-khu-dat-vang-94-pho-lo-duc-vao-su-dung-731520.html"
    print(f"Fetching: {url}")
    
    try:
        content = await secure_fetcher.fetch_rss(url)
        print(f"Length: {len(content)}")
        
        # Test Extraction
        extracted = summarizer._extract_content(content)
        print(f"Extracted length: {len(extracted)}")
        if len(extracted) < 200:
            print("❌ Extraction FAILED: Content too short")
            print("Preview:", extracted)
        else:
            print("✅ Extraction SUCCESS")
            print("Preview:", extracted[:200])
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
