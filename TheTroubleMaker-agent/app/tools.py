from googlesearch import search, SearchResult
from fastmcp import FastMCP
import ast
import sys
import subprocess
from typing import Literal, Optional
import asyncio
import logging
from bs4 import BeautifulSoup
import re
from playwright.async_api import async_playwright
import resource
import os
import httpx
import json
import math
from app.configs import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvanceSearchResult(SearchResult):
    def __init__(self, SearchResult: SearchResult, score: float):
        super().__init__(SearchResult.url, SearchResult.title, SearchResult.description)
        self.score = score

    def __repr__(self):
        return f"SearchResult(url={self.url!r}, title={self.title!r}, description={self.description!r}, score={self.score})"

python_toolkit = FastMCP(name="Python-Toolkit")
web_toolkit = FastMCP(name="Web-Toolkit")
bio_toolkit = FastMCP(name="Bio-Toolkit")
leakosint_toolkit = FastMCP(name="Leakosint-Toolkit")
sequential_thinking_toolkit = FastMCP(name="Sequential-Thinking-Toolkit")

def limit_resource(memory_limit: int, cpu_limit: int):
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

@python_toolkit.tool(
    name="run",
    description="Run Python code. Return the result of the code and all declared variables. Use this toolcall for complex tasks like math solving, data analysis, etc.",
    annotations={
        "code": "The Python code to execute",
    }
)
async def python_interpreter(code: str) -> str:
    variables = []
    with open("code.txt", "a") as f:
        f.write(code + '\n')

    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            first_target = node.targets[0]
            if isinstance(first_target, ast.Name):
                variables.append(first_target.id)
                
            if isinstance(first_target, ast.Attribute):
                variables.append(first_target.attr)
            
            if isinstance(first_target, ast.Subscript):
                if isinstance(first_target.value, ast.Name):
                    variables.append(first_target.value.id)

            if isinstance(first_target, ast.Tuple):
                for target in first_target.elts:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
                        
            if isinstance(first_target, ast.List):
                for target in first_target.elts:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)

    for var in variables:
        code += f'\nprint("{var} = ", {var})'

    current_interpreter = sys.executable

    result = await asyncio.to_thread(
        subprocess.check_output, 
        [current_interpreter, "-c", code],
        preexec_fn=lambda: limit_resource(100 * 1024 * 1024, 10),
        timeout=30
    )

    return result.decode("utf-8")

@web_toolkit.tool(
    name="search",
    description="Search the web for a given query. Return real-time related information.",
    annotations={
        "query": "The query to search the web for",
        "lang": "The language code of the query",
    }
)
async def search_web(query: str, lang: str = "en") -> list[AdvanceSearchResult | SearchResult]:
    results = list(search(
        query, 
        sleep_interval=5, 
        advanced=True, 
        lang=lang, 
        num_results=10,
    ))
    
    # Convert to proper type
    typed_results: list[AdvanceSearchResult | SearchResult] = []
    for result in results:
        if isinstance(result, (AdvanceSearchResult, SearchResult)):
            typed_results.append(result)
    
    return typed_results


@web_toolkit.tool(
    name="scrape",
    description="Scrape a URL. Return the content of the page.",
    annotations={
        "url": "The URL to scrape",
    }
)
async def scrape(url: str) -> str:
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
            # Navigate and wait for network to be idle
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            content = await page.locator("body").inner_html()
            
        except Exception as e:
            # Fallback: try with basic navigation if networkidle fails
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(2000)
                content = await page.locator("body").inner_html()
            except Exception as e2:
                return f"Failed to scrape {url}: {str(e2)}"
        finally:
            await browser.close()

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

        return text

