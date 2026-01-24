import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # RSS Feed Database (from JSON workflow)
    RSS_DATABASE = [
        "https://laodong.vn/rss/thoi-su.rss",
        "https://laodong.vn/rss/the-gioi.rss",
        "https://laodong.vn/rss/xa-hoi.rss",
        "https://laodong.vn/rss/kinh-doanh.rss",
        "https://laodong.vn/rss/phap-luat.rss",
        "https://dantri.com.vn/rss/phap-luat.rss",
        "https://dantri.com.vn/rss/kinh-doanh.rss",
        "https://dantri.com.vn/rss/doi-song.rss",
        "https://dantri.com.vn/rss/the-gioi.rss",
        "https://vtv.vn/rss/xa-hoi.rss",
        "https://vtv.vn/rss/phap-luat.rss",
        "https://vtv.vn/rss/the-gioi.rss",
        "https://vtv.vn/rss/kinh-te.rss",
        "https://hanoimoi.vn/rss/xa-hoi",
        "https://hanoimoi.vn/rss/the-gioi",
        "https://hanoimoi.vn/rss/phap-luat",
        "https://hanoimoi.vn/rss/kinh-te",
        "https://www.sggp.org.vn/rss/xahoi-199.rss",
        "https://www.sggp.org.vn/rss/phapluat-112.rss",
        "https://www.sggp.org.vn/rss/kinhte-89.rss",
        "https://www.sggp.org.vn/rss/thegioi-143.rss",
        "https://www.vietnamplus.vn/rss/kinhte-311.rss",
        "https://www.vietnamplus.vn/rss/thegioi-209.rss",
        "https://www.vietnamplus.vn/rss/xahoi/phapluat-327.rss",
        "https://www.vietnamplus.vn/rss/xahoi-314.rss",
        "https://tienphong.vn/rss/xa-hoi-2.rss",
        "https://tienphong.vn/rss/kinh-te-3.rss",
        "https://tienphong.vn/rss/the-gioi-5.rss",
        "https://tienphong.vn/rss/phap-luat-12.rss",
    ]

settings = Settings()
