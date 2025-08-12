
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Standalone proxy testing utility

from helper_funcs.proxy_fetcher import ProxyFetcher
import asyncio

async def main():
    fetcher = ProxyFetcher()
    
    print("🌐 Fetching fresh proxies from spys.one...")
    
    # Fetch HTTP proxies
    http_proxies = fetcher.fetch_spys_proxies("http", 15)
    print(f"✅ Found {len(http_proxies)} HTTP proxies")
    
    # Fetch SOCKS proxies  
    socks_proxies = fetcher.fetch_spys_proxies("socks", 15)
    print(f"✅ Found {len(socks_proxies)} SOCKS proxies")
    
    # Test some proxies
    all_proxies = http_proxies + socks_proxies
    if all_proxies:
        print(f"\n🧪 Testing first 5 proxies...")
        working_proxies = fetcher.get_working_proxies(all_proxies[:5], max_test=5)
        print(f"✅ {len(working_proxies)} out of 5 proxies are working")
        
        if working_proxies:
            print("\n🎯 Working proxies:")
            for proxy in working_proxies:
                print(f"  • {proxy}")
    else:
        print("❌ No proxies found")

if __name__ == "__main__":
    asyncio.run(main())