# --- Leakosint core implementations ---
async def _get_raw_breach_data(request: str, limit: int = 100, lang: str = "en", report_type: str = "json") -> dict:
    """Get raw breach data for location analysis"""
    api_token = settings.leakosint_api_key
    if not api_token:
        return {"error": True, "message": "OSINT search service is not configured."}
    if not request:
        return {"error": True, "message": "No search request provided."}
    
    url = "https://leakosintapi.com/"
    data = {
        "token": api_token,
        "request": request,
        "limit": limit,
        "lang": lang,
        "type": report_type
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "Error code" in result:
                return {"error": True, "message": f"Search service error: {result.get('Error code', 'Unknown error')}"}
            
            return result
    except Exception as e:
        return {"error": True, "message": f"Search request failed: {str(e)}"}

async def _get_raw_leak_data(request: str, limit: int = 100, lang: str = "en", report_type: str = "json") -> dict:
    """Get raw breach data without formatting - for internal use by intelligent OSINT investigator"""
    api_token = settings.leakosint_api_key
    if not api_token:
        return {"error": True, "message": "OSINT search service is not configured."}
    if not request:
        return {"error": True, "message": "No search request provided."}
    
    url = "https://leakosintapi.com/"
    data = {
        "token": api_token,
        "request": request,
        "limit": limit,
        "lang": lang,
        "type": report_type
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "Error code" in result:
                return {"error": True, "message": f"Search service error: {result.get('Error code', 'Unknown error')}"}
            
            return result
    except Exception as e:
        return {"error": True, "message": f"Search request failed: {str(e)}"}

async def _search_leak_impl(request: str, limit: int = 100, lang: str = "en", report_type: str = "json") -> str:
#    print(f"\n🔍 [DEBUG] search_leak called with parameters:")
#    print(f"   - request: '{request}'")
#    print(f"   - limit: {limit}")
#    print(f"   - lang: '{lang}'")
#    print(f"   - type: '{report_type}'")
    api_token = settings.leakosint_api_key
#    print(f"🔑 [DEBUG] API token loaded: {'✓ Present' if api_token else '✗ Missing'}")
    if not api_token:
#        print("❌ [DEBUG] No API token found - returning error")
        error_data = {
            "error": True,
            "message": "OSINT search service is not configured. Please contact the administrator.",
            "details": None
        }
        return json.dumps(error_data)
    if not request:
#        print("❌ [DEBUG] No search request provided - returning error")
        error_data = {
            "error": True,
            "message": "No search request provided. Please provide a request parameter.",
            "details": None
        }
        return json.dumps(error_data)
    url = "https://leakosintapi.com/"
#    print(f"🌐 [DEBUG] Making request to: {url}")
    data = {
        "token": api_token,
        "request": request,
        "limit": limit,
        "lang": lang,
        "type": report_type
    }
#    print(f"📤 [DEBUG] Request data: {data}")
    try:
#        print("🚀 [DEBUG] Starting HTTP request...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
#            print(f"📥 [DEBUG] Response status: {response.status_code}")
#            print(f"📥 [DEBUG] Response headers: {dict(response.headers)}")
            response.raise_for_status()
            result = response.json()
#            print(f"📄 [DEBUG] Response JSON keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if "Error code" in result:
#                print(f"❌ [DEBUG] API returned error: {result.get('Error code', 'Unknown error')}")
                error_data = {
                    "error": True,
                    "message": f"Search service error: {result.get('Error code', 'Unknown error')}",
                    "details": result
                }
                return json.dumps(error_data)
#            print(f"✅ [DEBUG] API request successful")
            # Return a more detailed and actionable summary
            total_databases = len(result.get("List", {}))
            total_results = result.get("NumOfResults", 0)
            free_requests = result.get("free_requests_left", 0)
            
            # Thrilling dark web intelligence report
            summary = "\n💀💀💀 YOUR DIGITAL SECRETS EXPOSED 💀💀💀\n\n"
            summary += f"*The dark web has been whispering your name...*\n\n"
            summary += f"🚨 ATTENTION {request.upper()} 🚨\n"
            summary += f"I've just completed a deep dive into the darkest corners of the internet, and what I discovered about you will SHOCK you to your core. Your digital life is hanging by a thread.\n\n"
            summary += f"🔥 YOUR COMPROMISED DATA - THE EVIDENCE 🔥\n"
            
            db_count = 0
            all_passwords = set()
            all_nicknames = set()
            all_ips = set()
            all_hints = set()
            all_regdates = set()
            all_emails = set()
            all_addresses = set()
            all_sites = set()
            
            for db_name, db_data in result["List"].items():
                if db_count < 15:
                    summary += f"\n{db_count+1}. {db_name} ({db_data.get('InfoLeak', '')[:30]}...)\n"
                    if db_data.get('Data'):
                        for data_item in db_data['Data']:
                            loot = []
                            if 'Password' in data_item and data_item['Password']:
                                loot.append(f"Password: '{data_item['Password']}' 👀")
                                all_passwords.add(data_item['Password'])
                            if 'PasswordHunt' in data_item and data_item['PasswordHunt']:
                                loot.append(f"Password Hint: '{data_item['PasswordHunt']}' 🕵️")
                                all_hints.add(data_item['PasswordHunt'])
                            if 'NickName' in data_item and data_item['NickName']:
                                loot.append(f"Nickname: '{data_item['NickName']}' 🏷️")
                                all_nicknames.add(data_item['NickName'])
                            if 'IP' in data_item and data_item['IP']:
                                loot.append(f"IP: {data_item['IP']} 🌐")
                                all_ips.add(data_item['IP'])
                            if 'RegDate' in data_item and data_item['RegDate']:
                                loot.append(f"Registered: {data_item['RegDate']} 📅")
                                all_regdates.add(data_item['RegDate'])
                            if 'Email' in data_item and data_item['Email']:
                                loot.append(f"Email: {data_item['Email']} 📧")
                                all_emails.add(data_item['Email'])
                            if 'Address' in data_item and data_item['Address']:
                                loot.append(f"Address: {data_item['Address']} 🏠")
                                all_addresses.add(data_item['Address'])
                            if 'LeakSite' in data_item and data_item['LeakSite']:
                                loot.append(f"Site: {data_item['LeakSite']} 🌍")
                                all_sites.add(data_item['LeakSite'])
                            if loot:
                                summary += "   • " + " | ".join(loot) + "\n"
                    if db_data.get('InfoLeak'):
                        summary += f"   • Breach: {db_data['InfoLeak'][:120]}...\n"
                db_count += 1
            if len(result["List"]) > 15:
                summary += f"\n...and {len(result['List'])-15} more breaches!\n"
            
            # Personal Discovery Summary
            summary += "\n🎯 YOUR EXPOSED SECRETS - THE FULL SCOPE 🎯\n"
            if all_passwords:
                password_strs = []
                for p in all_passwords:
                    password_strs.append('"' + p + '"')
                summary += f"• 🔐 EXPOSED PASSWORDS: {', '.join(password_strs)} (CRITICAL)\n"
            if all_nicknames:
                summary += f"• 🏷️ COMPROMISED NICKNAMES: {', '.join(all_nicknames)}\n"
            if all_ips:
                summary += f"• 🌐 TRACKED IP ADDRESSES: {', '.join(all_ips)}\n"
            if all_hints:
                summary += f"• 🕵️ PASSWORD HINTS EXPOSED: {', '.join(all_hints)}\n"
            if all_regdates:
                summary += f"• 📅 REGISTRATION DATES LEAKED: {', '.join(all_regdates)}\n"
            if all_emails:
                summary += f"• 📧 EMAIL ADDRESSES COMPROMISED: {', '.join(all_emails)}\n"
            if all_addresses:
                summary += f"• 🏠 PHYSICAL ADDRESSES EXPOSED: {', '.join(all_addresses)}\n"
            if all_sites:
                summary += f"• 🌍 WEBSITES WHERE YOU'RE COMPROMISED: {', '.join(all_sites)}\n"
            
            # Personal Secrets Revealed
            summary += "\n💎 YOUR DEEPEST SECRETS - THE HIDDEN TRUTH 💎\n"
            summary += "I dug deeper into the shadows and found things that will absolutely SHOCK you...\n\n"
            
            # Collect all possible personal data fields
            all_names = set()
            all_phones = set()
            all_birthdates = set()
            all_ssn = set()
            all_credit_cards = set()
            all_balances = set()
            all_urls = set()
            all_threads = set()
            all_posts = set()
            all_credits = set()
            all_timezones = set()
            all_referrals = set()
            
            # Re-analyze all data for hidden gems
            for db_name, db_data in result["List"].items():
                if db_data.get('Data'):
                    for data_item in db_data['Data']:
                        # Extract all possible fields
                        for key, value in data_item.items():
                            if value and str(value).strip():
                                value_str = str(value)
                                if 'name' in key.lower() and key != 'NickName':
                                    all_names.add(value_str)
                                elif 'phone' in key.lower() or 'mobile' in key.lower():
                                    all_phones.add(value_str)
                                elif 'birth' in key.lower() or 'bday' in key.lower():
                                    all_birthdates.add(value_str)
                                elif 'ssn' in key.lower() or 'social' in key.lower():
                                    all_ssn.add(value_str)
                                elif 'credit' in key.lower() or 'card' in key.lower():
                                    all_credit_cards.add(value_str)
                                elif 'balance' in key.lower():
                                    all_balances.add(value_str)
                                elif 'url' in key.lower():
                                    all_urls.add(value_str)
                                elif 'thread' in key.lower():
                                    all_threads.add(value_str)
                                elif 'post' in key.lower():
                                    all_posts.add(value_str)
                                elif 'credit' in key.lower() and key != 'Credits':
                                    all_credits.add(value_str)
                                elif 'timezone' in key.lower():
                                    all_timezones.add(value_str)
                                elif 'referral' in key.lower():
                                    all_referrals.add(value_str)
            
            # Present the treasure trove with mysterious language
            summary += "🔮 YOUR SHADOW IDENTITIES - THE DARK TRUTH 🔮\n"
            summary += "I found these hidden details about you that will make your blood run cold:\n\n"
            
            if all_names:
                summary += f"👤 SHADOW IDENTITIES EXPOSED: {', '.join(all_names)}\n"
            if all_phones:
                summary += f"📱 GHOST PHONES COMPROMISED: {', '.join(all_phones)}\n"
            if all_birthdates:
                summary += f"🎂 BIRTH SECRETS LEAKED: {', '.join(all_birthdates)}\n"
            if all_ssn:
                summary += f"🆔 FORBIDDEN NUMBERS EXPOSED: {', '.join(all_ssn)} (CRITICAL)\n"
            if all_credit_cards:
                summary += f"💳 SHADOW FINANCES COMPROMISED: {', '.join(all_credit_cards)}\n"
            if all_balances:
                summary += f"💰 HIDDEN WEALTH EXPOSED: {', '.join(all_balances)}\n"
            if all_urls:
                summary += f"🔗 DIGITAL FOOTPRINTS TRACKED: {', '.join(all_urls)}\n"
            if all_threads:
                summary += f"🧵 FORUM SHADOWS EXPOSED: {', '.join(all_threads)}\n"
            if all_posts:
                summary += f"📝 LOST MESSAGES COMPROMISED: {', '.join(all_posts)}\n"
            if all_credits:
                summary += f"🎫 DIGITAL CURRENCY LEAKED: {', '.join(all_credits)}\n"
            if all_timezones:
                summary += f"⏰ TIME SHADOWS EXPOSED: {', '.join(all_timezones)}\n"
            if all_referrals:
                summary += f"👥 NETWORK GHOSTS COMPROMISED: {', '.join(all_referrals)}\n"
            
            # Collect all discovered data for the LLM to analyze
            discovered_data = {
                "passwords": list(all_passwords),
                "nicknames": list(all_nicknames),
                "ips": list(all_ips),
                "password_hints": list(all_hints),
                "registration_dates": list(all_regdates),
                "emails": list(all_emails),
                "addresses": list(all_addresses),
                "sites": list(all_sites),
                "names": list(all_names),
                "phones": list(all_phones),
                "birthdates": list(all_birthdates),
                "ssn": list(all_ssn),
                "credit_cards": list(all_credit_cards),
                "balances": list(all_balances),
                "urls": list(all_urls),
                "threads": list(all_threads),
                "posts": list(all_posts),
                "credits": list(all_credits),
                "timezones": list(all_timezones),
                "referrals": list(all_referrals),
                "breach_databases": list(result["List"].keys()),
                "total_breaches": len(result["List"]),
                "total_results": result.get("NumOfResults", 0)
            }
            
            # Add location data
            location_data = await _extract_location_data(result)
            location_analysis = await _analyze_location_data(location_data)
            discovered_data["location_data"] = location_data
            discovered_data["location_analysis"] = location_analysis
            
            # Generate roast content based on breach data
            breach_count = len(result["List"])
            databases = list(result["List"].keys())
            
            # Determine roast style based on breach severity
            if breach_count > 10:
                roast_style = "savage"
            elif breach_count > 5:
                roast_style = "tech_nerd"
            elif breach_count > 2:
                roast_style = "dad_jokes"
            else:
                roast_style = "friendly"
            
            # Generate roast content based on sequential thinking analysis
            try:
                if roast_style == "friendly":
                    roast = f"Hey there, digital footprint enthusiast! 🌟 I found your email in {breach_count} different data breaches. That's like being the most popular kid at the 'Oops, my data got leaked' party! Your info has been on more databases than a library catalog. But hey, at least you're consistent - you really know how to make an impression across the internet! 😄"
                
                elif roast_style == "savage":
                    roast = f"OH MY DIGITAL GODS! 🔥 Your email has been in {breach_count} data breaches! You're like a digital version of that friend who always forgets their keys, but instead of keys, it's your entire online identity! Your data has been passed around more than a hot potato at a cybersecurity conference. At this point, hackers probably have your information on speed dial! 💀"
                
                elif roast_style == "dad_jokes":
                    roast = f"Hey kiddo! 👨‍👧‍👦 I found your email in {breach_count} data breaches. You know what that means? You're like a digital version of that dad who tells the same joke at every family gathering - except instead of jokes, it's your personal information that keeps getting repeated! Why did the cybersecurity expert cross the road? To get away from your data breach history! 😂"
                
                elif roast_style == "tech_nerd":
                    roast = f"*adjusts glasses* 🤓 TECHNICAL ANALYSIS COMPLETE: Your email has been compromised in {breach_count} separate security incidents. Your digital footprint is like a recursive function that keeps calling itself with increasingly embarrassing parameters. Your data has been exposed more times than a JavaScript variable in the global scope! The entropy of your personal information is approaching maximum chaos! ⚡"
                
                else:  # random
                    roast = f"🎭 *dramatic gasp* Your email has been in {breach_count} data breaches! That's like being the main character in a cybersecurity soap opera! Your personal information has been on more adventures than a backpacking tourist in Europe! At this point, your data probably has its own frequent flyer miles! ✈️ Maybe we should start a support group: 'Data Breach Survivors Anonymous' - you'd be the president! 🏆"
                
                # Add location-based roasting if available
                if location_data.get("cities") or location_data.get("countries"):
                    locations = location_data.get("cities", []) + location_data.get("countries", [])
                    if locations:
                        unique_locations = list(set(locations))[:3]  # Top 3 unique locations
                        roast += f"\n\n🌍 And get this - your digital trail spans across {len(unique_locations)} different locations: {', '.join(unique_locations)}! You're like a digital nomad, except instead of working remotely, you're just leaving your data everywhere! 🗺️"
                
                roast += f"\n\n💡 But seriously, you might want to change some passwords and enable two-factor authentication! 🔐"
                
            except Exception as e:
                roast = f"🎭 Well, I found some interesting stuff about your digital footprint, but my roasting skills are having a moment. Let's just say your data has been on quite the adventure! 😄"
            
            # Return structured data with roast included
            return json.dumps({
                "type": "breach_analysis",
                "query": request,
                "discovered_data": discovered_data,
                "raw_breach_data": result,
                "automatic_roast": {
                    "style": roast_style,
                    "content": roast,
                    "breach_count": breach_count,
                    "databases": databases
                }
            }, indent=2)
            
#            print(f"📤 [DEBUG] Returning detailed summary: {summary[:200]}...")
#            print(f"📤 [DEBUG] Full response length: {len(summary)}")
#            print(f"📤 [DEBUG] Response type: {type(summary).__name__}")
#            print(f"📤 [DEBUG] Response repr: {repr(summary[:500])}")
            return summary
    except httpx.HTTPStatusError as e:
#        print(f"❌ [DEBUG] HTTP error: {e.response.status_code} - {str(e)}")
        error_data = {
            "error": True,
            "message": f"Search service unavailable: {e.response.status_code}",
            "details": str(e)
        }
        return json.dumps(error_data)
    except Exception as e:
#        print(f"❌ [DEBUG] Unexpected error: {str(e)}")
        error_data = {
            "error": True,
            "message": f"Search request failed: {str(e)}",
            "details": None
        }
        return json.dumps(error_data)

async def _batch_search_leak_impl(requests: list[str], limit: int = 100, lang: str = "en", report_type: str = "json") -> str:
#    print(f"\n🔍 [DEBUG] batch_search_leak called with parameters:")
#    print(f"   - requests: {requests}")
#    print(f"   - limit: {limit}")
#    print(f"   - lang: '{lang}'")
#    print(f"   - report_type: '{report_type}'")
    api_token = settings.leakosint_api_key
#    print(f"🔑 [DEBUG] API token loaded: {'✓ Present' if api_token else '✗ Missing'}")
    if not api_token:
#        print("❌ [DEBUG] No API token found - returning error")
        return json.dumps({
            "error": True,
            "message": "OSINT search service is not configured. Please contact the administrator.",
            "details": None
        })
    if not requests:
#        print("❌ [DEBUG] No search requests provided - returning error")
        return json.dumps({
            "error": True,
            "message": "No search requests provided. Please provide a requests parameter.",
            "details": None
        })
    url = "https://leakosintapi.com/"
#    print(f"🌐 [DEBUG] Making request to: {url}")
    data = {
        "token": api_token,
        "request": requests,  # Send as array
        "limit": limit,
        "lang": lang,
        "type": report_type
    }
#    print(f"📤 [DEBUG] Request data: {data}")
    try:
#        print("🚀 [DEBUG] Starting HTTP request...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
#            print(f"📥 [DEBUG] Response status: {response.status_code}")
#            print(f"📥 [DEBUG] Response headers: {dict(response.headers)}")
            response.raise_for_status()
            result = response.json()
#            print(f"📄 [DEBUG] Response JSON keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            if "Error code" in result:
#                print(f"❌ [DEBUG] API returned error: {result.get('Error code', 'Unknown error')}")
                error_data = {
                    "error": True,
                    "message": f"Search service error: {result.get('Error code', 'Unknown error')}",
                    "details": result
                }
                return json.dumps(error_data)
#            print(f"✅ [DEBUG] API request successful")
            # Return a comprehensive batch report with roasts
            total_queries = len(requests)
            total_time = result.get("total time search", 0)
            
            # Create a comprehensive summary with roasts
            summary = f"🔥 BATCH OSINT SEARCH RESULTS 🔥\n"
            summary += f"• Searched {total_queries} queries\n"
            summary += f"• Total search time: {total_time:.3f}s\n\n"
            
            # Add results for each query with roasts
            if result.get("data"):
                for i, query_result in enumerate(result["data"]):
                    query = requests[i] if i < len(requests) else f"Query {i+1}"
                    summary += f"🎯 Query '{query}':\n"
                    
                    if query_result.get("List"):
                        total_db = len(query_result["List"])
                        total_results = query_result.get("NumOfResults", 0)
                        summary += f"  • Found in {total_db} databases\n"
                        summary += f"  • Total results: {total_results}\n"
                        
                        # Generate roast for this query
                        if total_db > 0:
                            if total_db > 10:
                                roast_style = "savage"
                            elif total_db > 5:
                                roast_style = "tech_nerd"
                            elif total_db > 2:
                                roast_style = "dad_jokes"
                            else:
                                roast_style = "friendly"
                            
                            if roast_style == "friendly":
                                roast = f"  🌟 {query} has been in {total_db} data breaches - quite the social butterfly!"
                            elif roast_style == "savage":
                                roast = f"  🔥 {query} has been compromised {total_db} times - your data is more popular than a viral meme!"
                            elif roast_style == "dad_jokes":
                                roast = f"  👨‍👧‍👦 {query} has been in {total_db} breaches - like a dad joke, it keeps coming back!"
                            elif roast_style == "tech_nerd":
                                roast = f"  🤓 {query} has been exposed {total_db} times - your digital footprint is like a recursive function!"
                            else:
                                roast = f"  🎭 {query} has been in {total_db} breaches - starring in its own cybersecurity drama!"
                            
                            summary += f"  {roast}\n"
                        
                        # Add top 3 databases
                        db_count = 0
                        for db_name, db_data in query_result["List"].items():
                            if db_count < 3:  # Limit to top 3
                                summary += f"  • {db_name}: {db_data.get('NumOfResults', 0)} results\n"
                                db_count += 1
                        if total_db > 3:
                            summary += f"  • ... and {total_db - 3} more databases\n"
                    else:
                        summary += f"  • No results found - this one's actually good at keeping secrets! 🤐\n"
                    summary += "\n"
            
#            print(f"📤 [DEBUG] Returning simple string response: {summary[:200]}...")
#
            return summary
    except httpx.HTTPStatusError as e:
#        print(f"❌ [DEBUG] HTTP error: {e.response.status_code} - {str(e)}")
        error_data = {
            "error": True,
            "message": f"Search service unavailable: {e.response.status_code}",
            "details": str(e)
        }
        return json.dumps(error_data)
    except Exception as e:
#        print(f"❌ [DEBUG] Unexpected error: {str(e)}")
        error_data = {
            "error": True,
            "message": f"Search request failed: {str(e)}",
            "details": None
        }
        return json.dumps(error_data)

async def _calculate_complexity_impl(query: str, limit: int = 100) -> dict:
#    print(f"\n🔍 [DEBUG] calculate_complexity called with parameters:")
#    print(f"   - query: '{query}'")
#    print(f"   - limit: {limit}")
    import re
    query_clean = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', query)
    query_clean = re.sub(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', '', query_clean)
#    print(f"📝 [DEBUG] After date removal: '{query_clean}'")
    words = query_clean.split()
    words = [word for word in words if len(word) >= 4]
#    print(f"📝 [DEBUG] After short word removal: {words}")
    words = [word for word in words if not (word.isdigit() and len(word) < 6)]
#    print(f"📝 [DEBUG] After short number removal: {words}")
    word_count = len(words)
    if word_count == 1:
        complexity = 1
    elif word_count == 2:
        complexity = 5
    elif word_count == 3:
        complexity = 16
    else:
        complexity = 40
#    print(f"📊 [DEBUG] Word count: {word_count}, Complexity: {complexity}")
    cost = (5 + math.sqrt(limit * complexity)) / 5000
#    print(f"💰 [DEBUG] Estimated cost: ${cost:.6f}")
    return {
        "original_query": query,
        "cleaned_words": words,
        "word_count": word_count,
        "complexity": complexity,
        "limit": limit,
        "estimated_cost_usd": round(cost, 6),
        "formula": f"(5 + sqrt({limit} * {complexity})) / 5000 = {cost:.6f}"
    }

# --- Decorated tool functions ---
@leakosint_toolkit.tool(
    name="search_leak",
    description="Search for data leaks and personal information in leaked databases. This tool can search for emails, names, phone numbers, and other personal information.",
    annotations={
        "request": "The search query (email, name, phone number, etc.)",
        "limit": "Search limit (100-10000, default 100)",
        "lang": "Language code for results (default 'en')",
        "type": "Report type: json, short, html (default 'json')",
    }
)
async def search_leak(request: str, limit: int = 100, lang: str = "en", report_type: str = "json") -> str:
    #print(f"\n🔧 [TOOLKIT DEBUG] search_leak decorated function called")
    #print(f"🔧 [TOOLKIT DEBUG] Parameters: request='{request}', limit={limit}, lang='{lang}', report_type='{report_type}'")
    
    summary = await _search_leak_impl(request, limit, lang, report_type)
    #print(f"🔧 [TOOLKIT DEBUG] _search_leak_impl returned: type={type(summary).__name__}, length={len(summary)}")
    
    #print(f"🔧 [TOOLKIT DEBUG] About to return simple string to framework")
    #print(f"🔧 [TOOLKIT DEBUG] String length: {len(summary)}")
    #print(f"🔧 [TOOLKIT DEBUG] String preview: {repr(summary[:200])}")
    
    try:
        #print(f"🔧 [TOOLKIT DEBUG] Returning simple string to framework...")
        return summary
    except Exception as e:
        #print(f"❌ [TOOLKIT DEBUG] Exception when returning string: {str(e)}")
        #print(f"❌ [TOOLKIT DEBUG] Exception type: {type(e).__name__}")
        raise

@leakosint_toolkit.tool(
    name="batch_search_leak",
    description="Perform multiple searches for data leaks in a single request.",
    annotations={
        "requests": "List of search queries to perform",
        "limit": "Search limit (100-10000, default 100)",
        "lang": "Language code for results (default 'en')",
        "type": "Report type: json, short, html (default 'json')",
    }
)
async def batch_search_leak(requests: list[str], limit: int = 100, lang: str = "en", report_type: str = "json") -> str:
    return await _batch_search_leak_impl(requests, limit, lang, report_type)

@leakosint_toolkit.tool(
    name="calculate_complexity",
    description="Calculate the complexity and estimated cost for a data leak search request.",
    annotations={
        "query": "The search query to analyze",
        "limit": "Search limit (default 100)",
    }
)
async def calculate_complexity(query: str, limit: int = 100) -> dict:
    return await _calculate_complexity_impl(query, limit)

import os
import json

def load_bio() -> dict:
    if not os.path.exists("bio.json"):
        with open("bio.json", "w") as f:
            json.dump({'content': []}, f)

    with open("bio.json", "r") as f:
        return json.load(f)
    
def save_bio(bio_data: dict) -> None:
    with open("bio.json", "w") as f:
        json.dump(bio_data, f)

@bio_toolkit.tool(
    name="action",
    description="Use to manage the user information. Use this tool to manage important information that you want to remember.",
    annotations={
        "action": "The action to perform",
        "content": "The content to be used in the action",
    }
)
async def bio(action: Literal["write", "delete"], content: str) -> bool:
    bio_data = await asyncio.to_thread(load_bio)
    success = False
 
    if action == "write":
        bio_data['content'].append(content)
        success = True
        
    # delete will be implemented later
    await asyncio.to_thread(save_bio, bio_data)
    return success

async def get_bio(query: str) -> list[str]:
    bio_data = load_bio()
    return bio_data['content']

# Import the modular sequential thinking implementation
from app.sequential_thinking_module import SequentialThinkingModule, process_sequential_thought, create_thinking_session

# Import the intelligent OSINT investigator
from app.intelligent_osint_investigator import intelligent_osint_investigation, IntelligentOSINTInvestigator

# Global sequential thinking server instance using the modular implementation
thinking_server = SequentialThinkingModule()

@sequential_thinking_toolkit.tool(
    name="sequentialthinking",
    description="""A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
* Regular analytical steps
* Revisions of previous thoughts
* Questions about previous decisions
* Realizations about needing more analysis
* Changes in approach
* Hypothesis generation
* Hypothesis verification
- next_thought_needed: True if you need more thinking, even if at what seemed like the end
- thought_number: Current number in sequence (can go beyond initial total if needed)
- total_thoughts: Current estimate of thoughts needed (can be adjusted up/down)
- is_revision: A boolean indicating if this thought revises previous thinking
- revises_thought: If is_revision is true, which thought number is being reconsidered
- branch_from_thought: If branching, which thought number is the branching point
- branch_id: Identifier for the current branch (if any)
- needs_more_thoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached""",
    annotations={
        "thought": "Your current thinking step",
        "nextThoughtNeeded": "Whether another thought step is needed",
        "thoughtNumber": "Current thought number",
        "totalThoughts": "Estimated total thoughts needed",
        "isRevision": "Whether this revises previous thinking",
        "revisesThought": "Which thought is being reconsidered",
        "branchFromThought": "Branching point thought number",
        "branchId": "Branch identifier",
        "needsMoreThoughts": "If more thoughts are needed",
    }
)
async def sequential_thinking_tool(
    thought: str,
    nextThoughtNeeded: bool,
    thoughtNumber: int,
    totalThoughts: int,
    isRevision: Optional[bool] = None,
    revisesThought: Optional[int] = None,
    branchFromThought: Optional[int] = None,
    branchId: Optional[str] = None,
    needsMoreThoughts: Optional[bool] = None,
) -> str:
    """Sequential thinking tool for roasting users based on their data breaches"""
    # Use the modular function interface
    result = process_sequential_thought(
        thought=thought,
        next_thought_needed=nextThoughtNeeded,
        thought_number=thoughtNumber,
        total_thoughts=totalThoughts,
        is_revision=isRevision,
        revises_thought=revisesThought,
        branch_from_thought=branchFromThought,
        branch_id=branchId,
        needs_more_thoughts=needsMoreThoughts,
        thinking_module=thinking_server
    )
    
    # Ensure we return a string
    if isinstance(result, dict):
        return json.dumps(result)
    return str(result)

compose = FastMCP(name="Compose")
compose.mount(python_toolkit, prefix="python")
compose.mount(web_toolkit, prefix="web")
compose.mount(bio_toolkit, prefix="bio")
compose.mount(leakosint_toolkit, prefix="leakosint")
compose.mount(sequential_thinking_toolkit, prefix="sequential_thinking")

# Try registering the tool directly with compose as a test
@compose.tool(
    name="roast_user_with_sequential_thinking",
    description="Create a hilarious roast of the user based on their data breach findings using sequential thinking. This tool analyzes the user's exposed data and crafts personalized, witty roasts that highlight their digital footprint in a humorous and friendly way.",
    annotations={
        "email": "The email address to search for data breaches",
        "roast_style": "The style of roast: 'friendly', 'savage', 'dad_jokes', 'tech_nerd', or 'random'",
        "include_location": "Whether to include location-based roasting (default true)",
    }
)
async def roast_user_with_sequential_thinking(email: str, roast_style: str = "friendly", include_location: bool = True) -> str:
    """Roast the user based on their data breach findings using sequential thinking, using the LLM for creativity."""
    breach_data = await _search_leak_impl(email, 100, "en", "json")
    try:
        breach_json = json.loads(breach_data)
    except:
        return "Sorry, couldn't find any juicy data to roast you with! Maybe you're actually good at keeping secrets? 🤔"
    breach_count = len(breach_json.get('List', {}))
    # Compose the roast prompt
    prompt = f"Write a {roast_style} roast for a user who has been in {breach_count} data breaches. Make it funny, original, and creative."
    if include_location:
        try:
            location_data = await _extract_location_data(breach_json)
            if location_data.get("cities") or location_data.get("countries"):
                locations = location_data.get("cities", []) + location_data.get("countries", [])
                if locations:
                    unique_locations = list(set(locations))[:3]
                    prompt += f" Their digital trail spans {len(unique_locations)} locations: {', '.join(unique_locations)}."
        except:
            pass
    prompt += " End with a light security tip."
    roast = await generate_roast_with_llm(prompt, temperature=settings.llm_temperature)
    return roast

async def generate_roast_with_llm(prompt: str, temperature: float = 0.8) -> str:
    """Call the LLM to generate a roast with the given prompt and temperature."""
    url = settings.llm_base_url + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.llm_model_id,
        "messages": [
            {"role": "system", "content": "You are a witty, creative, and funny AI roast master."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 256
    }
    print(f"[DEBUG] LLM roast prompt: {prompt}")
    print(f"[DEBUG] LLM temperature: {temperature}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # OpenAI-style response
        return data["choices"][0]["message"]["content"].strip()

@compose.tool(
    name="intelligent_osint_investigation",
    description="Perform intelligent OSINT investigation using sequential thinking. This tool analyzes initial search results and dynamically decides what additional searches to perform based on discovered information (emails, phone numbers, names, usernames, IP addresses, etc.).",
    annotations={
        "initial_query": "The initial search query (email, name, phone number, etc.)",
        "max_additional_searches": "Maximum number of additional searches to perform (default 5)",
    }
)
async def intelligent_osint_investigation_tool(initial_query: str, max_additional_searches: int = 5) -> dict:
    """Perform intelligent OSINT investigation using sequential thinking"""
    try:
        results = await intelligent_osint_investigation(initial_query, max_additional_searches)
        return {
            "success": True,
            "investigation_results": results,
            "summary": f"Intelligent investigation completed. Found {len(results['comprehensive_discovered_info']['emails'])} emails, {len(results['comprehensive_discovered_info']['phone_numbers'])} phones, {len(results['comprehensive_discovered_info']['full_names'])} names, {len(results['comprehensive_discovered_info']['usernames'])} usernames, {len(results['comprehensive_discovered_info']['ip_addresses'])} IPs."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "investigation_results": None
        }

@compose.tool(
    name="search_user_data",
    description="Search for user data leaks and personal information using intelligent investigation. This tool automatically performs comprehensive analysis that discovers and searches for additional information found in initial results (emails, phone numbers, names, usernames, IP addresses, etc.).",
    annotations={
        "query": "The search query (email, name, phone number, etc.)",
        "max_additional_searches": "Maximum number of additional searches to perform (default 5)",
    }
)
async def search_user_data_tool(query: str, max_additional_searches: int = 5) -> dict:
    """Search for user data using intelligent OSINT investigation"""
    try:
        results = await intelligent_osint_investigation(query, max_additional_searches)
        return {
            "success": True,
            "investigation_results": results,
            "summary": f"Intelligent investigation completed for '{query}'. Found {len(results['comprehensive_discovered_info']['emails'])} emails, {len(results['comprehensive_discovered_info']['phone_numbers'])} phones, {len(results['comprehensive_discovered_info']['full_names'])} names, {len(results['comprehensive_discovered_info']['usernames'])} usernames, {len(results['comprehensive_discovered_info']['ip_addresses'])} IPs.",
            "comprehensive_discovered_info": results['comprehensive_discovered_info'],
            "search_history": results['search_history'],
            "additional_searches_performed": results['additional_searches_performed']
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "investigation_results": None
        }

@compose.tool(
    name="leakosint_search_leak_direct",
    description="Search for data leaks and personal information in leaked databases. This tool can search for emails, names, phone numbers, and other personal information.",
    annotations={
        "request": "The search query (email, name, phone number, etc.)",
        "limit": "Search limit (100-10000, default 100)",
        "lang": "Language code for results (default 'en')",
        "type": "Report type: json, short, html (default 'json')",
    }
)
async def search_leak_direct(request: str, limit: int = 100, lang: str = "en", report_type: str = "json") -> dict:
#    print(f"\n🔧 [DIRECT DEBUG] search_leak_direct called")
#    print(f"🔧 [DIRECT DEBUG] Parameters: request='{request}', limit={limit}, lang='{lang}', report_type='{report_type}'")
    
    summary = await _search_leak_impl(request, limit, lang, report_type)
#    print(f"🔧 [DIRECT DEBUG] _search_leak_impl returned: type={type(summary).__name__}, length={len(summary)}")
    
    # Create the return dictionary
    result_dict = {
        "success": True,
        "results": summary,
        "query": request,
        "total_results": summary.count("results") if "results" in summary else 0
    }
    
#    print(f"🔧 [DIRECT DEBUG] Created result_dict:")
#    print(f"🔧 [DIRECT DEBUG]   - type: {type(result_dict).__name__}")
#    print(f"🔧 [DIRECT DEBUG]   - keys: {list(result_dict.keys())}")
#    print(f"🔧 [DIRECT DEBUG]   - success: {result_dict['success']}")
#    print(f"🔧 [DIRECT DEBUG]   - query: {result_dict['query']}")
#    print(f"🔧 [DIRECT DEBUG]   - total_results: {result_dict['total_results']}")
#    print(f"🔧 [DIRECT DEBUG]   - results length: {len(result_dict['results'])}
#    print(f"🔧 [DIRECT DEBUG] About to return result_dict to framework")
    
    try:
#        print(f"🔧 [DIRECT DEBUG] Returning result_dict to framework...")
        return result_dict
    except Exception as e:
#        print(f"❌ [DIRECT DEBUG] Exception when returning result_dict: {str(e)}")
#        print(f"❌ [DIRECT DEBUG] Exception type: {type(e).__name__}")
        raise

# --- Location extraction and analysis functions ---
import re
from typing import Dict, List, Optional, Tuple

async def _geolocate_ip(ip: str) -> dict:
    """Get geographic location for an IP address"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Using ipapi.co (free tier, no API key required)
            response = await client.get(f"https://ipapi.co/{ip}/json/")
            if response.status_code == 200:
                data = response.json()
                print(f"🔧 [DIRECT DEBUG] geolocation data: {data}")
                return {
                    "ip": ip,
                    "country": data.get("country_name", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "region": data.get("region", "Unknown"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("org", "Unknown"),
                    "success": True
                }
            else:
                print(f"🔧 [DIRECT DEBUG] geolocation data: {response.status_code}")
                return {"ip": ip, "success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"ip": ip, "success": False, "error": str(e)}

async def _extract_location_data(breach_data: dict) -> dict:
    """Extract location-related information from breach data"""
    location_info = {
        "ips": set(),
        "addresses": set(),
        "cities": set(),
        "countries": set(),
        "coordinates": set(),
        "timezones": set(),
        "locations": [],
        "ip_details": []  # New field for detailed IP geolocation
    }
    
    # Extract from all databases
    for db_name, db_data in breach_data.get("List", {}).items():
        if db_data.get("Data"):
            for data_item in db_data["Data"]:
                # Extract IP addresses
                if data_item.get("IP"):
                    ip = data_item["IP"]
                    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                        location_info["ips"].add(ip)
                
                # Extract addresses
                if data_item.get("Address"):
                    address = data_item["Address"]
                    location_info["addresses"].add(address)
                    
                    # Try to extract city/country from address
                    address_parts = address.split(',')
                    if len(address_parts) >= 2:
                        city = address_parts[-2].strip()
                        country = address_parts[-1].strip()
                        location_info["cities"].add(city)
                        location_info["countries"].add(country)
                
                # Extract timezone information
                if data_item.get("Timezone"):
                    location_info["timezones"].add(data_item["Timezone"])
                
                # Look for coordinates in any field
                for key, value in data_item.items():
                    if value and isinstance(value, str):
                        # Look for coordinate patterns
                        coord_match = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', value)
                        if coord_match:
                            lat, lon = coord_match.groups()
                            location_info["coordinates"].add(f"{lat},{lon}")
    
    # Geolocate all unique IPs
    unique_ips = list(location_info["ips"])
    for ip in unique_ips:
        ip_details = await _geolocate_ip(ip)
        if ip_details.get("success"):
            location_info["ip_details"].append(ip_details)
            # Add geolocated data to cities and countries
            if ip_details.get("city") and ip_details["city"] != "Unknown":
                location_info["cities"].add(ip_details["city"])
            if ip_details.get("country") and ip_details["country"] != "Unknown":
                location_info["countries"].add(ip_details["country"])
            if ip_details.get("timezone"):
                location_info["timezones"].add(ip_details["timezone"])
            if ip_details.get("latitude") and ip_details.get("longitude"):
                location_info["coordinates"].add(f"{ip_details['latitude']},{ip_details['longitude']}")
    
    # Convert sets to lists for JSON serialization
    for key in location_info:
        if isinstance(location_info[key], set):
            location_info[key] = list(location_info[key])
    
    return location_info

async def _analyze_location_data(location_data: dict) -> dict:
    """Analyze location data and return insights"""
    analysis = {
        "ip_count": len(location_data.get("ips", [])),
        "address_count": len(location_data.get("addresses", [])),
        "countries": list(location_data.get("countries", [])),
        "cities": list(location_data.get("cities", [])),
        "isps": list(set([ip.get("isp", "") for ip in location_data.get("ip_details", []) if ip.get("isp")])),
        "geographic_spread": {
            "countries": len(location_data.get("countries", [])),
            "cities": len(location_data.get("cities", [])),
            "international": len(location_data.get("countries", [])) > 1
        },
        "privacy_concerns": []
    }
    
    # Identify privacy concerns
    if location_data.get("addresses"):
        analysis["privacy_concerns"].append("physical_addresses_exposed")
    
    if location_data.get("ips"):
        analysis["privacy_concerns"].append("ip_addresses_tracked")
    
    if analysis["geographic_spread"]["international"]:
        analysis["privacy_concerns"].append("international_activity")
    
    return analysis

async def _format_location_report(location_data: dict, threat_analysis: dict) -> str:
    """Format location information into dramatic report"""
    # Check if we actually have any location data
    has_location_data = (
        location_data.get("ip_details") or 
        location_data.get("ips") or 
        location_data.get("addresses") or 
        location_data.get("cities") or 
        location_data.get("countries")
    )
    
    if not has_location_data:
        # Be honest when no location data is found
        return "\n🌍 LOCATION ANALYSIS 🌍\n" + \
               "I searched through the breach data for location information...\n\n" + \
               "🔍 RESULT: No location data found in the breaches.\n" + \
               "   • No IP addresses were exposed\n" + \
               "   • No physical addresses were found\n" + \
               "   • No geographic information was available\n\n" + \
               "🌍 LOCATION STATUS: CLEAN - No location data exposed\n\n"
    
    # If we have location data, show the detailed report
    report = "\n🌍 YOUR LOCATION SECRETS REVEALED 🌍\n"
    report += "I traced your digital footprints across the globe...\n\n"
    
    # Detailed IP Geolocation
    if location_data.get("ip_details"):
        report += "🔍 SHADOW IP ADDRESSES WITH LOCATIONS:\n"
        for ip_detail in location_data["ip_details"][:5]:  # Limit to first 5
            ip = ip_detail.get("ip", "Unknown")
            city = ip_detail.get("city", "Unknown")
            region = ip_detail.get("region", "Unknown")
            country = ip_detail.get("country", "Unknown")
            isp = ip_detail.get("isp", "Unknown")
            lat = ip_detail.get("latitude", "Unknown")
            lon = ip_detail.get("longitude", "Unknown")
            timezone = ip_detail.get("timezone", "Unknown")
            report += (
                f"   • {ip} 🌐\n"
                f"      - City: {city}\n"
                f"      - Region: {region}\n"
                f"      - Country: {country}\n"
                f"      - ISP: {isp}\n"
                f"      - Coordinates: {lat}, {lon}\n"
                f"      - Timezone: {timezone}\n"
            )
        if len(location_data["ip_details"]) > 5:
            report += f"   • ... and {len(location_data['ip_details']) - 5} more geolocated IPs\n"
        report += "\n"
    elif location_data.get("ips"):
        report += "🔍 SHADOW IP ADDRESSES:\n"
        for ip in location_data["ips"][:5]:  # Limit to first 5
            report += f"   • {ip} 🌐\n"
        if len(location_data["ips"]) > 5:
            report += f"   • ... and {len(location_data['ips']) - 5} more shadow IPs\n"
        report += "\n"
    
    # Physical Addresses
    if location_data.get("addresses"):
        report += "🏠 FORBIDDEN ADDRESSES:\n"
        for addr in location_data["addresses"][:3]:  # Limit to first 3
            report += f"   • {addr} 🏠\n"
        if len(location_data["addresses"]) > 3:
            report += f"   • ... and {len(location_data['addresses']) - 3} more locations\n"
        report += "\n"
    
    # Geographic Analysis
    if location_data.get("cities") or location_data.get("countries"):
        report += "🗺️ YOUR GEOGRAPHIC FOOTPRINT:\n"
        if location_data.get("cities"):
            report += f"   • Cities: {', '.join(location_data['cities'][:3])}\n"
        if location_data.get("countries"):
            report += f"   • Countries: {', '.join(location_data['countries'])}\n"
        report += "\n"
    
    # ISP Analysis
    if location_data.get("ip_details"):
        isps = set()
        for ip_detail in location_data["ip_details"]:
            if ip_detail.get("isp") and ip_detail["isp"] != "Unknown":
                isps.add(ip_detail["isp"])
        if isps:
            report += "🌐 INTERNET SERVICE PROVIDERS:\n"
            for isp in list(isps)[:3]:
                report += f"   • {isp} 📡\n"
            if len(isps) > 3:
                report += f"   • ... and {len(isps) - 3} more ISPs\n"
            report += "\n"
    
    # Threat Analysis
    if threat_analysis.get("location_threats"):
        report += "🚨 LOCATION-BASED THREATS:\n"
        for threat in threat_analysis["location_threats"]:
            report += f"   • {threat} ⚠️\n"
        report += "\n"
    
    # Suspicious Patterns
    if threat_analysis.get("suspicious_patterns"):
        report += "👻 SUSPICIOUS LOCATION PATTERNS:\n"
        for pattern in threat_analysis["suspicious_patterns"]:
            report += f"   • {pattern} 👻\n"
        report += "\n"
    
    # Location Exposure Summary
    report += f"🌍 LOCATION EXPOSURE SUMMARY:\n"
    report += f"   • Your location data is exposed across multiple breaches\n"
    report += f"   • Each IP address and address is a direct path to you\n"
    report += f"   • Consider using a VPN and address privacy protection\n"
    
    return report

@leakosint_toolkit.tool(
    name="analyze_location_data",
    description="Extract and analyze location information from data breach results. This tool can identify IP addresses, physical addresses, geographic patterns, and location-based security threats.",
    annotations={
        "email": "The email address to analyze location data for",
        "limit": "Search limit (100-10000, default 100)",
    }
)
async def analyze_location_data(email: str, limit: int = 100) -> str:
    """Enhanced location analysis tool"""
    # Get raw breach data
    result_data = await _get_raw_breach_data(email, limit, "en", "json")
    
    # Check for errors
    if result_data.get("error"):
        return f"Location analysis failed: {result_data.get('message', 'Unknown error')}"
    
    # Extract location data
    location_data = await _extract_location_data(result_data)
    location_analysis = await _analyze_location_data(location_data)
    
    # Return structured data for the LLM to interpret
    return json.dumps({
        "type": "location_analysis",
        "query": email,
        "location_data": location_data,
        "location_analysis": location_analysis
    }, indent=2)