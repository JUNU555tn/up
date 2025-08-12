
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Dynamic proxy fetcher from spys.one

import requests
import re
import logging
import random
from typing import List, Optional

logger = logging.getLogger(__name__)

class ProxyFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_spys_proxies(self, proxy_type: str = "http", limit: int = 20) -> List[str]:
        """
        Fetch fresh proxies from spys.one
        
        Args:
            proxy_type: "http" or "socks"
            limit: Maximum number of proxies to return
        """
        try:
            if proxy_type == "http":
                url = "https://spys.one/en/http-proxy-list/"
            else:
                url = "https://spys.one/en/socks-proxy-list/"
            
            logger.info(f"Fetching {proxy_type} proxies from spys.one...")
            
            # First request to get the page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Extract proxy data using regex
            # Pattern for IP:PORT format
            proxy_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})'
            matches = re.findall(proxy_pattern, response.text)
            
            proxies = []
            for ip, port in matches[:limit]:
                if self._is_valid_ip(ip) and self._is_valid_port(port):
                    if proxy_type == "http":
                        proxy_url = f"http://{ip}:{port}"
                    else:
                        proxy_url = f"socks5://{ip}:{port}"
                    proxies.append(proxy_url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_proxies = []
            for proxy in proxies:
                if proxy not in seen:
                    seen.add(proxy)
                    unique_proxies.append(proxy)
            
            logger.info(f"Successfully fetched {len(unique_proxies)} {proxy_type} proxies from spys.one")
            return unique_proxies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to fetch proxies from spys.one: {e}")
            return []
    
    def fetch_all_proxy_types(self, limit_per_type: int = 15) -> List[str]:
        """Fetch both HTTP and SOCKS proxies"""
        all_proxies = []
        
        # Fetch HTTP proxies
        http_proxies = self.fetch_spys_proxies("http", limit_per_type)
        all_proxies.extend(http_proxies)
        
        # Fetch SOCKS proxies
        socks_proxies = self.fetch_spys_proxies("socks", limit_per_type)
        all_proxies.extend(socks_proxies)
        
        # Shuffle for better distribution
        random.shuffle(all_proxies)
        
        return all_proxies
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_valid_port(self, port: str) -> bool:
        """Validate port number"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    def test_proxy(self, proxy_url: str, test_url: str = "https://httpbin.org/ip", timeout: int = 10) -> bool:
        """Test if a proxy is working"""
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_working_proxies(self, proxy_list: List[str], max_test: int = 10) -> List[str]:
        """Test proxies and return working ones"""
        working_proxies = []
        tested_count = 0
        
        for proxy in proxy_list:
            if tested_count >= max_test:
                break
                
            logger.info(f"Testing proxy: {proxy}")
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
                logger.info(f"Proxy {proxy} is working")
            else:
                logger.info(f"Proxy {proxy} failed test")
            
            tested_count += 1
        
        return working_proxies
