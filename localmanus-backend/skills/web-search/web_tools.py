import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from core.skill_manager import BaseSkill
from typing import List, Dict


class WebSearchSkill(BaseSkill):
    """
    Standardized skill for web search operations using DuckDuckGo.
    """

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Skill for web-related operations like searching and scraping."

    def search_web(self, query: str, max_results: int = 5) -> str:
        """
        Searches the web using DuckDuckGo and returns results.

        Args:
            query (str): The search query string
            max_results (int): Maximum number of results to return (default: 5)

        Returns:
            str: Formatted search results or error message
        """
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
            return "\n".join(results) if results else "No results found."
        except Exception as e:
            return f"Error during search: {str(e)}"

    def scrape_web(self, url: str) -> str:
        """
        Fetches the content of a webpage and returns the text.

        Args:
            url (str): The URL to scrape

        Returns:
            str: Scraped text content or error message
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to 5000 characters
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"


class WebTools(BaseSkill):
    """
    Legacy class maintained for backward compatibility.
    Use WebSearchSkill instead.
    """
    
    def __init__(self):
        super().__init__()
        self.web_search_skill = WebSearchSkill()

    def search(self, query: str, max_results: int = 5) -> str:
        """
        Searches the web using DuckDuckGo and returns results.
        
        Args:
            query (str): The search query string
            max_results (int): Maximum number of results to return (default: 5)
        
        Returns:
            str: Formatted search results or error message
        """
        return self.web_search_skill.search_web(query, max_results)

    def scrape(self, url: str) -> str:
        """
        Fetches the content of a webpage and returns the text.
        
        Args:
            url (str): The URL to scrape
        
        Returns:
            str: Scraped text content or error message
        """
        return self.web_search_skill.scrape_web(url)
