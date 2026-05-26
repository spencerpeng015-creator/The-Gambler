import base64
import time
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class KalshiClient:
    def __init__(self, base_url: str, api_key_id: str, private_key_pem: str):
        self.base_url = base_url.rstrip("/")
        self.api_key_id = api_key_id
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
        )

    def _sign(self, timestamp_ms: str, method: str, path: str) -> str:
        message = f"{timestamp_ms}{method.upper()}{path}".encode()
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def _headers(self, method: str, path: str):
        timestamp_ms = str(int(time.time() * 1000))
        signature = self._sign(timestamp_ms, method, path)
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json",
        }

    def get_balance(self):
        path = "/trade-api/v2/portfolio/balance"
        url = f"{self.base_url}/portfolio/balance"
        r = requests.get(url, headers=self._headers("GET", path), timeout=15)
        r.raise_for_status()
        return r.json()

    def get_markets(self, status="open", limit=100):
        url = f"{self.base_url}/markets?status={status}&limit={limit}"
        sign_path = "/trade-api/v2/markets"
        r = requests.get(url, headers=self._headers("GET", sign_path), timeout=15)
        r.raise_for_status()
        return r.json()

    def get_orderbook(self, ticker: str):
        path = f"/trade-api/v2/markets/{ticker}/orderbook"
        url = f"{self.base_url}/markets/{ticker}/orderbook"
        r = requests.get(url, headers=self._headers("GET", path), timeout=15)
        r.raise_for_status()
        return r.json()

    def get_positions(self):
        path = "/trade-api/v2/portfolio/positions"
        url = f"{self.base_url}/portfolio/positions"
        r = requests.get(url, headers=self._headers("GET", path), timeout=15)
        r.raise_for_status()
        return r.json()

    def create_order(self, order_data: dict):
        url = f"{self.base_url}/portfolio/orders"
        sign_path = urlparse(url).path
        headers = self._headers("POST", sign_path)
        r = requests.post(url, headers=headers, json=order_data, timeout=15)
        r.raise_for_status()
        return r.json()
