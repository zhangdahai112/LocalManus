"""
Test cases for SSE chat endpoint (main.py L399-419)

These tests cover all skill capabilities:
- Web Search (Bing, Google, DuckDuckGo, Baidu)
- Web Scraping
- Browser Screenshot
- File Operations
- System Execution (Python, Shell)

Usage:
    python test_chat_sse.py

Requirements:
    - Backend server running on http://localhost:8000
    - Valid access token for authentication
    - Sandbox container running (for web search tests)
"""

import asyncio
import json
import aiohttp
from typing import Optional
from datetime import datetime

BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = "/api/chat"


async def get_access_token(session: aiohttp.ClientSession) -> Optional[str]:
    """Get access token by logging in via /api/login endpoint.
    
    The endpoint uses OAuth2PasswordRequestForm which expects form data
    with 'username' and 'password' fields.
    """
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    try:
        # Use form data (application/x-www-form-urlencoded) as required by OAuth2PasswordRequestForm
        async with session.post(f"{BASE_URL}/api/login", data=login_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Try different token field names
                token = data.get("access_token") or data.get("token") or data.get("data", {}).get("token")
                if token:
                    print(f"✅ Login successful, token obtained")
                    return token
                else:
                    print(f"⚠️ Login response: {data}")
            else:
                text = await resp.text()
                print(f"❌ Login failed: HTTP {resp.status} - {text}")
    except Exception as e:
        print(f"❌ Login error: {e}")
    return None


async def test_sse_chat(
    session: aiohttp.ClientSession, 
    access_token: str, 
    message: str, 
    file_paths: Optional[str] = None,
    test_name: str = "Test"
) -> None:
    """Test SSE chat endpoint with a message."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    if file_paths:
        print(f"Files: {file_paths}")
    
    params = {
        "session_id": f"test_session_{datetime.now().timestamp()}",
        "input": message,
        "access_token": access_token
    }
    if file_paths:
        params["file_paths"] = file_paths
    
    try:
        async with session.get(
            f"{BASE_URL}{CHAT_ENDPOINT}",
            params=params
        ) as resp:
            if resp.status != 200:
                print(f"❌ Error: HTTP {resp.status}")
                return
            
            print("\n📨 Response chunks:")
            print("-" * 60)
            
            chunk_count = 0
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        print("\n✅ Stream completed")
                        break
                    try:
                        json_data = json.loads(data)
                        if 'content' in json_data:
                            print(json_data['content'], end='', flush=True)
                            chunk_count += 1
                    except json.JSONDecodeError:
                        print(f"Raw: {data}")
            
            print(f"\n\n📊 Total chunks received: {chunk_count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


# =============================================================================
# Test Cases - Web Search Skills
# =============================================================================

async def test_bing_search(session: aiohttp.ClientSession, token: str):
    """Test Bing web search."""
    await test_sse_chat(
        session, token,
        message="Search Bing for today's AI news",
        test_name="🔍 Bing Search - Today's AI News"
    )


async def test_google_search(session: aiohttp.ClientSession, token: str):
    """Test Google web search."""
    await test_sse_chat(
        session, token,
        message="Search Google for Python asyncio best practices",
        test_name="🔍 Google Search - Python Asyncio"
    )


async def test_duckduckgo_search(session: aiohttp.ClientSession, token: str):
    """Test DuckDuckGo web search."""
    await test_sse_chat(
        session, token,
        message="Search DuckDuckGo for privacy-focused browsers",
        test_name="🔍 DuckDuckGo Search - Privacy Browsers"
    )


async def test_baidu_search(session: aiohttp.ClientSession, token: str):
    """Test Baidu web search (Chinese)."""
    await test_sse_chat(
        session, token,
        message="Search Baidu for 人工智能最新进展",
        test_name="🔍 Baidu Search - 人工智能最新进展"
    )


async def test_multi_engine_search(session: aiohttp.ClientSession, token: str):
    """Test searching across multiple engines."""
    await test_sse_chat(
        session, token,
        message="Compare search results from Bing, Google, and Baidu for 'machine learning frameworks'",
        test_name="🔍 Multi-Engine Search Comparison"
    )


# =============================================================================
# Test Cases - Web Scraping Skills
# =============================================================================

async def test_scrape_webpage(session: aiohttp.ClientSession, token: str):
    """Test web page scraping."""
    await test_sse_chat(
        session, token,
        message="Scrape the content from https://example.com and summarize it",
        test_name="📄 Web Scraping - example.com"
    )


async def test_scrape_news_article(session: aiohttp.ClientSession, token: str):
    """Test scraping a news article."""
    await test_sse_chat(
        session, token,
        message="Find and scrape a recent tech news article about AI, then summarize the key points",
        test_name="📄 News Article Scraping & Summary"
    )


# =============================================================================
# Test Cases - Browser Screenshot
# =============================================================================

async def test_browser_screenshot(session: aiohttp.ClientSession, token: str):
    """Test browser screenshot capability."""
    await test_sse_chat(
        session, token,
        message="Take a screenshot of https://github.com and describe what you see",
        test_name="📸 Browser Screenshot - GitHub"
    )


async def test_screenshot_with_navigation(session: aiohttp.ClientSession, token: str):
    """Test screenshot after navigation."""
    await test_sse_chat(
        session, token,
        message="Navigate to https://news.ycombinator.com, take a screenshot, and tell me the top 3 headlines",
        test_name="📸 Screenshot with Navigation - Hacker News"
    )


# =============================================================================
# Test Cases - File Operations
# =============================================================================

async def test_list_files(session: aiohttp.ClientSession, token: str):
    """Test listing user files."""
    await test_sse_chat(
        session, token,
        message="List all my uploaded files",
        test_name="📁 List User Files"
    )


async def test_read_file(session: aiohttp.ClientSession, token: str):
    """Test reading a file (requires a file to exist)."""
    await test_sse_chat(
        session, token,
        message="Read the content of my file 'test.txt' if it exists",
        test_name="📄 Read File Content"
    )


async def test_file_with_context(session: aiohttp.ClientSession, token: str):
    """Test chat with file context."""
    await test_sse_chat(
        session, token,
        message="Analyze this file and summarize its content",
        file_paths="test_document.txt",
        test_name="📎 Chat with File Context"
    )


async def test_multiple_files(session: aiohttp.ClientSession, token: str):
    """Test chat with multiple files."""
    await test_sse_chat(
        session, token,
        message="Compare these two files and identify the differences",
        file_paths="file1.txt,file2.txt",
        test_name="📎 Multi-File Comparison"
    )


# =============================================================================
# Test Cases - System Execution
# =============================================================================

async def test_python_execution(session: aiohttp.ClientSession, token: str):
    """Test Python code execution."""
    await test_sse_chat(
        session, token,
        message="Execute Python code to calculate the factorial of 10 and print the result",
        test_name="🐍 Python Execution - Factorial"
    )


async def test_shell_command(session: aiohttp.ClientSession, token: str):
    """Test shell command execution."""
    await test_sse_chat(
        session, token,
        message="Run a shell command to show the current directory and list files",
        test_name="🖥️ Shell Command - List Directory"
    )


async def test_data_analysis(session: aiohttp.ClientSession, token: str):
    """Test data analysis with Python."""
    await test_sse_chat(
        session, token,
        message="""Execute Python to:
1. Create a list of 10 random numbers
2. Calculate mean, median, and standard deviation
3. Print the results
        """,
        test_name="🐍 Python Data Analysis"
    )


# =============================================================================
# Test Cases - Complex Multi-Skill Scenarios
# =============================================================================

async def test_research_workflow(session: aiohttp.ClientSession, token: str):
    """Test complex research workflow using multiple skills."""
    await test_sse_chat(
        session, token,
        message="""I need to research the latest developments in LLMs:
1. Search for recent news about large language models
2. Scrape one of the articles you find
3. Summarize the key points
4. Save the summary to a file called 'llm_research.txt'
        """,
        test_name="🔬 Complex Research Workflow"
    )


async def test_web_development_helper(session: aiohttp.ClientSession, token: str):
    """Test web development assistance."""
    await test_sse_chat(
        session, token,
        message="""Help me check the status of a website:
1. Navigate to https://httpbin.org/status/200
2. Take a screenshot
3. Check the HTTP status code
4. Report back what you found
        """,
        test_name="🌐 Web Development Helper"
    )


async def test_chinese_language_support(session: aiohttp.ClientSession, token: str):
    """Test Chinese language support."""
    await test_sse_chat(
        session, token,
        message="""请帮我完成以下任务：
1. 使用百度搜索"Python教程"
2. 找到第一个结果并访问
3. 提取页面主要内容
4. 用中文总结你学到的内容
        """,
        test_name="🇨🇳 Chinese Language Support"
    )


async def test_error_handling(session: aiohttp.ClientSession, token: str):
    """Test error handling with invalid inputs."""
    await test_sse_chat(
        session, token,
        message="Search for information from an invalid URL: not-a-valid-url",
        test_name="⚠️ Error Handling - Invalid URL"
    )


async def test_long_conversation(session: aiohttp.ClientSession, token: str):
    """Test multi-turn conversation context."""
    session_id = f"long_test_{datetime.now().timestamp()}"
    
    print(f"\n{'='*60}")
    print(f"🧪 Multi-Turn Conversation Test")
    print(f"{'='*60}")
    
    messages = [
        "What are the latest trends in AI?",
        "Can you search for more specific information about the first trend you mentioned?",
        "Now scrape one of those articles and give me a summary",
        "Based on what you found, what are the implications for developers?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Turn {i}/{len(messages)} ---")
        print(f"User: {message}")
        
        params = {
            "session_id": session_id,
            "input": message,
            "access_token": token
        }
        
        try:
            async with session.get(f"{BASE_URL}{CHAT_ENDPOINT}", params=params) as resp:
                print("Assistant: ", end='', flush=True)
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data)
                            if 'content' in json_data:
                                print(json_data['content'], end='', flush=True)
                        except json.JSONDecodeError:
                            pass
                print()
        except Exception as e:
            print(f"Error: {e}")


# =============================================================================
# Main Test Runner
# =============================================================================

async def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("🚀 SSE Chat Endpoint Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    async with aiohttp.ClientSession() as session:
        # Get access token
        print("\n🔐 Authenticating...")
        token = await get_access_token(session)
        
        if not token:
            print("❌ Failed to get access token. Please check credentials.")
            return
        
        print("✅ Authentication successful")
        
        # Run test categories
        test_categories = [
            ("Web Search Tests", [
                test_bing_search,
                test_google_search,
                test_duckduckgo_search,
                test_baidu_search,
                test_multi_engine_search,
            ]),
            ("Web Scraping Tests", [
                test_scrape_webpage,
                test_scrape_news_article,
            ]),
            ("Browser Screenshot Tests", [
                test_browser_screenshot,
                test_screenshot_with_navigation,
            ]),
            ("File Operation Tests", [
                test_list_files,
                test_read_file,
                test_file_with_context,
                test_multiple_files,
            ]),
            ("System Execution Tests", [
                test_python_execution,
                test_shell_command,
                test_data_analysis,
            ]),
            ("Complex Workflow Tests", [
                test_research_workflow,
                test_web_development_helper,
                test_chinese_language_support,
                test_error_handling,
            ]),
        ]
        
        for category_name, tests in test_categories:
            print(f"\n{'='*60}")
            print(f"📂 {category_name}")
            print(f"{'='*60}")
            
            for test_func in tests:
                try:
                    await test_func(session, token)
                    await asyncio.sleep(2)  # Brief pause between tests
                except Exception as e:
                    print(f"❌ Test failed: {e}")
        
        # Run long conversation test separately
        print(f"\n{'='*60}")
        print("📂 Multi-Turn Conversation Test")
        print(f"{'='*60}")
        try:
            await test_long_conversation(session, token)
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print(f"\n{'='*60}")
    print("✅ All tests completed!")
    print(f"{'='*60}")


async def run_quick_tests():
    """Run a quick subset of tests."""
    print("=" * 60)
    print("🚀 Quick Test Suite (Subset)")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        token = await get_access_token(session)
        if not token:
            print("❌ Authentication failed")
            return
        
        quick_tests = [
            test_bing_search,
            test_baidu_search,
            test_scrape_webpage,
            test_python_execution,
            test_chinese_language_support,
        ]
        
        for test_func in quick_tests:
            try:
                await test_func(session, token)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"❌ Test failed: {e}")
    
    print("\n✅ Quick tests completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(run_quick_tests())
    else:
        asyncio.run(run_all_tests())
