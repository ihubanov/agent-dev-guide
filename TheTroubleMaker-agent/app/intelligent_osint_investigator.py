#!/usr/bin/env python3

"""
Intelligent OSINT Investigator using Sequential Thinking
This module uses sequential thinking to dynamically decide what additional OSINT searches
to perform based on discovered information from initial searches.
"""

import json
import re
import asyncio
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass
import logging

from app.sequential_thinking_module import SequentialThinkingModule, process_sequential_thought

logger = logging.getLogger(__name__)

# Import required modules for API calls
import httpx
from app.configs import settings


@dataclass
class DiscoveredInfo:
    """Data structure for discovered information during OSINT investigation"""
    emails: Optional[Set[str]] = None
    phone_numbers: Optional[Set[str]] = None
    full_names: Optional[Set[str]] = None
    usernames: Optional[Set[str]] = None
    ip_addresses: Optional[Set[str]] = None
    addresses: Optional[Set[str]] = None
    passwords: Optional[Set[str]] = None
    nicknames: Optional[Set[str]] = None
    social_media: Optional[Set[str]] = None
    websites: Optional[Set[str]] = None
    geolocations: Optional[Dict[str, dict]] = None
    
    def __post_init__(self):
        if self.emails is None:
            self.emails = set()
        if self.phone_numbers is None:
            self.phone_numbers = set()
        if self.full_names is None:
            self.full_names = set()
        if self.usernames is None:
            self.usernames = set()
        if self.ip_addresses is None:
            self.ip_addresses = set()
        if self.addresses is None:
            self.addresses = set()
        if self.passwords is None:
            self.passwords = set()
        if self.nicknames is None:
            self.nicknames = set()
        if self.social_media is None:
            self.social_media = set()
        if self.websites is None:
            self.websites = set()
        if self.geolocations is None:
            self.geolocations = {}


