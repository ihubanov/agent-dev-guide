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
from app.tools import _get_raw_leak_data, _batch_search_leak_impl

logger = logging.getLogger(__name__)


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


class IntelligentOSINTInvestigator:
    """
    Intelligent OSINT investigator that uses sequential thinking to dynamically
    decide what additional searches to perform based on discovered information.
    """
    
    def __init__(self):
        self.thinking_module = SequentialThinkingModule()
        self.discovered_info = DiscoveredInfo()
        self.search_history = []
        self.investigation_results = {}
        
    def _extract_emails(self, text: str) -> Set[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return set(re.findall(email_pattern, text))
    
    def _extract_phone_numbers(self, text: str) -> Set[str]:
        """Extract phone numbers from text"""
        # Various phone number patterns
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\+1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US with country code
            r'\b\d{10,15}\b',  # Generic long numbers
        ]
        phones = set()
        for pattern in patterns:
            phones.update(re.findall(pattern, text))
        return phones
    
    def _extract_names(self, text: str) -> Set[str]:
        """Extract potential full names from text"""
        # Look for patterns like "First Last" or "First M. Last"
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        names = set(re.findall(name_pattern, text))
        
        # Also look for patterns with middle initials
        name_with_middle_pattern = r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b'
        names.update(re.findall(name_with_middle_pattern, text))
        
        return names
    
    def _extract_usernames(self, text: str) -> Set[str]:
        """Extract potential usernames from text"""
        # Look for common username patterns
        username_patterns = [
            r'\b[A-Za-z0-9_]{3,20}\b',  # Basic username pattern
            r'@([A-Za-z0-9_]{3,20})',   # Twitter-style handles
        ]
        usernames = set()
        for pattern in username_patterns:
            matches = re.findall(pattern, text)
            # Filter out common words that aren't usernames
            filtered = [m for m in matches if len(m) >= 3 and not m.isdigit()]
            usernames.update(filtered)
        return usernames
    
    def _extract_ip_addresses(self, text: str) -> Set[str]:
        """Extract IP addresses from text"""
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        return set(re.findall(ip_pattern, text))
    
    def _extract_social_media(self, text: str) -> Set[str]:
        """Extract social media handles and platforms"""
        social_patterns = [
            r'@([A-Za-z0-9_]{3,20})',  # Twitter/Instagram handles
            r'facebook\.com/([A-Za-z0-9_.]+)',
            r'twitter\.com/([A-Za-z0-9_]+)',
            r'instagram\.com/([A-Za-z0-9_.]+)',
            r'linkedin\.com/in/([A-Za-z0-9-]+)',
        ]
        social_media = set()
        for pattern in social_patterns:
            matches = re.findall(pattern, text)
            social_media.update(matches)
        return social_media
    
    def _extract_websites(self, text: str) -> Set[str]:
        """Extract website domains from text"""
        website_pattern = r'\b(?:https?://)?(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b'
        return set(re.findall(website_pattern, text))
    
    def _parse_breach_data(self, breach_data: Union[str, dict]) -> DiscoveredInfo:
        """Parse breach data and extract all discoverable information"""
        if isinstance(breach_data, str):
            try:
                data = json.loads(breach_data)
            except:
                # If it's not JSON, treat as plain text
                data = {"raw_text": breach_data}
        else:
            # Already a dict
            data = breach_data
        
        discovered = DiscoveredInfo()
        
        # Extract from all databases
        if isinstance(data, dict) and "List" in data:
            for db_name, db_data in data["List"].items():
                if db_data.get("Data"):
                    for data_item in db_data["Data"]:
                        # Extract emails
                        if data_item.get("Email"):
                            discovered.emails.add(data_item["Email"])
                        
                        # Extract phone numbers
                        if data_item.get("Phone"):
                            discovered.phone_numbers.add(data_item["Phone"])
                        
                        # Extract names
                        if data_item.get("Name"):
                            discovered.full_names.add(data_item["Name"])
                        
                        # Extract usernames
                        if data_item.get("Username"):
                            discovered.usernames.add(data_item["Username"])
                        
                        # Extract IP addresses
                        if data_item.get("IP"):
                            discovered.ip_addresses.add(data_item["IP"])
                        
                        # Extract addresses
                        if data_item.get("Address"):
                            discovered.addresses.add(data_item["Address"])
                        
                        # Extract passwords
                        if data_item.get("Password"):
                            discovered.passwords.add(data_item["Password"])
                        
                        # Extract nicknames
                        if data_item.get("NickName"):
                            discovered.nicknames.add(data_item["NickName"])
                        
                        # Extract all text fields for additional analysis
                        for key, value in data_item.items():
                            if isinstance(value, str):
                                # Extract emails from any field
                                discovered.emails.update(self._extract_emails(value))
                                
                                # Extract phone numbers from any field
                                discovered.phone_numbers.update(self._extract_phone_numbers(value))
                                
                                # Extract names from any field
                                discovered.full_names.update(self._extract_names(value))
                                
                                # Extract usernames from any field
                                discovered.usernames.update(self._extract_usernames(value))
                                
                                # Extract IP addresses from any field
                                discovered.ip_addresses.update(self._extract_ip_addresses(value))
                                
                                # Extract social media from any field
                                discovered.social_media.update(self._extract_social_media(value))
                                
                                # Extract websites from any field
                                discovered.websites.update(self._extract_websites(value))
        
        # Also analyze raw text if available
        if "raw_text" in data:
            text = data["raw_text"]
            discovered.emails.update(self._extract_emails(text))
            discovered.phone_numbers.update(self._extract_phone_numbers(text))
            discovered.full_names.update(self._extract_names(text))
            discovered.usernames.update(self._extract_usernames(text))
            discovered.ip_addresses.update(self._extract_ip_addresses(text))
            discovered.social_media.update(self._extract_social_media(text))
            discovered.websites.update(self._extract_websites(text))
        
        return discovered
    
    async def _sequential_thinking_analysis(self, initial_query: str, initial_results: str) -> Dict[str, Any]:
        """Use sequential thinking to analyze initial results and decide on additional searches"""
        
        # Parse the initial results
        initial_discovered = self._parse_breach_data(initial_results)
        
        # Start sequential thinking analysis
        process_sequential_thought(
            thought=f"I need to analyze the initial OSINT search results for '{initial_query}' to determine what additional searches would be valuable.",
            next_thought_needed=True,
            thought_number=1,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        # Analyze what was discovered
        discovered_summary = {
            "emails": len(initial_discovered.emails),
            "phones": len(initial_discovered.phone_numbers),
            "names": len(initial_discovered.full_names),
            "usernames": len(initial_discovered.usernames),
            "ips": len(initial_discovered.ip_addresses),
            "addresses": len(initial_discovered.addresses),
            "passwords": len(initial_discovered.passwords),
            "social_media": len(initial_discovered.social_media),
            "websites": len(initial_discovered.websites)
        }
        
        process_sequential_thought(
            thought=f"Initial search discovered: {discovered_summary}. I need to evaluate which of these could lead to additional valuable information.",
            next_thought_needed=True,
            thought_number=2,
            total_thoughts=5,
            thinking_module=self.thinking_module
        )
        
        # Decide on additional searches
        additional_searches = []
        
        # If we found phone numbers, search for them
        if initial_discovered.phone_numbers:
            process_sequential_thought(
                thought=f"Found {len(initial_discovered.phone_numbers)} phone numbers. These could reveal additional personal information, so I should search for them.",
                next_thought_needed=True,
                thought_number=3,
                total_thoughts=5,
                thinking_module=self.thinking_module
            )
            additional_searches.extend(list(initial_discovered.phone_numbers))
        
        # If we found full names, search for them
        if initial_discovered.full_names:
            process_sequential_thought(
                thought=f"Found {len(initial_discovered.full_names)} full names. These could reveal additional accounts and information, so I should search for them.",
                next_thought_needed=True,
                thought_number=4,
                total_thoughts=5,
                thinking_module=self.thinking_module
            )
            additional_searches.extend(list(initial_discovered.full_names))
        
        # If we found usernames, search for them
        if initial_discovered.usernames:
            process_sequential_thought(
                thought=f"Found {len(initial_discovered.usernames)} usernames. These could reveal additional accounts across different platforms, so I should search for them.",
                next_thought_needed=True,
                thought_number=5,
                total_thoughts=6,
                thinking_module=self.thinking_module
            )
            additional_searches.extend(list(initial_discovered.usernames))
        
        # If we found IP addresses, search for them
        if initial_discovered.ip_addresses:
            process_sequential_thought(
                thought=f"Found {len(initial_discovered.ip_addresses)} IP addresses. These could reveal additional accounts and locations, so I should search for them.",
                next_thought_needed=False,
                thought_number=6,
                total_thoughts=6,
                thinking_module=self.thinking_module
            )
            additional_searches.extend(list(initial_discovered.ip_addresses))
        
        return {
            "initial_query": initial_query,
            "initial_discovered": initial_discovered,
            "additional_searches": additional_searches,
            "thinking_summary": self.thinking_module.get_summary()
        }
    
    async def investigate(self, initial_query: str, max_additional_searches: int = 5) -> Dict[str, Any]:
        """
        Perform intelligent OSINT investigation using sequential thinking.
        
        Args:
            initial_query: The initial search query (email, name, etc.)
            max_additional_searches: Maximum number of additional searches to perform
            
        Returns:
            Dictionary containing all investigation results
        """
        
        # Step 1: Perform initial search
        logger.info(f"🔍 Starting intelligent OSINT investigation for: {initial_query}")
        
        initial_results = await _get_raw_leak_data(initial_query, 100, "en", "json")
        self.search_history.append({
            "query": initial_query,
            "type": "initial",
            "results": initial_results
        })
        
        # Step 2: Use sequential thinking to analyze results and decide on additional searches
        analysis = await self._sequential_thinking_analysis(initial_query, initial_results)
        
        # Step 3: Perform additional searches based on sequential thinking analysis
        additional_results = {}
        additional_searches = analysis["additional_searches"][:max_additional_searches]
        
        if additional_searches:
            logger.info(f"🧠 Sequential thinking decided to perform {len(additional_searches)} additional searches")
            
            # Perform batch search for efficiency
            batch_results = await _batch_search_leak_impl(additional_searches, 100, "en", "json")
            additional_results["batch_search"] = batch_results
            
            # Also perform individual searches for detailed analysis
            for search_query in additional_searches:
                individual_result = await _search_leak_impl(search_query, 100, "en", "json")
                additional_results[search_query] = individual_result
                self.search_history.append({
                    "query": search_query,
                    "type": "additional",
                    "results": individual_result
                })
        
        # Step 4: Compile comprehensive results
        all_discovered_info = DiscoveredInfo()
        
        # Merge all discovered information
        for search_record in self.search_history:
            discovered = self._parse_breach_data(search_record["results"])
            all_discovered_info.emails.update(discovered.emails)
            all_discovered_info.phone_numbers.update(discovered.phone_numbers)
            all_discovered_info.full_names.update(discovered.full_names)
            all_discovered_info.usernames.update(discovered.usernames)
            all_discovered_info.ip_addresses.update(discovered.ip_addresses)
            all_discovered_info.addresses.update(discovered.addresses)
            all_discovered_info.passwords.update(discovered.passwords)
            all_discovered_info.nicknames.update(discovered.nicknames)
            all_discovered_info.social_media.update(discovered.social_media)
            all_discovered_info.websites.update(discovered.websites)
        
        # Step 5: Generate final analysis using sequential thinking
        process_sequential_thought(
            thought=f"Comprehensive investigation complete. Total discovered: {len(all_discovered_info.emails)} emails, {len(all_discovered_info.phone_numbers)} phones, {len(all_discovered_info.full_names)} names, {len(all_discovered_info.usernames)} usernames, {len(all_discovered_info.ip_addresses)} IPs.",
            next_thought_needed=False,
            thought_number=1,
            total_thoughts=1,
            thinking_module=self.thinking_module
        )
        
        # Compile final results
        investigation_results = {
            "initial_query": initial_query,
            "search_history": self.search_history,
            "additional_searches_performed": len(additional_searches),
            "sequential_thinking_analysis": analysis,
            "comprehensive_discovered_info": {
                "emails": list(all_discovered_info.emails),
                "phone_numbers": list(all_discovered_info.phone_numbers),
                "full_names": list(all_discovered_info.full_names),
                "usernames": list(all_discovered_info.usernames),
                "ip_addresses": list(all_discovered_info.ip_addresses),
                "addresses": list(all_discovered_info.addresses),
                "passwords": list(all_discovered_info.passwords),
                "nicknames": list(all_discovered_info.nicknames),
                "social_media": list(all_discovered_info.social_media),
                "websites": list(all_discovered_info.websites)
            },
            "thinking_summary": self.thinking_module.get_summary(),
            "additional_results": additional_results
        }
        
        logger.info(f"✅ Intelligent OSINT investigation complete for: {initial_query}")
        return investigation_results


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