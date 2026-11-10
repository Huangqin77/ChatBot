import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///./chatroom.db'))
    api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''), repr=False)
    base_url: str = field(default_factory=lambda: os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'))
    model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'))
    mode: str = field(default_factory=lambda: os.getenv('LLM_MODE', 'auto'))
    origins: list[str] = field(default_factory=lambda: os.getenv(
        'FRONTEND_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','))

    @property
    def demo(self) -> bool:
        return self.mode == 'demo' or (self.mode == 'auto' and not self.api_key)

    def __post_init__(self):
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.strip().rstrip('/')
        self.model = self.model.strip()
        if self.mode not in {'auto', 'demo', 'live'}:
            raise ValueError('LLM_MODE must be auto, demo or live')
        url = urlsplit(self.base_url)
        if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('OPENAI_BASE_URL 必须为 HTTP(S) API 地址，不得包含凭据、查询参数或片段。')
        if not self.model:
            raise ValueError('OPENAI_MODEL 不能为空')
