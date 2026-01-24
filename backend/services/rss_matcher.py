from typing import List
from config import settings

class RSSMatcher:
    """
    Matches newspaper names to RSS feed URLs
    Replaces the first ai_llm node in the JSON workflow
    """
    
    def match_feeds(self, newspaper_names: str) -> List[str]:
        """
        Match newspaper names to RSS feed URLs from the database
        
        Args:
            newspaper_names: Comma-separated string of newspaper names
            
        Returns:
            List of matching RSS feed URLs
        """
        # Parse newspaper names
        newspapers = [name.strip().lower() for name in newspaper_names.split(",")]
        
        # Domain mapping for Vietnamese newspapers
        domain_mapping = {
            "lao động": "laodong.vn",
            "laodong": "laodong.vn",
            "dân trí": "dantri.com.vn",
            "dantri": "dantri.com.vn",
            "vtv": "vtv.vn",
            "hà nội mới": "hanoimoi.vn",
            "hanoimoi": "hanoimoi.vn",
            "sài gòn giải phóng": "sggp.org.vn",
            "sggp": "sggp.org.vn",
            "vietnamplus": "vietnamplus.vn",
            "vietnam plus": "vietnamplus.vn",
            "tiền phong": "tienphong.vn",
            "tienphong": "tienphong.vn",
        }
        
        # Find matching domains
        matching_domains = []
        for newspaper in newspapers:
            if newspaper in domain_mapping:
                matching_domains.append(domain_mapping[newspaper])
        
        # Filter RSS feeds that contain any of the matching domains
        matched_feeds = []
        for feed_url in settings.RSS_DATABASE:
            for domain in matching_domains:
                if domain in feed_url:
                    matched_feeds.append(feed_url)
                    break
        
        return matched_feeds

rss_matcher = RSSMatcher()
