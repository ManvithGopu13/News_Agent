import aiohttp
import asyncio
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Tuple
import os
import feedparser
from urllib.parse import urljoin, urlparse
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage

class NewsAggregator:
    def __init__(self):
        nvidia_api_key = os.getenv('NVIDIA_API_KEY')
        nvidia_model = os.getenv('NVIDIA_MODEL')
        if not nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY not found in .env file")
        if not nvidia_model:
            raise ValueError("NVIDIA_MODEL not found in .env file")
        self.llm = ChatNVIDIA(model=nvidia_model, nvidia_api_key=nvidia_api_key)
        # Limit concurrent API calls to prevent rate limiting (max 10 at a time)
        self.semaphore = asyncio.Semaphore(10)
        self.upsc_relevant_topics = [
            "government policy", "economy", "international relations",
            "science and technology", "environment", "social issues",
            "polity", "governance", "current affairs india",
            "parliament", "supreme court", "budget", "agriculture",
            "defence", "space", "health", "education", "infrastructure",
            "scheme", "bill", "act", "judgment", "policy", "reform"
        ]
        
    async def fetch_upsc_news(self) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
        """Fetch news from multiple sources relevant to UPSC.
        
        Returns:
            tuple: (list of articles, dictionary mapping source names to their articles)
        """
        news_sources = [
            self._fetch_from_pib(),
            self._fetch_from_the_hindu(),
            self._fetch_from_indian_express(),
            self._fetch_from_times_of_india(),
            self._fetch_from_hindustan_times(),
            self._fetch_from_business_standard(),
            self._fetch_from_livemint(),
            self._fetch_from_web_search()
        ]
        
        results = await asyncio.gather(*news_sources, return_exceptions=True)
        
        # Flatten and combine all news, track by source
        all_news = []
        source_map = {}  # Map source name to list of articles from that source
        
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
                # Group by source
                for article in result:
                    source = article.get('source', 'Unknown')
                    if source not in source_map:
                        source_map[source] = []
                    source_map[source].append(article)
            elif isinstance(result, Exception):
                print(f"Error in news source: {result}")
        
        # Remove duplicates based on title similarity
        unique_news = self._remove_duplicates(all_news)
        
        # Rebuild source_map after removing duplicates
        source_map_clean = {}
        seen_titles = set()
        for article in unique_news:
            title_normalized = re.sub(r'\W+', '', article.get('title', '').lower())
            if title_normalized and title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                source = article.get('source', 'Unknown')
                if source not in source_map_clean:
                    source_map_clean[source] = []
                source_map_clean[source].append(article)
        
        # Filter for UPSC relevance using keywords
        relevant_news = self._filter_upsc_relevant(unique_news)
        
        # Sort by date (most recent first) and limit to 60
        relevant_news.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        final_news = relevant_news[:60]
        
        # Build final source summary from relevant articles
        final_source_map = {}
        for article in final_news:
            source = article.get('source', 'Unknown')
            if source not in final_source_map:
                final_source_map[source] = []
            final_source_map[source].append(article)
        
        print(f"✅ Found {len(final_news)} UPSC-relevant articles from {len(all_news)} total articles")
        
        return final_news, final_source_map
    
    def format_source_summary(self, source_map: Dict[str, List[Dict]]) -> str:
        """Format a summary message showing articles by source with counts and links.
        
        Args:
            source_map: Dictionary mapping source names to their articles
            
        Returns:
            Formatted string message
        """
        if not source_map:
            return "📊 No articles found from any source."
        
        message_parts = ["📊 Articles Found by Source:\n"]
        total_count = 0
        
        # Sort sources by number of articles (descending)
        sorted_sources = sorted(source_map.items(), key=lambda x: len(x[1]), reverse=True)
        
        for source, articles in sorted_sources:
            count = len(articles)
            total_count += count
            message_parts.append(f"\n📰 <b>{source}</b>: {count} article{'s' if count != 1 else ''}")
            
            # Add links for each article (limit to first 10 to avoid message too long)
            displayed_articles = articles[:10]
            for idx, article in enumerate(displayed_articles, 1):
                title = article.get('title', 'Untitled')[:60]  # Limit title length
                url = article.get('url', '')
                if url:
                    # Use HTML link format for Telegram
                    message_parts.append(f"{idx}. <a href='{url}'>{title}</a>")
                else:
                    message_parts.append(f"{idx}. {title}")
            
            if len(articles) > 10:
                message_parts.append(f"... and {len(articles) - 10} more")
        
        message_parts.append(f"\n\n✅ <b>Total: {total_count} UPSC-relevant articles</b>")
        
        return "\n".join(message_parts)

    async def _fetch_from_pib(self) -> List[Dict]:
        """Fetch news from Press Information Bureau using RSS and web scraping."""
        news_items = []
        try:
            # Try RSS feed first
            rss_url = "https://pib.gov.in/rssFeed.aspx"
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries[:30]:
                            news_items.append({
                                'title': entry.get('title', ''),
                                'source': 'PIB India',
                                'url': entry.get('link', ''),
                                'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                            })
        except Exception as e:
            print(f"Error fetching PIB RSS: {e}")
        
        # Also try web scraping
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://pib.gov.in/allRel.aspx"
                async with session.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        articles = soup.find_all('div', class_='content-area')[:20]
                        for article in articles:
                            title_elem = article.find('a')
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                href = title_elem.get('href', '')
                                if title and href:
                                    news_items.append({
                                        'title': title,
                                        'source': 'PIB India',
                                        'url': urljoin('https://pib.gov.in', href),
                                        'date': datetime.now().strftime('%Y-%m-%d')
                                    })
        except Exception as e:
            print(f"Error fetching PIB web: {e}")
        
        return news_items

    async def _fetch_from_the_hindu(self) -> List[Dict]:
        """Fetch news from The Hindu using RSS feed."""
        news_items = []
        try:
            rss_feeds = [
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "https://www.thehindu.com/news/international/feeder/default.rss",
                "https://www.thehindu.com/business/feeder/default.rss"
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_feeds:
                    try:
                        async with session.get(rss_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                for entry in feed.entries[:15]:
                                    news_items.append({
                                        'title': entry.get('title', ''),
                                        'source': 'The Hindu',
                                        'url': entry.get('link', ''),
                                        'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                                    })
                    except Exception as e:
                        print(f"Error fetching The Hindu RSS {rss_url}: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching The Hindu: {e}")
        
        return news_items

    async def _fetch_from_indian_express(self) -> List[Dict]:
        """Fetch news from Indian Express using RSS feed."""
        news_items = []
        try:
            rss_feeds = [
                "https://indianexpress.com/section/india/feed/",
                "https://indianexpress.com/section/world/feed/",
                "https://indianexpress.com/section/business/feed/"
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_feeds:
                    try:
                        async with session.get(rss_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                for entry in feed.entries[:15]:
                                    news_items.append({
                                        'title': entry.get('title', ''),
                                        'source': 'Indian Express',
                                        'url': entry.get('link', ''),
                                        'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                                    })
                    except Exception as e:
                        print(f"Error fetching Indian Express RSS {rss_url}: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching Indian Express: {e}")
        
        return news_items

    async def _fetch_from_times_of_india(self) -> List[Dict]:
        """Fetch news from Times of India using RSS feed."""
        news_items = []
        try:
            rss_feeds = [
                "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",  # India
                "https://timesofindia.indiatimes.com/rssfeeds/296589293.cms",  # World
                "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms"     # Business
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_feeds:
                    try:
                        async with session.get(rss_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                for entry in feed.entries[:15]:
                                    news_items.append({
                                        'title': entry.get('title', ''),
                                        'source': 'Times of India',
                                        'url': entry.get('link', ''),
                                        'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                                    })
                    except Exception as e:
                        print(f"Error fetching TOI RSS {rss_url}: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching Times of India: {e}")
        
        return news_items

    async def _fetch_from_hindustan_times(self) -> List[Dict]:
        """Fetch news from Hindustan Times using RSS feed."""
        news_items = []
        try:
            rss_feeds = [
                "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
                "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
                "https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml"
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_feeds:
                    try:
                        async with session.get(rss_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                for entry in feed.entries[:15]:
                                    news_items.append({
                                        'title': entry.get('title', ''),
                                        'source': 'Hindustan Times',
                                        'url': entry.get('link', ''),
                                        'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                                    })
                    except Exception as e:
                        print(f"Error fetching HT RSS {rss_url}: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching Hindustan Times: {e}")
        
        return news_items

    async def _fetch_from_business_standard(self) -> List[Dict]:
        """Fetch news from Business Standard using RSS feed."""
        news_items = []
        try:
            rss_feeds = [
                "https://www.business-standard.com/rss/economy-106.rss",
                "https://www.business-standard.com/rss/politics-102.rss",
                "https://www.business-standard.com/rss/current-affairs-103.rss"
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_feeds:
                    try:
                        async with session.get(rss_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                for entry in feed.entries[:15]:
                                    news_items.append({
                                        'title': entry.get('title', ''),
                                        'source': 'Business Standard',
                                        'url': entry.get('link', ''),
                                        'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                                    })
                    except Exception as e:
                        print(f"Error fetching BS RSS {rss_url}: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching Business Standard: {e}")
        
        return news_items

    async def _fetch_from_livemint(self) -> List[Dict]:
        """Fetch news from Livemint using RSS feed."""
        news_items = []
        try:
            rss_feeds = [
                "https://www.livemint.com/rss/politics",
                "https://www.livemint.com/rss/economy",
                "https://www.livemint.com/rss/news"
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_feeds:
                    try:
                        async with session.get(rss_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                for entry in feed.entries[:15]:
                                    news_items.append({
                                        'title': entry.get('title', ''),
                                        'source': 'Livemint',
                                        'url': entry.get('link', ''),
                                        'date': self._parse_date(entry.get('published', datetime.now().strftime('%Y-%m-%d')))
                                    })
                    except Exception as e:
                        print(f"Error fetching Livemint RSS {rss_url}: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching Livemint: {e}")
        
        return news_items

    async def _fetch_from_web_search(self) -> List[Dict]:
        """Fetch news using web search for UPSC-relevant queries."""
        news_items = []
        search_queries = [
            "India government policy news today",
            "UPSC current affairs today",
            "India economy news latest",
            "Indian parliament news today",
            "Supreme Court India judgment today",
            "India international relations news",
            "India budget news latest",
            "India agriculture policy news",
            "India science technology news",
            "India environment climate news"
        ]
        
        try:
            # Use DuckDuckGo HTML scraping as fallback (free, no API key needed)
            async with aiohttp.ClientSession() as session:
                for query in search_queries[:5]:  # Limit to avoid too many requests
                    try:
                        # DuckDuckGo search URL
                        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}+site:indiatimes.com+OR+site:thehindu.com+OR+site:indianexpress.com"
                        
                        async with session.get(
                            search_url, 
                            timeout=15,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        ) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Find search results
                                results = soup.find_all('a', class_='result__a')[:5]
                                for result in results:
                                    title = result.get_text(strip=True)
                                    url = result.get('href', '')
                                    if title and url:
                                        # Extract domain as source
                                        domain = urlparse(url).netloc
                                        source = domain.replace('www.', '').split('.')[0].title()
                                        
                                        news_items.append({
                                            'title': title,
                                            'source': source,
                                            'url': url,
                                            'date': datetime.now().strftime('%Y-%m-%d')
                                        })
                        
                        await asyncio.sleep(2)  # Rate limiting
                    except Exception as e:
                        print(f"Error in web search for '{query}': {e}")
                        continue
        except Exception as e:
            print(f"Error in web search: {e}")
        
        return news_items

    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats and return YYYY-MM-DD format."""
        try:
            # Try parsing common RSS date formats
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                # Default to today if parsing fails
                return datetime.now().strftime('%Y-%m-%d')

    def _filter_upsc_relevant(self, news_list: List[Dict]) -> List[Dict]:
        """Filter news articles for UPSC relevance based on keywords."""
        relevant_news = []
        
        for news in news_list:
            title_lower = news.get('title', '').lower()
            # Check if title contains any UPSC-relevant keywords
            if any(topic.lower() in title_lower for topic in self.upsc_relevant_topics):
                relevant_news.append(news)
        
        return relevant_news

    def _remove_duplicates(self, news_list: List[Dict]) -> List[Dict]:
        """Remove duplicate news based on title similarity."""
        unique_news = []
        seen_titles = set()
        
        for news in news_list:
            title_normalized = re.sub(r'\W+', '', news.get('title', '').lower())
            if title_normalized and title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_news.append(news)
        
        return unique_news

    def _prepare_news_for_analysis(self, news_data: List[Dict]) -> List[Dict]:
        """Prepare and normalize news data for analysis.
        
        Returns:
            List of prepared news articles ready for analysis
        """
        if not news_data:
            # If no news fetched, create sample data
            news_data = self._get_sample_news()
        
        # Remove duplicates first
        news_data = self._remove_duplicates(news_data)
        
        # Ensure we analyze at least 50 articles
        if len(news_data) < 50:
            # If we have fewer than 50, use sample news to fill up
            sample_news = self._get_sample_news()
            # Get titles we already have to avoid duplicates
            existing_titles = {re.sub(r'\W+', '', news.get('title', '').lower()) for news in news_data}
            # Add only new articles from sample
            for article in sample_news:
                title_normalized = re.sub(r'\W+', '', article.get('title', '').lower())
                if title_normalized and title_normalized not in existing_titles and len(news_data) < 60:
                    news_data.append(article)
                    existing_titles.add(title_normalized)
        
        # Limit to 60 to ensure we get at least 50 successful analyses
        news_data = news_data[:60]
        return news_data
    
    async def analyze_news(self, news_data: List[Dict], progress_callback=None) -> Dict:
        """Analyze news using NVIDIA LLM for UPSC relevance.
        
        Args:
            news_data: List of news articles to analyze
            progress_callback: Optional async function to call with progress updates (current, total, message)
            
        Returns:
            Dictionary with analysis results and actual article count
        """
        # Prepare news data (normalize, remove duplicates, ensure minimum count)
        news_data = self._prepare_news_for_analysis(news_data)
        total_articles = len(news_data)
        
        print(f"📊 Starting PARALLEL analysis of {total_articles} articles...")
        if progress_callback:
            await progress_callback(0, total_articles, f"Starting parallel analysis of {total_articles} articles...")
        
        # Process ALL articles in parallel for maximum speed
        tasks = []
        for idx, news in enumerate(news_data):
            task = self._analyze_single_article(
                news, 
                article_num=idx + 1,
                total=total_articles,
                progress_callback=None  # Don't update progress in individual articles
            )
            tasks.append(task)
        
        # Track progress as tasks complete
        analyzed_articles = []
        completed = 0
        failed = 0
        
        # Process results as they complete using asyncio.as_completed for real-time updates
        if progress_callback:
            # Use as_completed to get results as they finish
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    if result is not None:
                        analyzed_articles.append(result)
                        completed += 1
                    else:
                        failed += 1
                    
                    processed = completed + failed
                    status_msg = f"✅ Completed: {completed} | ❌ Failed: {failed} | 📊 Progress: {processed}/{total_articles}"
                    await progress_callback(processed, total_articles, status_msg)
                except Exception as e:
                    failed += 1
                    print(f"❌ Error analyzing article: {e}")
                    processed = completed + failed
                    status_msg = f"✅ Completed: {completed} | ❌ Failed: {failed} | 📊 Progress: {processed}/{total_articles}"
                    await progress_callback(processed, total_articles, status_msg)
        else:
            # If no callback, use gather for efficiency
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    print(f"❌ Error analyzing article {idx + 1}/{total_articles}: {result}")
                elif result is not None:
                    analyzed_articles.append(result)
                    completed += 1
                else:
                    failed += 1
        
        print(f"✅ Analysis complete! Successfully analyzed {len(analyzed_articles)}/{total_articles} articles")
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_articles': len(analyzed_articles),
            'articles': analyzed_articles
        }

    async def _analyze_single_article(self, news: Dict, article_num: int, total: int, progress_callback=None) -> Dict:
        """Analyze a single news article (used for parallel processing).
        
        Args:
            news: News article dictionary to analyze
            article_num: Article number for progress tracking
            total: Total number of articles
            progress_callback: Optional async function to call with progress updates (currently unused)
        """
        # Use semaphore to limit concurrent API calls
        async with self.semaphore:
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    print(f"📝 Analyzing article {article_num}/{total}: {news.get('title', 'Unknown')[:60]}...")
                    
                    prompt = f"""Analyze this news article for UPSC Civil Services preparation:

Title: {news['title']}
Source: {news.get('source', 'Unknown')}

Provide a comprehensive analysis in the following JSON-like format (use clear section headers):

**UPSC Relevance:**
[Explain why this is important for UPSC - mention specific GS papers]

**Key Points:**
[Bullet points of main information - one per line with •]

**Concepts to Understand:**
[Related concepts and background knowledge needed - one per line with •]

**Prelims Perspective:**
[Provide 2-3 sample questions with answers - format as Q1, Q2, etc.]

**Mains Perspective:**
[Provide 2 questions with brief answer outlines - format as Q1, Q2]

**Static Portion:**
[Related constitutional articles, acts, or historical background]

Keep the analysis detailed but focused on exam preparation."""

                    response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                    
                    analysis = response.content
                    
                    # Parse analysis into structured format
                    parsed_analysis = self._parse_analysis(analysis)
                    
                    result = {
                        'title': news['title'],
                        'source': news.get('source', 'Unknown'),
                        'url': news.get('url', ''),
                        'date': news.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'analysis': analysis,
                        'parsed': parsed_analysis
                    }
                    
                    print(f"✅ Completed {article_num}/{total}")
                    
                    return result
                    
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit error (429)
                    if '429' in error_str or 'Too Many Requests' in error_str:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            print(f"⚠️ Rate limited for article {article_num}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Rate limit error for article {article_num}/{total} after {max_retries} attempts: {e}")
                            return None
                    else:
                        print(f"❌ Error analyzing article {article_num}/{total}: {e}")
                        return None
            
            return None
    
    def _parse_analysis(self, analysis_text: str) -> Dict:
        """Parse analysis text into structured format."""
        parsed = {
            'upsc_relevance': '',
            'key_points': [],
            'concepts': [],
            'prelims_questions': [],
            'mains_questions': [],
            'static_portion': ''
        }
        
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Detect section headers
            if 'upsc relevance' in line_stripped.lower():
                current_section = 'upsc_relevance'
                continue
            elif 'key points' in line_stripped.lower():
                current_section = 'key_points'
                continue
            elif 'concepts to understand' in line_stripped.lower():
                current_section = 'concepts'
                continue
            elif 'prelims' in line_stripped.lower():
                current_section = 'prelims_questions'
                continue
            elif 'mains' in line_stripped.lower():
                current_section = 'mains_questions'
                continue
            elif 'static portion' in line_stripped.lower():
                current_section = 'static_portion'
                continue
            
            # Add content to current section
            if current_section:
                if current_section in ['key_points', 'concepts']:
                    if line_stripped.startswith('•') or line_stripped.startswith('-'):
                        parsed[current_section].append(line_stripped.lstrip('•- '))
                    elif line_stripped.startswith(('Q', 'q')) and ':' in line_stripped:
                        parsed[current_section].append(line_stripped)
                elif current_section in ['prelims_questions', 'mains_questions']:
                    if line_stripped.startswith(('Q', 'q')) or any(char.isdigit() for char in line_stripped[:3]):
                        parsed[current_section].append(line_stripped)
                    elif parsed[current_section] and line_stripped:
                        # Append to last question if it exists
                        parsed[current_section][-1] += ' ' + line_stripped
                else:
                    if parsed[current_section]:
                        parsed[current_section] += ' ' + line_stripped
                    else:
                        parsed[current_section] = line_stripped
        
        return parsed

    def _get_sample_news(self) -> List[Dict]:
        """Get sample news if API fails."""
        today = datetime.now().strftime('%Y-%m-%d')
        return [
            {
                'title': 'India\'s GDP Growth Projections Revised',
                'source': 'Economic Times',
                'url': 'https://example.com/news1',
                'date': today
            },
            {
                'title': 'New Environmental Protection Bill Introduced in Parliament',
                'source': 'The Hindu',
                'url': 'https://example.com/news2',
                'date': today
            },
            {
                'title': 'India-US Strategic Partnership: Recent Developments',
                'source': 'Indian Express',
                'url': 'https://example.com/news3',
                'date': today
            },
            {
                'title': 'Supreme Court Ruling on Article 370',
                'source': 'PIB India',
                'url': 'https://example.com/news4',
                'date': today
            },
            {
                'title': 'ISRO Successfully Launches Communication Satellite',
                'source': 'PTI',
                'url': 'https://example.com/news5',
                'date': today
            }
        ]