class IntelligentOSINTInvestigator:
    """
    Intelligent OSINT investigator that uses sequential thinking to dynamically
    decide what additional searches to perform based on discovered information.
    """
    
    def __init__(self):
        self.thinking_module = SequentialThinkingModule()
        # self.discovered_info = DiscoveredInfo() # Unused instance variable
        self.search_history = []
        # self.investigation_results = {} # Unused instance variable
        
    # def _extract_emails(self, text: str) -> Set[str]: # Unused method
    #     """Extract email addresses from text"""
    #     email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    #     return set(re.findall(email_pattern, text))
    
    # def _extract_phone_numbers(self, text: str) -> Set[str]: # Unused method
    #     """Extract phone numbers from text"""
    #     # Various phone number patterns
    #     patterns = [
    #         r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
    #         r'\b\+1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US with country code
    #         r'\b\d{10,15}\b',  # Generic long numbers
    #     ]
    #     phones = set()
    #     for pattern in patterns:
    #         phones.update(re.findall(pattern, text))
    #     return phones
    
    # def _extract_names(self, text: str) -> Set[str]: # Unused method
    #     """Extract potential full names from text"""
    #     # Look for patterns like "First Last" or "First M. Last"
    #     name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    #     names = set(re.findall(name_pattern, text))
        
    #     # Also look for patterns with middle initials
    #     name_with_middle_pattern = r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b'
    #     names.update(re.findall(name_with_middle_pattern, text))
        
    #     return names
    
    # def _extract_usernames(self, text: str) -> Set[str]: # Unused method
    #     """Extract potential usernames from text"""
    #     # Look for common username patterns
    #     username_patterns = [
    #         r'\b[A-Za-z0-9_]{3,20}\b',  # Basic username pattern
    #         r'@([A-Za-z0-9_]{3,20})',   # Twitter-style handles
    #     ]
    #     usernames = set()
    #     for pattern in username_patterns:
    #         matches = re.findall(pattern, text)
    #         # Filter out common words that aren't usernames
    #         filtered = [m for m in matches if len(m) >= 3 and not m.isdigit()]
    #         usernames.update(filtered)
    #     return usernames
    
    # def _extract_ip_addresses(self, text: str) -> Set[str]: # Unused method
    #     """Extract IP addresses from text"""
    #     ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    #     return set(re.findall(ip_pattern, text))
    
    # def _extract_social_media(self, text: str) -> Set[str]: # Unused method
    #     """Extract social media handles and platforms"""
    #     social_patterns = [
    #         r'@([A-Za-z0-9_]{3,20})',  # Twitter/Instagram handles
    #         r'facebook\.com/([A-Za-z0-9_.]+)',
    #         r'twitter\.com/([A-Za-z0-9_]+)',
    #         r'instagram\.com/([A-Za-z0-9_.]+)',
    #         r'linkedin\.com/in/([A-Za-z0-9-]+)',
    #     ]
    #     social_media = set()
    #     for pattern in social_patterns:
    #         matches = re.findall(pattern, text)
    #         social_media.update(matches)
    #     return social_media
    
    # def _extract_websites(self, text: str) -> Set[str]: # Unused method
    #     """Extract website domains from text"""
    #     website_pattern = r'\b(?:https?://)?(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b'
    #     return set(re.findall(website_pattern, text))
    
    # async def _parse_breach_data(self, breach_data: Union[str, dict]) -> DiscoveredInfo: # Unused method
    #     """Parse breach data and extract all discoverable information using only the LLM."""
    #     logger.debug(f"[LLM-OSINT] _parse_breach_data called with type: {type(breach_data)}")
    #     if isinstance(breach_data, str):
    #         try:
    #             data = json.loads(breach_data)
    #             logger.debug(f"[LLM-OSINT] Parsed string as JSON, keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
    #         except:
    #             data = {"raw_text": breach_data}
    #             logger.debug(f"[LLM-OSINT] Failed to parse as JSON, treating as raw text")
    #     else:
    #         data = breach_data
    #         logger.debug(f"[LLM-OSINT] Data is already dict, keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
    #     raw_text = ""
    #     if "raw_text" in data:
    #         raw_text = data["raw_text"]
    #         logger.debug(f"[LLM-OSINT] Found raw_text, length: {len(raw_text)}")
    #     elif isinstance(data, dict) and "List" in data and isinstance(data["List"], dict):
    #         logger.debug(f"[LLM-OSINT] Processing List data, databases: {len(data['List'])}")
    #         for db_name, db_data in data["List"].items():
    #             if isinstance(db_data, dict) and db_data.get("Data"):
    #                 for data_item in db_data["Data"]:
    #                     for v in data_item.values():
    #                         if isinstance(v, str):
    #                             raw_text += v + "\n"
    #         logger.debug(f"[LLM-OSINT] Built raw_text from List data, length: {len(raw_text)}")
    #     else:
    #         logger.debug(f"[LLM-OSINT] No raw_text or List found in data")
    #     if raw_text.strip():
    #         logger.debug(f"[LLM-OSINT] Calling _extract_with_llm with text length: {len(raw_text)}")
    #         return await self._extract_with_llm(raw_text)
    #     else:
    #         logger.debug(f"[LLM-OSINT] No raw_text to process, returning empty DiscoveredInfo")
    #         return DiscoveredInfo()
    
    async def _sequential_thinking_analysis(self, initial_query: str, discovered_info: DiscoveredInfo) -> Dict[str, Any]:
        """Use sequential thinking to analyze discovered info and decide on additional searches"""
        initial_discovered = discovered_info
        # Start sequential thinking analysis
        process_sequential_thought(
            thought=f"I need to analyze the initial OSINT search results for '{initial_query}' to understand what information was discovered.",
            next_thought_needed=True,
            thought_number=1,
            total_thoughts=4,
            thinking_module=self.thinking_module
        )
        # Analyze what was discovered
        discovered_summary = {
            "emails": len(initial_discovered.emails) if initial_discovered.emails else 0,
            "phones": len(initial_discovered.phone_numbers) if initial_discovered.phone_numbers else 0,
            "names": len(initial_discovered.full_names) if initial_discovered.full_names else 0,
            "usernames": len(initial_discovered.usernames) if initial_discovered.usernames else 0,
            "ips": len(initial_discovered.ip_addresses) if initial_discovered.ip_addresses else 0,
            "addresses": len(initial_discovered.addresses) if initial_discovered.addresses else 0,
            "passwords": len(initial_discovered.passwords) if initial_discovered.passwords else 0,
            "social_media": len(initial_discovered.social_media) if initial_discovered.social_media else 0,
            "websites": len(initial_discovered.websites) if initial_discovered.websites else 0
        }
        process_sequential_thought(
            thought=f"Initial search discovered: {discovered_summary}. This provides a comprehensive view of the target's digital footprint without the risk of false positives from additional searches.",
            next_thought_needed=True,
            thought_number=2,
            total_thoughts=4,
            thinking_module=self.thinking_module
        )
        # LLM extraction step (now just a placeholder for step count)
        process_sequential_thought(
            thought="Now using structured parsing to extract entities from the OSINT data for more thorough coverage.",
            next_thought_needed=True,
            thought_number=3,
            total_thoughts=4,
            thinking_module=self.thinking_module
        )
        # Focus on analysis rather than additional searches
        process_sequential_thought(
            thought=f"The initial search provides sufficient information for analysis. Additional searches would introduce false positives and dilute the accuracy of the investigation. I'll focus on analyzing the discovered data.",
            next_thought_needed=False,
            thought_number=4,
            total_thoughts=4,
            thinking_module=self.thinking_module
        )
        return {
            "initial_query": initial_query,
            "initial_discovered": initial_discovered,
            "additional_searches": [],  # Always empty - no additional searches
            "thinking_summary": self.thinking_module.get_summary()
        }
    
    async def investigate(self, initial_query: str, max_additional_searches: int = 5) -> Dict[str, Any]:
        """
        Perform intelligent OSINT investigation using sequential thinking.
        """
        logger.info(f"🔍 Starting intelligent OSINT investigation for: {initial_query}")
        try:
            initial_results = await _get_raw_leak_data(initial_query, 100, "en", "json")
            logger.debug(f"[LLM-OSINT] Raw OSINT API response for query '{initial_query}':\n{initial_results}")
            self.search_history.append({
                "query": initial_query,
                "type": "initial",
                "results": initial_results
            })
            # Use robust structured parser
            discovered_info = self._parse_structured_osint(initial_results)
            # Step 3: Geolocate IPs if present
            if discovered_info.ip_addresses:
                discovered_info.geolocations = await self._geolocate_ips(discovered_info.ip_addresses)
        except Exception as e:
            logger.error(f"🔒 OSINT API Initial Search Exception: {str(e)}")
            return {
                "error": True,
                "message": f"Initial search exception: {str(e)}",
                "initial_query": initial_query,
                "search_history": self.search_history
            }
        # Step 2: Use sequential thinking to analyze results
        analysis = await self._sequential_thinking_analysis(initial_query, discovered_info)
        # Step 3: No additional searches - focus on initial search analysis only
        logger.info(f"🧠 Sequential thinking completed analysis of initial search results")
        # Step 4: Compile comprehensive results from initial search only
        all_discovered_info = discovered_info
        # Step 5: Generate final analysis using sequential thinking
        self.thinking_module.clear_history()
        process_sequential_thought(
            thought=f"Comprehensive investigation complete using only initial search. Total discovered: {len(all_discovered_info.emails) if all_discovered_info.emails else 0} emails, {len(all_discovered_info.phone_numbers) if all_discovered_info.phone_numbers else 0} phones, {len(all_discovered_info.full_names) if all_discovered_info.full_names else 0} names, {len(all_discovered_info.usernames) if all_discovered_info.usernames else 0} usernames, {len(all_discovered_info.ip_addresses) if all_discovered_info.ip_addresses else 0} IPs. No additional searches were performed to maintain accuracy.",
            next_thought_needed=False,
            thought_number=1,
            total_thoughts=1,
            thinking_module=self.thinking_module
        )
        # Step 6: Format data in tidy, comprehensive format
        formatted_data = self._format_discovered_data(all_discovered_info)
        # Step 7: Generate sophisticated roast using sequential thinking
        roast_results = await self._generate_sophisticated_roast(all_discovered_info, initial_query)
        # Generate user-friendly findings presentation
        user_findings = self._format_findings_for_user(all_discovered_info, formatted_data)
        
        # Compile final results
        investigation_results = {
            "initial_query": initial_query,
            "search_history": self.search_history,
            "additional_searches_performed": 0,
            "sequential_thinking_analysis": analysis,
            "formatted_data": formatted_data,
            "user_findings": user_findings,
            "sophisticated_roast": roast_results,
            "thinking_summary": self.thinking_module.get_summary()
        }
        logger.info(f"✅ Intelligent OSINT investigation complete for: {initial_query}")
        return investigation_results

    def _format_discovered_data(self, discovered_info: DiscoveredInfo) -> Dict[str, Any]:
        """Format discovered data in a tidy, comprehensive format"""
        formatted_data = {
            "summary": {
                "total_emails": len(discovered_info.emails) if discovered_info.emails else 0,
                "total_phones": len(discovered_info.phone_numbers) if discovered_info.phone_numbers else 0,
                "total_names": len(discovered_info.full_names) if discovered_info.full_names else 0,
                "total_usernames": len(discovered_info.usernames) if discovered_info.usernames else 0,
                "total_ips": len(discovered_info.ip_addresses) if discovered_info.ip_addresses else 0,
                "total_addresses": len(discovered_info.addresses) if discovered_info.addresses else 0,
                "total_passwords": len(discovered_info.passwords) if discovered_info.passwords else 0,
                "total_social_media": len(discovered_info.social_media) if discovered_info.social_media else 0,
                "total_websites": len(discovered_info.websites) if discovered_info.websites else 0,
                "total_nicknames": len(discovered_info.nicknames) if discovered_info.nicknames else 0
            },
            "detailed_data": {
                "emails": list(discovered_info.emails) if discovered_info.emails else [],
                "phone_numbers": list(discovered_info.phone_numbers) if discovered_info.phone_numbers else [],
                "full_names": list(discovered_info.full_names) if discovered_info.full_names else [],
                "usernames": list(discovered_info.usernames) if discovered_info.usernames else [],
                "ip_addresses": list(discovered_info.ip_addresses) if discovered_info.ip_addresses else [],
                "addresses": list(discovered_info.addresses) if discovered_info.addresses else [],
                "passwords": list(discovered_info.passwords) if discovered_info.passwords else [],
                "social_media": list(discovered_info.social_media) if discovered_info.social_media else [],
                "websites": list(discovered_info.websites) if discovered_info.websites else [],
                "nicknames": list(discovered_info.nicknames) if discovered_info.nicknames else []
            },
            "geolocation_data": discovered_info.geolocations if discovered_info.geolocations else {},
            "breach_analysis": {
                "total_breaches": sum([
                    len(discovered_info.emails) if discovered_info.emails else 0,
                    len(discovered_info.phone_numbers) if discovered_info.phone_numbers else 0,
                    len(discovered_info.full_names) if discovered_info.full_names else 0,
                    len(discovered_info.usernames) if discovered_info.usernames else 0,
                    len(discovered_info.ip_addresses) if discovered_info.ip_addresses else 0,
                    len(discovered_info.addresses) if discovered_info.addresses else 0,
                    len(discovered_info.passwords) if discovered_info.passwords else 0,
                    len(discovered_info.social_media) if discovered_info.social_media else 0,
                    len(discovered_info.websites) if discovered_info.websites else 0,
                    len(discovered_info.nicknames) if discovered_info.nicknames else 0
                ]),
                "data_types_found": len([k for k, v in {
                    "emails": discovered_info.emails,
                    "phones": discovered_info.phone_numbers,
                    "names": discovered_info.full_names,
                    "usernames": discovered_info.usernames,
                    "ips": discovered_info.ip_addresses,
                    "addresses": discovered_info.addresses,
                    "passwords": discovered_info.passwords,
                    "social_media": discovered_info.social_media,
                    "websites": discovered_info.websites,
                    "nicknames": discovered_info.nicknames
                }.items() if v and len(v) > 0])
            }
        }
        return formatted_data

    async def _generate_sophisticated_roast(self, discovered_info: DiscoveredInfo, initial_query: str) -> Dict[str, Any]:
        """Generate a sophisticated roast using sequential thinking based on all findings"""
        
        # Reset thinking session for roasting
        self.thinking_module.clear_history()
        
        # Start roasting analysis with sequential thinking
        process_sequential_thought(
            thought=f"I need to analyze all the discovered data for '{initial_query}' to create a comprehensive and entertaining roast. Let me examine what we found and identify the most roast-worthy aspects.",
            next_thought_needed=True,
            thought_number=1,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        # Analyze the data types and their roast potential
        data_summary = {
            "emails": len(discovered_info.emails) if discovered_info.emails else 0,
            "phones": len(discovered_info.phone_numbers) if discovered_info.phone_numbers else 0,
            "names": len(discovered_info.full_names) if discovered_info.full_names else 0,
            "usernames": len(discovered_info.usernames) if discovered_info.usernames else 0,
            "ips": len(discovered_info.ip_addresses) if discovered_info.ip_addresses else 0,
            "addresses": len(discovered_info.addresses) if discovered_info.addresses else 0,
            "passwords": len(discovered_info.passwords) if discovered_info.passwords else 0,
            "social_media": len(discovered_info.social_media) if discovered_info.social_media else 0,
            "websites": len(discovered_info.websites) if discovered_info.websites else 0,
            "nicknames": len(discovered_info.nicknames) if discovered_info.nicknames else 0
        }
        
        process_sequential_thought(
            thought=f"Data analysis shows: {data_summary}. The most roast-worthy aspects are: {len(discovered_info.passwords) if discovered_info.passwords else 0} exposed passwords (security nightmare), {len(discovered_info.usernames) if discovered_info.usernames else 0} usernames (digital footprint), and {len(discovered_info.emails) if discovered_info.emails else 0} emails (online presence). This person has a significant digital trail!",
            next_thought_needed=True,
            thought_number=2,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        # Identify specific roast targets
        roast_targets = []
        if discovered_info.passwords and len(discovered_info.passwords) > 0:
            roast_targets.append(f"{len(discovered_info.passwords)} exposed passwords")
        if discovered_info.usernames and len(discovered_info.usernames) > 0:
            roast_targets.append(f"{len(discovered_info.usernames)} usernames across platforms")
        if discovered_info.emails and len(discovered_info.emails) > 0:
            roast_targets.append(f"{len(discovered_info.emails)} email addresses")
        if discovered_info.phone_numbers and len(discovered_info.phone_numbers) > 0:
            roast_targets.append(f"{len(discovered_info.phone_numbers)} phone numbers")
        
        process_sequential_thought(
            thought=f"Key roast targets identified: {', '.join(roast_targets)}. The password exposure is particularly embarrassing - this person clearly needs a security intervention! The multiple usernames suggest they're either very active online or can't stick to one identity.",
            next_thought_needed=True,
            thought_number=3,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        # Generate roast content
        roast_content = self._create_roast_content(discovered_info, initial_query)
        
        process_sequential_thought(
            thought=f"Roast content generated successfully. The roast focuses on their security negligence, digital footprint size, and the embarrassing nature of having personal data exposed. It's both entertaining and educational about cybersecurity.",
            next_thought_needed=True,
            thought_number=4,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        # Final roast assessment
        process_sequential_thought(
            thought=f"Roast complete! This person has {len(discovered_info.passwords) if discovered_info.passwords else 0} passwords exposed, {len(discovered_info.usernames) if discovered_info.usernames else 0} usernames floating around, and a digital footprint that could be seen from space. They need to invest in a password manager and maybe some privacy lessons!",
            next_thought_needed=False,
            thought_number=5,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        return {
            "roast_content": roast_content,
            "roast_targets": roast_targets,
            "data_summary": data_summary,
            "thinking_summary": self.thinking_module.get_summary()
        }
    
    def _create_roast_content(self, discovered_info: DiscoveredInfo, initial_query: str) -> str:
        """Create entertaining roast content based on discovered data"""
        
        roast_parts = []
        
        # Password roast
        if discovered_info.passwords and len(discovered_info.passwords) > 0:
            password_count = len(discovered_info.passwords)
            if password_count > 10:
                roast_parts.append(f"🔥 {password_count} passwords exposed! This person's security is so weak, even a calculator could hack them!")
            elif password_count > 5:
                roast_parts.append(f"🔐 {password_count} passwords leaked! They probably use 'password123' for everything!")
            else:
                roast_parts.append(f"🔑 {password_count} passwords found! At least they're consistent in their poor security choices!")
        
        # Username roast
        if discovered_info.usernames and len(discovered_info.usernames) > 0:
            username_count = len(discovered_info.usernames)
            if username_count > 15:
                roast_parts.append(f"👤 {username_count} usernames! This person has more online identities than a spy movie!")
            elif username_count > 8:
                roast_parts.append(f"🎭 {username_count} usernames discovered! They can't decide who they want to be online!")
            else:
                roast_parts.append(f"💻 {username_count} usernames found! At least they're trying to stay organized!")
        
        # Email roast
        if discovered_info.emails and len(discovered_info.emails) > 0:
            email_count = len(discovered_info.emails)
            roast_parts.append(f"📧 {email_count} email addresses exposed! Their inbox is probably a disaster zone!")
        
        # Phone number roast
        if discovered_info.phone_numbers and len(discovered_info.phone_numbers) > 0:
            phone_count = len(discovered_info.phone_numbers)
            roast_parts.append(f"📱 {phone_count} phone numbers leaked! They're probably getting spam calls from the 90s!")
        
        # Overall assessment
        total_exposures = sum([
            len(discovered_info.emails) if discovered_info.emails else 0,
            len(discovered_info.phone_numbers) if discovered_info.phone_numbers else 0,
            len(discovered_info.usernames) if discovered_info.usernames else 0,
            len(discovered_info.passwords) if discovered_info.passwords else 0
        ])
        
        if total_exposures > 20:
            roast_parts.append("💀 This person's digital footprint is so massive, it could be seen from the International Space Station!")
        elif total_exposures > 10:
            roast_parts.append("😅 They've got more exposed data than a government database!")
        else:
            roast_parts.append("😊 At least they're not the worst case we've seen... yet!")
        
        # Security tip
        roast_parts.append("💡 Pro tip: Use a password manager and enable 2FA! Your future self will thank you!")
        
        return " ".join(roast_parts)

    async def _extract_with_llm(self, raw_text: str) -> DiscoveredInfo:
        """Use the LLM to extract entities from raw OSINT text."""
        prompt = (
            "Extract all emails, phone numbers, full names, usernames, IP addresses, addresses, passwords, nicknames, social media handles, and website domains from the following text. "
            "Return the result as a JSON object with keys: emails, phone_numbers, full_names, usernames, ip_addresses, addresses, passwords, nicknames, social_media, websites.\n\nText:\n" + raw_text
        )
        url = settings.llm_base_url + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": settings.llm_model_id,
            "messages": [
                {"role": "system", "content": "You are an expert OSINT entity extractor."},
                {"role": "user", "content": prompt}
            ],
            "temperature": settings.llm_temperature,
            "max_tokens": 512
        }
        logger.debug(f"[LLM-OSINT] Prompt sent to LLM:\n{prompt}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.debug(f"[LLM-OSINT] Raw LLM response:\n{content}")
            try:
                parsed = json.loads(content)
            except Exception:
                # Try to extract JSON from text
                import re
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                else:
                    parsed = {}
            return DiscoveredInfo(
                emails=set(parsed.get("emails", [])),
                phone_numbers=set(parsed.get("phone_numbers", [])),
                full_names=set(parsed.get("full_names", [])),
                usernames=set(parsed.get("usernames", [])),
                ip_addresses=set(parsed.get("ip_addresses", [])),
                addresses=set(parsed.get("addresses", [])),
                passwords=set(parsed.get("passwords", [])),
                nicknames=set(parsed.get("nicknames", [])),
                social_media=set(parsed.get("social_media", [])),
                websites=set(parsed.get("websites", [])),
            )

    def _parse_structured_osint(self, raw_results: dict) -> DiscoveredInfo:
        """Parse the structured OSINT API response and aggregate all discovered info."""
        discovered = DiscoveredInfo()
        if not isinstance(raw_results, dict) or "List" not in raw_results or not isinstance(raw_results["List"], dict):
            return discovered
        for db_name, db_data in raw_results["List"].items():
            if not isinstance(db_data, dict) or not db_data.get("Data"):
                continue
            for data_item in db_data["Data"]:
                # Emails
                if data_item.get("Email") and discovered.emails is not None:
                    discovered.emails.add(data_item["Email"])
                # Phone numbers
                if data_item.get("Phone") and discovered.phone_numbers is not None:
                    discovered.phone_numbers.add(data_item["Phone"])
                # Full names
                if data_item.get("FullName") and discovered.full_names is not None:
                    discovered.full_names.add(data_item["FullName"])
                if data_item.get("Name") and discovered.full_names is not None:
                    discovered.full_names.add(data_item["Name"])
                # Usernames
                if data_item.get("Username") and discovered.usernames is not None:
                    discovered.usernames.add(data_item["Username"])
                if data_item.get("NickName") and discovered.usernames is not None:
                    discovered.usernames.add(data_item["NickName"])
                # IP addresses
                if data_item.get("IP") and discovered.ip_addresses is not None:
                    discovered.ip_addresses.add(data_item["IP"].strip())
                # Addresses
                if data_item.get("Address") and discovered.addresses is not None:
                    discovered.addresses.add(data_item["Address"])
                # Passwords
                if data_item.get("Password") and discovered.passwords is not None:
                    discovered.passwords.add(data_item["Password"])
                # Other password fields (hashes, etc)
                for key in data_item:
                    if "password" in key.lower() and isinstance(data_item[key], str) and discovered.passwords is not None:
                        discovered.passwords.add(data_item[key])
                # Nicknames
                if data_item.get("NickName") and discovered.nicknames is not None:
                    discovered.nicknames.add(data_item["NickName"])
                # Social media (not always present, but check common fields)
                if data_item.get("Twitter") and discovered.social_media is not None:
                    discovered.social_media.add(data_item["Twitter"])
                if data_item.get("Facebook") and discovered.social_media is not None:
                    discovered.social_media.add(data_item["Facebook"])
                # Websites
                if data_item.get("LeakSite") and discovered.websites is not None:
                    discovered.websites.add(data_item["LeakSite"])
                if data_item.get("Url") and discovered.websites is not None:
                    discovered.websites.add(data_item["Url"])
        return discovered

    async def _geolocate_ips(self, ip_addresses: Set[str]) -> Dict[str, dict]:
        """Geolocate a set of IP addresses asynchronously."""
        results = {}
        tasks = [asyncio.create_task(_geolocate_ip(ip)) for ip in ip_addresses]
        geos = await asyncio.gather(*tasks)
        for ip, geo in zip(ip_addresses, geos):
            results[ip] = geo
        return results

    # def _analyze_geographic_distribution(self, discovered_info: DiscoveredInfo) -> Dict[str, Any]: # Unused method
    #     """Analyze the geographic distribution of user's own leaked IP addresses."""
    #     if not discovered_info.geolocations:
    #         return {"countries": [], "total_countries": 0, "cities": [], "total_cities": 0, "regions": [], "total_regions": 0}
        
        countries = set()
        cities = set()
        regions = set()
        
        for ip, geo_data in discovered_info.geolocations.items():
            if geo_data.get("success") and geo_data.get("country"):
                countries.add(geo_data["country"])
            if geo_data.get("success") and geo_data.get("city"):
                cities.add(geo_data["city"])
            if geo_data.get("success") and geo_data.get("region"):
                regions.add(geo_data["region"])
        
        return {
            "countries": list(countries),
            "cities": list(cities),
            "regions": list(regions),
            "total_countries": len(countries),
            "total_cities": len(cities),
            "total_regions": len(regions)
        }
    
    def _format_findings_for_user(self, discovered_info: DiscoveredInfo, formatted_data: Dict[str, Any]) -> str:
        """Format discovered data in a fun, user-friendly way for presentation"""
        findings = []
        
        # Header
        findings.append("🔍 YOUR DIGITAL FOOTPRINT DISCOVERY 🔍")
        findings.append("=" * 50)
        
        # Summary stats
        total_breaches = formatted_data["breach_analysis"]["total_breaches"]
        findings.append(f"📊 Total data points found: {total_breaches}")
        findings.append("")
        
        # Detailed breakdown
        if discovered_info.emails and len(discovered_info.emails) > 0:
            findings.append(f"📧 Email addresses: {len(discovered_info.emails)}")
            for email in list(discovered_info.emails)[:3]:  # Show first 3
                findings.append(f"   • {email}")
            if len(discovered_info.emails) > 3:
                findings.append(f"   ... and {len(discovered_info.emails) - 3} more")
            findings.append("")
        
        if discovered_info.phone_numbers and len(discovered_info.phone_numbers) > 0:
            findings.append(f"📱 Phone numbers: {len(discovered_info.phone_numbers)}")
            for phone in list(discovered_info.phone_numbers)[:3]:
                findings.append(f"   • {phone}")
            if len(discovered_info.phone_numbers) > 3:
                findings.append(f"   ... and {len(discovered_info.phone_numbers) - 3} more")
            findings.append("")
        
        if discovered_info.full_names and len(discovered_info.full_names) > 0:
            findings.append(f"👤 Full names: {len(discovered_info.full_names)}")
            for name in list(discovered_info.full_names)[:3]:
                findings.append(f"   • {name}")
            if len(discovered_info.full_names) > 3:
                findings.append(f"   ... and {len(discovered_info.full_names) - 3} more")
            findings.append("")
        
        if discovered_info.usernames and len(discovered_info.usernames) > 0:
            findings.append(f"💻 Usernames: {len(discovered_info.usernames)}")
            for username in list(discovered_info.usernames)[:3]:
                findings.append(f"   • {username}")
            if len(discovered_info.usernames) > 3:
                findings.append(f"   ... and {len(discovered_info.usernames) - 3} more")
            findings.append("")
        
        if discovered_info.passwords and len(discovered_info.passwords) > 0:
            findings.append(f"🔐 Passwords: {len(discovered_info.passwords)}")
            for password in list(discovered_info.passwords)[:3]:
                findings.append(f"   • {password}")
            if len(discovered_info.passwords) > 3:
                findings.append(f"   ... and {len(discovered_info.passwords) - 3} more")
            findings.append("")
        
        if discovered_info.addresses and len(discovered_info.addresses) > 0:
            findings.append(f"🏠 Addresses: {len(discovered_info.addresses)}")
            for address in list(discovered_info.addresses)[:3]:
                findings.append(f"   • {address}")
            if len(discovered_info.addresses) > 3:
                findings.append(f"   ... and {len(discovered_info.addresses) - 3} more")
            findings.append("")
        
        if discovered_info.social_media and len(discovered_info.social_media) > 0:
            findings.append(f"📱 Social media: {len(discovered_info.social_media)}")
            for social in list(discovered_info.social_media)[:3]:
                findings.append(f"   • {social}")
            if len(discovered_info.social_media) > 3:
                findings.append(f"   ... and {len(discovered_info.social_media) - 3} more")
            findings.append("")
        
        if discovered_info.websites and len(discovered_info.websites) > 0:
            findings.append(f"🌐 Websites: {len(discovered_info.websites)}")
            for website in list(discovered_info.websites)[:3]:
                findings.append(f"   • {website}")
            if len(discovered_info.websites) > 3:
                findings.append(f"   ... and {len(discovered_info.websites) - 3} more")
            findings.append("")
        
        # Geolocation data - user's own leaked IP addresses
        if discovered_info.geolocations and len(discovered_info.geolocations) > 0:
            findings.append("🌍 Your leaked IP addresses:")
            for ip, geo_data in discovered_info.geolocations.items():
                if geo_data.get("success"):
                    location_parts = []
                    if geo_data.get("city"):
                        location_parts.append(geo_data["city"])
                    if geo_data.get("region"):
                        location_parts.append(geo_data["region"])
                    if geo_data.get("country"):
                        location_parts.append(geo_data["country"])
                    
                    if location_parts:
                        findings.append(f"   • {ip} → {', '.join(location_parts)}")
                    else:
                        findings.append(f"   • {ip} → Location unknown")
                else:
                    findings.append(f"   • {ip} → Geolocation failed")
            findings.append("")
        
        # Footer
        findings.append("=" * 50)
        findings.append("🎭 Now for the roast... 🎭")
        findings.append("")
        
        return "\n".join(findings)


# Convenience function for easy usage
async def intelligent_osint_investigation(initial_query: str, max_additional_searches: int = 5) -> Dict[str, Any]:
    """
    Perform intelligent OSINT investigation using sequential thinking.
    
    Args:
        initial_query: The initial search query (email, name, etc.)
        max_additional_searches: Maximum number of additional searches to perform
        
    Returns:
        Dictionary containing all investigation results
    """
    investigator = IntelligentOSINTInvestigator()
    return await investigator.investigate(initial_query, max_additional_searches)


# Example usage
if __name__ == "__main__":
    async def test_investigation():
        # Test the intelligent investigation
        results = await intelligent_osint_investigation("test@example.com", max_additional_searches=3)
        print(json.dumps(results, indent=2))
    
    asyncio.run(test_investigation()) 

# async def _get_raw_leak_data(request: str, limit: int = 100, lang: str = "en", report_type: str = "json") -> dict: # Unused function
#     """Get raw breach data without formatting - for internal use by intelligent OSINT investigator"""
#     api_token = settings.leakosint_api_key
#     if not api_token:
#         logger.error("🔒 OSINT API Error: No API token configured")
#         return {"error": True, "message": "OSINT search service is not configured."}
#     if not request:
#         logger.error("🔒 OSINT API Error: No search request provided")
#         return {"error": True, "message": "No search request provided."}
    
#     url = "https://leakosintapi.com/"
#     data = {
#         "token": api_token,
#         "request": request,
#         "limit": limit,
#         "lang": lang,
#         "type": report_type
#     }
    
#     logger.info(f"🔍 OSINT API Request: {request} (limit={limit}, lang={lang}, type={report_type})")
    
#     try:
#         async with httpx.AsyncClient(timeout=60.0) as client:
#             response = await client.post(url, json=data)
#             response.raise_for_status()
#             result = response.json()
            
#             if "Error code" in result:
#                 error_msg = f"Search service error: {result.get('Error code', 'Unknown error')}"
#                 logger.error(f"🔒 OSINT API Error: {error_msg}")
#                 return {"error": True, "message": error_msg}
            
#             logger.info(f"✅ OSINT API Success: {request} - {len(result.get('List', {}))} databases found")
#             return result
#     except httpx.HTTPStatusError as e:
#         error_msg = f"Search service unavailable: HTTP {e.response.status_code} - {str(e)}"
#         logger.error(f"🔒 OSINT API HTTP Error: {error_msg}")
#         return {"error": True, "message": error_msg}
#     except httpx.TimeoutException as e:
#         error_msg = f"Search request timeout: {str(e)}"
#         logger.error(f"🔒 OSINT API Timeout: {error_msg}")
#         return {"error": True, "message": error_msg}
#     except httpx.ConnectError as e:
#         error_msg = f"Search service connection failed: {str(e)}"
#         logger.error(f"🔒 OSINT API Connection Error: {error_msg}")
#         return {"error": True, "message": error_msg}
#     except Exception as e:
#         error_msg = f"Search request failed: {str(e)}"
#         logger.error(f"🔒 OSINT API Unexpected Error: {error_msg}")
#         return {"error": True, "message": error_msg}

async def _geolocate_ip(ip: str) -> dict:
    """Geolocate an IP address using a free API service"""
    try:
        url = f"http://ip-api.com/json/{ip}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                return {
                    "success": True,
                    "ip": ip,
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "isp": data.get("isp"),
                    "org": data.get("org")
                }
            else:
                return {
                    "success": False,
                    "ip": ip,
                    "error": "Geolocation failed"
                }
    except Exception as e:
        logger.error(f"Geolocation error for {ip}: {str(e)}")
        return {
            "success": False,
            "ip": ip,
            "error": str(e)
        } 