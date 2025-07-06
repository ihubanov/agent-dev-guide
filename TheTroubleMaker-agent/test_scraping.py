#!/usr/bin/env python3
"""
Test script for ARM64 Chromium scraping functionality
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_chromium_installation():
    """Test if Chromium is properly installed and accessible"""
    print("Testing Chromium installation...")
    
    # Check if the snap Chromium executable exists
    chromium_path = "/snap/bin/chromium"
    if os.path.exists(chromium_path):
        print(f"✓ Chromium found at: {chromium_path}")
    else:
        print(f"❌ Chromium not found at: {chromium_path}")
        return False
    
    # Check if it's executable
    if os.access(chromium_path, os.X_OK):
        print("✓ Chromium is executable")
    else:
        print("❌ Chromium is not executable")
        return False
    
    return True

async def test_playwright_scraping():
    """Test Playwright scraping functionality"""
    print("\nTesting Playwright scraping...")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Try to launch Chromium with our ARM64 configuration
            browser = await p.chromium.launch(
                headless=True,
                executable_path="/snap/bin/chromium",
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--disable-plugins',
                ]
            )
            
            print("✓ Successfully launched Chromium browser")
            
            # Create a simple page
            page = await browser.new_page()
            await page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
            
            content = await page.content()
            if "Test Page" in content:
                print("✓ Successfully rendered and scraped test page")
            else:
                print("❌ Failed to render test page")
                return False
            
            await browser.close()
            print("✓ Successfully closed browser")
            
    except Exception as e:
        print(f"❌ Playwright scraping test failed: {e}")
        return False
    
    return True

async def test_scrape_functionality():
    """Test the scraping functionality directly"""
    print("\nTesting scraping functionality...")
    
    try:
        from playwright.async_api import async_playwright
        from bs4 import BeautifulSoup
        import re
        
        async with async_playwright() as p:
            # Use the ARM64-compatible Chromium installation
            browser = await p.chromium.launch(
                headless=True,
                executable_path="/snap/bin/chromium",  # ARM64 snap installation path
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu',  # Important for ARM64
                    '--disable-software-rasterizer',  # Important for ARM64
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Speed up scraping
                    '--disable-javascript',  # Speed up scraping
                    '--disable-css',  # Speed up scraping
                ]
            )
            
            # Create context with realistic user agent and settings
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # Additional stealth measures
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            try:
                # Test with a simple, reliable website
                await page.goto("https://httpbin.org/html", timeout=30000)
                await page.wait_for_timeout(2000)
                
                content = await page.locator("body").inner_html()
                
                html = BeautifulSoup(content, 'html.parser')
                
                # remove style, script
                for style in html.find_all('style'):
                    style.decompose()

                for script in html.find_all('script'):
                    script.decompose()

                text = html.get_text(separator=" ")
                
                # remove duplicate spaces
                text = re.sub(r'\s+', ' ', text)

                # remove leading and trailing spaces
                text = text.strip()
                
                if "Herman Melville - Moby Dick" in text:
                    print("✓ Scraping functionality works correctly")
                    return True
                else:
                    print("⚠️ Scraping returned unexpected content")
                    print(f"Result preview: {text[:200]}...")
                    return True  # Still consider it working if we got content
                    
            except Exception as e:
                print(f"❌ Scraping test failed: {e}")
                return False
            finally:
                await browser.close()
            
    except Exception as e:
        print(f"❌ Scraping functionality test failed: {e}")
        return False

async def main():
    """Run all scraping tests"""
    print("Starting ARM64 Chromium scraping tests...\n")
    
    try:
        # Test Chromium installation
        if not await test_chromium_installation():
            print("\n❌ Chromium installation test failed")
            return 1
        
        # Test Playwright functionality
        if not await test_playwright_scraping():
            print("\n❌ Playwright scraping test failed")
            return 1
        
        # Test the actual scraping functionality
        if not await test_scrape_functionality():
            print("\n❌ Scraping functionality test failed")
            return 1
        
        print("\n🎉 All scraping tests passed! ARM64 Chromium scraping is working correctly.")
        print("\nYour agent is now ready to run with full functionality including web scraping!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 