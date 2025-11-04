import PyPDF2
import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage
from typing import Dict, List
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
        self.irrelevant_keywords = [
            'advertisement', 'classified', 'matrimonial', 'horoscope',
            'sports scores', 'movie review', 'entertainment gossip',
            'personal advice column', 'comic strip', 'crossword'
        ]
        
    async def analyze_newspaper(self, pdf_path: str) -> Dict:
        """Analyze a newspaper PDF and extract UPSC-relevant content."""
        # Extract text from PDF
        text_content = self._extract_text_from_pdf(pdf_path)
        
        # Split into articles
        articles = self._segment_articles(text_content)
        
        # Filter and analyze relevant articles
        analyzed_articles = await self._filter_and_analyze(articles)
        
        return {
            'total_articles': len(analyzed_articles),
            'articles': analyzed_articles
        }

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            raise
        
        return text

    def _segment_articles(self, text: str) -> List[str]:
        """Segment text into individual articles."""
        # Simple segmentation based on multiple newlines or common delimiters
        # In production, use more sophisticated NLP techniques
        
        articles = []
        current_article = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_article:
                    articles.append('\n'.join(current_article))
                    current_article = []
            else:
                current_article.append(line)
        
        if current_article:
            articles.append('\n'.join(current_article))
        
        # Filter out very short segments (likely headers/footers)
        articles = [a for a in articles if len(a.split()) > 50]
        
        return articles

    async def _filter_and_analyze(self, articles: List[str]) -> List[Dict]:
        """Filter irrelevant articles and analyze relevant ones."""
        analyzed = []
        
        for idx, article in enumerate(articles[:20]):  # Limit to first 20 articles
            # Quick relevance check
            if self._is_likely_irrelevant(article):
                continue
            
            try:
                # Use NVIDIA LLM to determine relevance and analyze
                analysis = await self._analyze_single_article(article)
                
                if analysis and analysis.get('is_relevant'):
                    analyzed.append({
                        'article_number': idx + 1,
                        'original_text': article[:500] + '...' if len(article) > 500 else article,
                        'summary': analysis.get('summary', ''),
                        'simplified_explanation': analysis.get('simplified', ''),
                        'key_concepts': analysis.get('key_concepts', []),
                        'upsc_relevance': analysis.get('upsc_relevance', ''),
                        'prelims_questions': analysis.get('prelims_questions', []),
                        'mains_questions': analysis.get('mains_questions', []),
                        'related_topics': analysis.get('related_topics', [])
                    })
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error analyzing article {idx}: {e}")
                continue
        
        return analyzed

    def _is_likely_irrelevant(self, article: str) -> bool:
        """Quick check for obviously irrelevant content."""
        article_lower = article.lower()
        
        # Check for irrelevant keywords
        for keyword in self.irrelevant_keywords:
            if keyword in article_lower:
                return True
        
        # Check if article is too short
        if len(article.split()) < 50:
            return True
        
        return False

    async def _analyze_single_article(self, article: str) -> Dict:
        """Analyze a single article for UPSC relevance."""
        prompt = f"""Analyze this newspaper article for UPSC Civil Services preparation:

Article Text:
{article[:3000]}  # Limit to avoid token issues

Provide analysis in the following JSON-like format:

1. Is this article relevant for UPSC preparation? (YES/NO)
2. If relevant, provide:
   - Brief Summary (3-4 sentences)
   - Simplified Explanation (explain complex terms in simple language)
   - Key Concepts (list important concepts mentioned)
   - UPSC Relevance (which papers/topics this relates to)
   - 2 Potential Prelims Questions with answers
   - 2 Potential Mains Questions with brief answer outlines
   - Related Topics to study

Focus on:
- Government policies and schemes
- Economic developments
- International relations
- Scientific achievements
- Social issues
- Constitutional matters
- Environmental issues

Ignore: Sports entertainment, advertisements, personal stories without policy relevance."""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            response_text = response.content
            
            # Parse the response
            analysis = self._parse_analysis_response(response_text)
            
            return analysis
            
        except Exception as e:
            print(f"Error in NVIDIA LLM analysis: {e}")
            return None

    def _parse_analysis_response(self, response: str) -> Dict:
        """Parse NVIDIA LLM's response into structured data."""
        # This is a simplified parser
        # In production, use more robust parsing or structured output
        
        is_relevant = 'yes' in response.lower().split('\n')[0]
        
        if not is_relevant:
            return {'is_relevant': False}
        
        # Extract sections (simplified parsing)
        sections = {
            'is_relevant': True,
            'summary': '',
            'simplified': '',
            'key_concepts': [],
            'upsc_relevance': '',
            'prelims_questions': [],
            'mains_questions': [],
            'related_topics': []
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'summary' in line.lower():
                current_section = 'summary'
            elif 'simplified' in line.lower():
                current_section = 'simplified'
            elif 'key concept' in line.lower():
                current_section = 'key_concepts'
            elif 'upsc relevance' in line.lower():
                current_section = 'upsc_relevance'
            elif 'prelims' in line.lower():
                current_section = 'prelims_questions'
            elif 'mains' in line.lower():
                current_section = 'mains_questions'
            elif 'related topic' in line.lower():
                current_section = 'related_topics'
            elif current_section and line:
                if current_section in ['key_concepts', 'prelims_questions', 'mains_questions', 'related_topics']:
                    sections[current_section].append(line)
                else:
                    sections[current_section] += line + ' '
        
        return sections