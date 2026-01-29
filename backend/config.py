import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Backend server configuration
    # Default host is 0.0.0.0 to preserve existing behaviour where the service
    # is reachable from other network interfaces (e.g. Docker, LAN).
    # Desktop/Electron builds can override this via BACKEND_HOST=127.0.0.1
    # if they only need local access.
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
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
        "https://vov.vn/rss/the-gioi.rss",
        "https://vov.vn/rss/kinh-te.rss",
        "https://vov.vn/rss/xa-hoi.rss",
        "https://vov.vn/rss/phap-luat.rss",
        "https://baotintuc.vn/the-gioi.rss",
        "https://baotintuc.vn/kinh-te.rss",
        "https://baotintuc.vn/xa-hoi.rss",
        "https://baotintuc.vn/phap-luat.rss",
        "https://tuoitre.vn/rss/phap-luat.rss",
        "https://tuoitre.vn/rss/the-gioi.rss",
        "https://tuoitre.vn/rss/kinh-doanh.rss",
        "https://tuoitre.vn/rss/thoi-su.rss",
        # Báo Nhân Dân (Official source for verification)
        "https://nhandan.vn/rss/kinhte-1185.rss",
        "https://nhandan.vn/rss/phapluat-1287.rss",
        "https://nhandan.vn/rss/xahoi-1211.rss",
        "https://nhandan.vn/rss/thegioi-1231.rss",
    ]


settings = Settings()
