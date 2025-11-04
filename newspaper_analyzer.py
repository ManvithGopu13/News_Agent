import PyPDF2
import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage
from typing import Dict, List, Optional, Callable
import asyncio

class NewspaperAnalyzer:
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
        self.irrelevant_keywords = [
            'advertisement', 'classified', 'matrimonial', 'horoscope',
            'sports scores', 'movie review', 'entertainment gossip',
            'personal advice column', 'comic strip', 'crossword', 'weather forecast',
            'stock market update', 'celebrity news', 'fashion', 'recipe',
            'cricket', 'football', 'tennis', 'match', 'tournament', 'sports',
            'movie', 'actor', 'actress', 'bollywood', 'hollywood', 'trailer',
            'restaurant review', 'food review', 'restaurant', 'hotel', 'travelogue',
            'obituary', 'birthday', 'anniversary', 'wedding', 'party'
        ]
        # High-priority UPSC relevant topics - articles must mention these
        self.upsc_critical_topics = [
            "government policy", "government scheme", "government program",
            "cabinet decision", "ministry", "parliament", "lok sabha", "rajya sabha",
            "supreme court", "high court", "judgment", "verdict", "constitutional",
            "budget", "economic survey", "finance", "reserve bank", "rbi",
            "international relations", "diplomacy", "foreign policy", "bilateral",
            "multilateral", "united nations", "world bank", "imf", "who",
            "environment", "climate change", "pollution", "conservation",
            "science and technology", "isro", "nasa", "space", "research",
            "health policy", "medical", "disease", "vaccine", "public health",
            "education policy", "skill development", "university", "board",
            "agriculture", "farmer", "crop", "irrigation", "food security",
            "infrastructure", "transport", "railway", "highway", "airport",
            "defence", "military", "security", "border", "nuclear",
            "social issue", "poverty", "employment", "unemployment", "welfare",
            "scheme", "yojana", "initiative", "mission", "program",
            "bill", "act", "law", "legislation", "ordinance",
            "judgment", "petition", "case", "court", "legal",
            "policy", "reform", "regulation", "committee", "commission",
            "constitutional amendment", "fundamental rights", "directive principles",
            "panchayati raj", "urban local bodies", "governance"
        ]
        # Secondary topics - these alone aren't enough, must be combined with critical topics
        self.upsc_secondary_topics = [
            "economy", "economic", "gdp", "inflation", "trade", "export", "import",
            "social", "society", "development", "growth", "reform"
        ]
        
    async def analyze_newspaper(self, pdf_path: str, progress_callback: Optional[Callable] = None) -> Dict:
        """Analyze a newspaper PDF and extract UPSC-relevant content.
        
        Args:
            pdf_path: Path to the PDF file
            progress_callback: Optional async function to call with progress updates (current, total, message)
        """
        # Step 1: Extract text from PDF
        if progress_callback:
            await progress_callback(0, 100, "📖 Extracting text from PDF...")
        
        text_content = self._extract_text_from_pdf(pdf_path)
        
        # Step 2: Split into articles
        if progress_callback:
            await progress_callback(10, 100, "📰 Segmenting articles...")
        
        articles = self._segment_articles(text_content)
        total_found = len(articles)
        
        print(f"📊 Found {total_found} potential articles in the newspaper")
        if progress_callback:
            await progress_callback(20, 100, f"📊 Found {total_found} potential articles in the newspaper")
        
        # Step 3: Quick filter for obviously irrelevant articles
        if progress_callback:
            await progress_callback(25, 100, "🔍 Performing quick relevance filtering...")
        
        potentially_relevant = self._quick_relevance_filter(articles)
        potentially_relevant_count = len(potentially_relevant)
        
        filtered_out = total_found - potentially_relevant_count
        print(f"🔍 Strict filtering: {filtered_out} articles filtered out (not highly relevant)")
        print(f"✅ {potentially_relevant_count} articles passed initial strict relevance check")
        if progress_callback:
            await progress_callback(30, 100, f"🔍 Strict filtering applied:\n📊 Total: {total_found} | ❌ Filtered: {filtered_out}\n✅ Passed: {potentially_relevant_count}\n\n📝 Starting detailed UPSC relevance analysis...")
        
        # Step 4: Parallel analysis of all potentially relevant articles
        analyzed_articles = await self._analyze_articles_parallel(
            potentially_relevant,
            total_found=total_found,
            progress_callback=progress_callback
        )
        
        relevant_count = len(analyzed_articles)
        rejected_count = potentially_relevant_count - relevant_count
        print(f"✅ Analysis complete! {relevant_count}/{potentially_relevant_count} articles are HIGHLY RELEVANT for UPSC")
        print(f"❌ Rejected: {rejected_count} articles (not important enough)")
        
        if progress_callback:
            await progress_callback(95, 100, f"✅ Strict UPSC relevance analysis complete!\n📊 Total found: {total_found}\n🔍 Analyzed: {potentially_relevant_count}\n✅ Highly relevant: {relevant_count}\n❌ Rejected: {rejected_count}")
        
        return {
            'total_articles_found': total_found,
            'potentially_relevant': potentially_relevant_count,
            'total_articles': relevant_count,
            'articles': analyzed_articles
        }

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"📄 PDF has {total_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text += page.extract_text() + "\n\n"
                    if (page_num + 1) % 10 == 0:
                        print(f"   Extracted {page_num + 1}/{total_pages} pages...")
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            raise
        
        return text

    def _segment_articles(self, text: str) -> List[str]:
        """Segment text into individual articles."""
        articles = []
        current_article = []
        lines = text.split('\n')
        
        # Enhanced segmentation
        for line in lines:
            line = line.strip()
            if not line:
                if current_article and len(' '.join(current_article).split()) > 30:
                    articles.append(' '.join(current_article))
                    current_article = []
            else:
                # Check if this might be a new article (starts with common patterns)
                if current_article and (
                    line.isupper() or 
                    any(line.startswith(pattern) for pattern in ['By ', 'NEW DELHI', 'MUMBAI', 'KOLKATA', 'CHENNAI'])
                ) and len(current_article) > 5:
                    # Save current article and start new one
                    if len(' '.join(current_article).split()) > 30:
                        articles.append(' '.join(current_article))
                    current_article = [line]
                else:
                    current_article.append(line)
        
        if current_article and len(' '.join(current_article).split()) > 30:
            articles.append(' '.join(current_article))
        
        # Filter out very short segments (likely headers/footers)
        articles = [a for a in articles if len(a.split()) > 50]
        
        return articles

    def _quick_relevance_filter(self, articles: List[str]) -> List[str]:
        """Quick filter to remove obviously irrelevant articles.
        
        Uses strict criteria: must have at least 2 critical UPSC topics or
        1 critical + 2 secondary topics to pass initial filter.
        """
        relevant = []
        
        for article in articles:
            article_lower = article.lower()
            
            # Skip if contains irrelevant keywords
            if any(keyword in article_lower for keyword in self.irrelevant_keywords):
                continue
            
            # Count how many critical topics are mentioned
            critical_matches = sum(1 for topic in self.upsc_critical_topics if topic in article_lower)
            secondary_matches = sum(1 for topic in self.upsc_secondary_topics if topic in article_lower)
            
            # Strict criteria: Need at least 2 critical topics OR 1 critical + 2 secondary
            if critical_matches >= 2 or (critical_matches >= 1 and secondary_matches >= 2):
                # Additional check: article must be substantial (at least 100 words)
                if len(article.split()) >= 100:
                    relevant.append(article)
        
        return relevant

    async def _analyze_articles_parallel(
        self, 
        articles: List[str], 
        total_found: int,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Analyze all articles in parallel."""
        total_articles = len(articles)
        
        if total_articles == 0:
            return []
        
        print(f"📊 Starting PARALLEL analysis of {total_articles} articles...")
        if progress_callback:
            await progress_callback(30, 100, f"🤖 Starting parallel analysis of {total_articles} articles...")
        
        # Create tasks for parallel processing
        tasks = []
        for idx, article in enumerate(articles):
            task = self._analyze_single_article_parallel(
                article,
                article_num=idx + 1,
                total=total_articles,
                progress_callback=progress_callback
            )
            tasks.append(task)
        
        # Execute all tasks in parallel
        analyzed_articles = []
        completed = 0
        failed = 0
        
        # Process results as they complete using asyncio.as_completed for real-time updates
        if progress_callback:
            # Use as_completed to get results as they finish
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    if result is not None and result.get('is_relevant'):
                        analyzed_articles.append(result)
                        completed += 1
                    elif result is not None:
                        # Article was analyzed but not relevant
                        completed += 1
                    else:
                        failed += 1
                    
                    processed = completed + failed
                    progress_pct = 30 + int((processed / total_articles) * 65)  # 30-95% range
                    status_msg = (
                        f"📊 Progress: {processed}/{total_articles} articles processed\n"
                        f"✅ Relevant: {len(analyzed_articles)} | ❌ Failed: {failed}\n"
                        f"📰 Total found: {total_found} | 🔍 Analyzing: {total_articles}"
                    )
                    await progress_callback(progress_pct, 100, status_msg)
                except Exception as e:
                    failed += 1
                    print(f"❌ Unexpected error: {e}")
                    processed = completed + failed
                    progress_pct = 30 + int((processed / total_articles) * 65)
                    if progress_callback:
                        status_msg = (
                            f"📊 Progress: {processed}/{total_articles} articles processed\n"
                            f"✅ Relevant: {len(analyzed_articles)} | ❌ Failed: {failed}"
                        )
                        await progress_callback(progress_pct, 100, status_msg)
        else:
            # If no callback, use gather for efficiency
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                    print(f"❌ Error analyzing article: {result}")
                elif result is not None and result.get('is_relevant'):
                    analyzed_articles.append(result)
                    completed += 1
                elif result is not None:
                    completed += 1
                else:
                    failed += 1
        
        return analyzed_articles

    async def _analyze_single_article_parallel(
        self,
        article: str,
        article_num: int,
        total: int,
        progress_callback: Optional[Callable] = None
    ) -> Optional[Dict]:
        """Analyze a single article (used for parallel processing).
        
        Args:
            article: Article text to analyze
            article_num: Article number for progress tracking
            total: Total number of articles
            progress_callback: Optional async function to call with progress updates
        """
        # Use semaphore to limit concurrent API calls
        async with self.semaphore:
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    # Truncate article if too long (limit to ~3000 chars to avoid token limits)
                    article_text = article[:3000] if len(article) > 3000 else article
                    
                    prompt = f"""Analyze this newspaper article for UPSC Civil Services preparation.

IMPORTANT: Be STRICT about relevance. Only mark as relevant if the article is HIGHLY IMPORTANT for UPSC preparation.

Article Text:
{article_text}

**Strict Relevance Criteria:**
Mark as relevant ONLY if the article discusses:
1. Government policies, schemes, or programs (NEW or UPDATES to existing ones)
2. Parliamentary proceedings, bills, acts, or constitutional matters
3. Important Supreme Court/High Court judgments with constitutional or policy implications
4. Budget, economic policies, RBI decisions, or major economic reforms
5. Significant international relations, diplomacy, or multilateral agreements
6. Major scientific achievements, space missions, or technology initiatives by government
7. Environmental policies, climate change actions, or conservation programs
8. Health policies, public health programs, or major health initiatives
9. Education policies, skill development programs, or educational reforms
10. Agriculture policies, farmer welfare schemes, or food security measures
11. Infrastructure projects of national importance
12. Defence, security, or strategic matters
13. Social welfare schemes or poverty alleviation programs
14. Governance reforms, institutional changes, or administrative decisions

**Mark as NOT RELEVANT if:**
- It's just a news update without policy/governance significance
- Local news without national implications
- Routine administrative decisions without broader impact
- Business/corporate news without government policy connection
- Opinion pieces without factual policy content
- Event coverage without policy/governance context
- Sports, entertainment, lifestyle, or celebrity news
- General economic news without policy implications
- Personal stories without policy relevance

Provide analysis in the following format with clear section headers:

**Relevance Check:**
STRICTLY YES or NO - Is this article HIGHLY RELEVANT for UPSC preparation?
(Only YES if it meets the strict criteria above)

**Summary:**
[Brief summary in 3-4 sentences ONLY if relevant]

**Simplified Explanation:**
[Explain complex terms and concepts in simple language ONLY if relevant]

**Key Concepts:**
[Important concepts mentioned - one per line with • ONLY if relevant]

**UPSC Relevance:**
[Which GS papers/topics this relates to - ONLY if relevant]

**Prelims Questions:**
[2 potential Prelims questions with answers - format as Q1, Q2 ONLY if relevant]

**Mains Questions:**
[2 potential Mains questions with brief answer outlines - format as Q1, Q2 ONLY if relevant]

**Related Topics:**
[Related topics to study - one per line with • ONLY if relevant]

Remember: BE STRICT. If the article is not highly important for UPSC, mark it as NOT RELEVANT."""

                    response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                    
                    response_text = response.content
                    
                    # Parse the response
                    analysis = self._parse_analysis_response(response_text)
                    
                    if analysis and analysis.get('is_relevant'):
                        analysis['article_number'] = article_num
                        analysis['original_text'] = article[:500] + '...' if len(article) > 500 else article
                    
                    return analysis
                    
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

    def _parse_analysis_response(self, response: str) -> Dict:
        """Parse NVIDIA LLM's response into structured data.
        
        Uses strict parsing - only marks as relevant if explicitly stated as YES.
        """
        if not response:
            return {'is_relevant': False}
        
        lines = response.split('\n')
        response_lower = response.lower()
        
        # STRICT relevance check - look for explicit YES or NO
        relevance_line = ''
        for line in lines[:15]:  # Check first 15 lines for relevance section
            line_lower = line.lower().strip()
            if 'relevance check' in line_lower or ('relevance' in line_lower and 'check' in line_lower):
                # Get the next few lines after "Relevance Check" header
                idx = lines.index(line)
                for next_line in lines[idx:idx+5]:
                    if next_line.strip() and 'relevance' not in next_line.lower():
                        relevance_line = next_line.lower()
                        break
                if relevance_line:
                    break
            elif 'relevant' in line_lower and any(word in line_lower for word in ['yes', 'no', 'strictly']):
                relevance_line = line_lower
                break
        
        # Check for explicit NO indicators first (be conservative)
        no_indicators = [
            'not relevant', 'irrelevant', 'not highly relevant',
            'no', 'strictly no', 'mark as not', 'not important'
        ]
        
        if any(indicator in relevance_line for indicator in no_indicators):
            return {'is_relevant': False}
        
        if any(indicator in response_lower[:300] for indicator in ['not relevant', 'irrelevant', 'strictly no']):
            return {'is_relevant': False}
        
        # Check for explicit YES (must be clear)
        yes_indicators = ['strictly yes', 'yes', 'highly relevant', 'relevant']
        is_relevant = any(indicator in relevance_line for indicator in yes_indicators)
        
        # Additional strict check: if there's no clear YES in relevance section, check overall
        if not is_relevant:
            # Look for YES elsewhere in first 200 chars
            first_part = response_lower[:200]
            if 'yes' in first_part and 'no' not in first_part[:50]:
                # But only if it's clearly about relevance
                if any(word in first_part for word in ['relevant', 'relevance']):
                    is_relevant = True
        
        # Final strict check: if ambiguous or unclear, default to NOT relevant
        if not is_relevant or len(response) < 150:
            return {'is_relevant': False}
        
        # If marked as relevant but has very little content, be suspicious
        if 'summary' not in response_lower and len(response) < 300:
            return {'is_relevant': False}
        
        # Extract sections
        sections = {
            'is_relevant': True,
            'summary': '',
            'simplified_explanation': '',
            'key_concepts': [],
            'upsc_relevance': '',
            'prelims_questions': [],
            'mains_questions': [],
            'related_topics': []
        }
        
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Detect section headers
            line_lower = line_stripped.lower()
            if 'summary' in line_lower and 'key' not in line_lower:
                current_section = 'summary'
                continue
            elif 'simplified' in line_lower or 'explanation' in line_lower:
                current_section = 'simplified_explanation'
                continue
            elif 'key concept' in line_lower:
                current_section = 'key_concepts'
                continue
            elif 'upsc relevance' in line_lower:
                current_section = 'upsc_relevance'
                continue
            elif 'prelims' in line_lower and 'question' in line_lower:
                current_section = 'prelims_questions'
                continue
            elif 'mains' in line_lower and 'question' in line_lower:
                current_section = 'mains_questions'
                continue
            elif 'related topic' in line_lower:
                current_section = 'related_topics'
                continue
            elif 'relevance check' in line_lower:
                continue  # Skip relevance check line
            
            # Add content to current section
            if current_section:
                if current_section in ['key_concepts', 'related_topics']:
                    if line_stripped.startswith(('•', '-', '*')):
                        sections[current_section].append(line_stripped.lstrip('•-* '))
                    elif line_stripped and not line_stripped[0].isdigit():
                        sections[current_section].append(line_stripped)
                elif current_section in ['prelims_questions', 'mains_questions']:
                    if line_stripped.startswith(('Q', 'q')) or any(char.isdigit() for char in line_stripped[:3]):
                        sections[current_section].append(line_stripped)
                    elif sections[current_section] and line_stripped:
                        # Append to last question if it exists
                        sections[current_section][-1] += ' ' + line_stripped
                else:
                    if sections[current_section]:
                        sections[current_section] += ' ' + line_stripped
                    else:
                        sections[current_section] = line_stripped
        
        return sections