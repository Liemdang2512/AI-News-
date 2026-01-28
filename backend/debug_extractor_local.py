from bs4 import BeautifulSoup
from services.summarizer import summarizer

def debug_extraction():
    with open("hanoimoi.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script/style
    for script in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
        script.decompose()

    selectors = [
        'article', 
        '[role="main"]', 
        '.post-content', 
        '.article-content', 
        '#content', 
        '.content',
        '.entry', 
        '.b-maincontent',
        '.fck_detail',
        '.details__content',
        '.cms-body', 
        '#article-body', 
        '.article-body', 
        '.content-detail', 
        '.detail-content', 
        '.post_content',
        '.body-content'
    ]
    
    print("Testing selectors...")
    for selector in selectors:
        found = soup.select_one(selector)
        if found:
            print(f"✅ FOUND selector: {selector}")
            text = found.get_text(separator=' ', strip=True)
            print(f"   Length: {len(text)}")
            print(f"   Preview: {text[:100]}...")
            # break # Don't break, see all matches
        else:
            print(f"❌ Not found: {selector}")

if __name__ == "__main__":
    debug_extraction()
