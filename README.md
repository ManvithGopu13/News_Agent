# UPSC News Agent Telegram Bot 🎓📰

An intelligent Telegram bot that helps UPSC Civil Services aspirants stay updated with relevant current affairs through automated news aggregation, analysis, and PDF generation. The bot uses NVIDIA LLM via LangChain for high-speed parallel analysis of news articles.

## 🚀 Key Features

### 1. Comprehensive News Aggregation
- **Multiple Source Integration**: Automatically fetches news from 8+ major Indian news sources:
  - **PIB India** (Press Information Bureau) - Official government releases
  - **The Hindu** - National, International, Business news
  - **Indian Express** - India, World, Business sections
  - **Times of India** - Comprehensive coverage
  - **Hindustan Times** - Multi-section news
  - **Business Standard** - Economy, Politics, Current Affairs
  - **Livemint** - Politics, Economy, News
  - **Web Search** - Fallback for additional UPSC-relevant articles

### 2. Source-Wise Article Summary
- **Real-time Article Count**: Shows exactly how many articles were found from each source
- **Clickable Links**: All articles include clickable links for quick access
- **Organized Display**: Sources sorted by article count with detailed breakdown
- **Smart Filtering**: Automatically filters for UPSC-relevant content using keyword matching

### 3. High-Speed Parallel Analysis
- **Parallel Processing**: Analyzes up to 60 articles simultaneously for maximum speed
- **Progress Tracking**: Real-time progress updates showing:
  - Current progress (X/Total articles)
  - Successfully completed count
  - Failed attempts count
  - Live status updates via Telegram
- **Rate Limiting**: Intelligent semaphore-based concurrency control (max 10 concurrent requests)
- **Retry Logic**: Automatic retry with exponential backoff for rate limit errors (429)
- **Minimum Guarantee**: Ensures analysis of at least 50 articles (fills with sample if needed)

### 4. Comprehensive PDF Reports
The generated PDF is organized into 7 major sections for easy studying:

1. **📋 All Topics Covered** - Complete list of all analyzed articles with sources and dates
2. **🎯 UPSC Relevance - All Topics** - Why each topic matters for UPSC (GS paper-wise)
3. **🔑 Key Points - All Topics** - Main information from each article
4. **📚 Concepts to Understand - All Topics** - Related concepts and background knowledge
5. **📝 Prelims Perspective - All Questions** - Sample Prelims questions with answers
6. **✍️ Mains Perspective - All Questions** - Mains questions with answer outlines
7. **📜 Static Portion - All Topics** - Constitutional articles, acts, historical background

### 5. Newspaper PDF Analysis with Strict UPSC Relevance Filtering
- Upload any newspaper PDF file (up to 20 MB)
- **Two-Phase Strict Filtering**:
  - **Phase 1**: Quick keyword-based filter using 40+ critical UPSC topics
    - Requires minimum 2 critical topics OR 1 critical + 2 secondary topics
    - Filters out sports, entertainment, lifestyle, local news, etc.
  - **Phase 2**: AI-powered relevance analysis for each article
    - Only highly relevant articles pass (strict criteria)
    - Rejects routine news, local events, business news without policy connections
- **Real-time Progress Tracking**:
  - Shows total articles found
  - Displays filtered count (articles removed in phase 1)
  - Shows analyzed count (articles checked in phase 2)
  - Displays final highly relevant count (kept articles)
  - Rejected count (not important enough)
- **Parallel Processing**: Fast analysis of all articles simultaneously
- Provides simplified explanations and key concepts
- Generates potential exam questions (Prelims & Mains)
- Creates a cleaned, analyzed PDF with only highly relevant articles

### 6. Advanced Features
- **Duplicate Detection**: Automatically removes duplicate articles based on title similarity
- **UPSC Relevance Filtering**: Keyword-based filtering for exam-relevant topics
- **HTML Sanitization**: Properly handles HTML content for PDF generation
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Progress Persistence**: Progress updates persist even if individual articles fail

## 📋 Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (get from @BotFather on Telegram)
- NVIDIA API Key and Model Name (for LLM inference)
- Active internet connection for news fetching

## 🛠️ Installation Steps

### 1. Clone or Download the Project
```bash
mkdir upsc_news_bot
cd upsc_news_bot
# Copy all project files here
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Required Packages:**
- `python-telegram-bot==20.7` - Telegram bot framework
- `langchain-nvidia-ai-endpoints` - NVIDIA LLM integration
- `langchain-core` - Core LangChain functionality
- `aiohttp==3.9.1` - Async HTTP client for web scraping
- `beautifulsoup4==4.12.2` - HTML parsing
- `feedparser==6.0.10` - RSS feed parsing
- `PyPDF2==3.0.1` - PDF reading
- `reportlab==4.0.7` - PDF generation
- `python-dotenv==1.0.0` - Environment variable management

### 3. Configure Environment Variables

Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=your_model_name_here
```

**Getting your Telegram Bot Token:**
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token provided

**Getting your NVIDIA API Key:**
1. Visit NVIDIA AI Playground or API portal
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key and copy it
5. Note your model name (e.g., `meta/llama-3-70b-instruct`)

### 4. Run the Bot
```bash
python main.py
```

You should see: `Bot started successfully!`

## 📱 Usage Guide

### Starting the Bot
1. Open Telegram and search for your bot (use the username you created)
2. Send `/start` to see the welcome message

### Getting Daily News Analysis

Send the message:
```
news
```

**What happens:**
1. 📊 **Gathering Phase** (10-30 seconds)
   - Fetches news from all configured sources
   - Removes duplicates
   - Filters for UPSC relevance

2. 📰 **Source Summary** (shown immediately)
   - Displays article count by source
   - Shows clickable links to all articles
   - Example:
     ```
     📰 PIB India: 8 articles
     1. [Clickable link to article]
     2. [Clickable link to article]
     ...
     ```

3. 🤖 **Analysis Phase** (2-5 minutes)
   - Real-time progress updates:
     ```
     📊 Progress: 15/36
     ✅ Completed: 12 | ❌ Failed: 3 | 📊 Progress: 15/36
     ```
   - Parallel processing for speed
   - Automatic retry on failures

4. 📄 **PDF Generation** (10-30 seconds)
   - Creates organized PDF with all sections
   - Professional formatting

5. ✅ **Delivery**
   - PDF sent to your Telegram chat
   - Includes summary statistics

### Analyzing a Newspaper PDF

1. **Upload PDF** to the bot in Telegram (max 20 MB)
2. **File Size Check**: Bot checks size before processing
   - Files >20 MB: Immediate rejection with compression suggestions
   - Files >10 MB: Warning about longer processing time
3. **Bot Processing Flow**:
   
   **Step 1: Extraction & Segmentation** (30 seconds - 2 minutes)
   - Extracts text from all PDF pages
   - Segments into individual articles
   - Shows: "📊 Found X potential articles in the newspaper"
   
   **Step 2: Strict Initial Filtering** (5-10 seconds)
   - Applies keyword-based filtering
   - Progress shows: "🔍 Strict filtering applied: Total: X | ❌ Filtered: Y | ✅ Passed: Z"
   - Removes obviously irrelevant content
   
   **Step 3: AI-Powered Analysis** (2-10 minutes)
   - Parallel analysis of potentially relevant articles
   - Real-time progress: "📊 Progress: 45%\n✅ Relevant: 8 | ❌ Failed: 2\n📰 Total found: 50 | 🔍 Analyzing: 25"
   - Only highly relevant articles pass strict criteria
   
   **Step 4: Summary & PDF Generation** (30 seconds - 1 minute)
   - Shows final summary:
     ```
     📊 Strict UPSC Relevance Analysis Summary:
     📰 Total articles found: 50
     🔍 Analyzed for relevance: 25
     ✅ Highly relevant (kept): 12
     ❌ Rejected (not important enough): 13
     ```
   - Generates cleaned PDF with only highly relevant articles
   - Sends analyzed PDF back to user

## 📁 Project Structure

```
NewsAgent/
│
├── main.py                  # Main bot application & handlers
├── news_aggregator.py       # News fetching, aggregation, and analysis
├── newspaper_analyzer.py    # PDF analysis and filtering
├── pdf_generator.py         # PDF generation with section organization
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md               # This file
```

## 🏗️ Architecture & Key Components

### 1. News Aggregator (`news_aggregator.py`)

**Core Functionality:**
- `fetch_upsc_news()`: Main function that fetches from all sources
- `_fetch_from_*()`: Individual source fetchers (PIB, The Hindu, etc.)
- `_remove_duplicates()`: Title-based duplicate detection
- `_filter_upsc_relevant()`: Keyword-based relevance filtering
- `_prepare_news_for_analysis()`: Normalizes and ensures minimum article count
- `analyze_news()`: Parallel analysis orchestration
- `_analyze_single_article()`: Individual article analysis with retry logic
- `format_source_summary()`: Creates formatted summary with links

**Features:**
- Async/await for non-blocking operations
- Semaphore-based rate limiting (10 concurrent requests)
- Exponential backoff retry for 429 errors
- Progress callbacks for real-time updates

### 2. PDF Generator (`pdf_generator.py`)

**Section Organization:**
- All topics listed first
- Grouped sections for each analysis type
- Professional styling with colors and fonts
- HTML sanitization for clean PDF output

**Key Methods:**
- `generate_news_pdf()`: Main PDF generation
- `_clean_html_for_reportlab()`: Sanitizes HTML for PDF compatibility
- `_extract_section()`, `_extract_bullet_points()`, `_extract_questions()`: Fallback parsers

### 3. Newspaper Analyzer (`newspaper_analyzer.py`)

**Core Functionality:**
- `analyze_newspaper()`: Main analysis orchestration with progress tracking
- `_extract_text_from_pdf()`: Extracts text from PDF with page tracking
- `_segment_articles()`: Advanced article segmentation with pattern recognition
- `_quick_relevance_filter()`: Strict keyword-based initial filtering
- `_analyze_articles_parallel()`: Parallel analysis with real-time progress
- `_analyze_single_article_parallel()`: Individual article analysis with retry logic
- `_parse_analysis_response()`: Strict conservative parsing (defaults to NOT relevant)

**Strict Filtering System:**
- **Two-Tier Topic Classification**:
  - **Critical Topics** (40+ keywords): Government policies, schemes, parliament, courts, budget, RBI, international relations, environment, science, health, education, agriculture, infrastructure, defence, social welfare, governance, constitutional matters
  - **Secondary Topics**: Economy, GDP, trade, social development (need combination with critical topics)
- **Initial Filter Criteria**: 
  - Must have ≥2 critical topics OR ≥1 critical + ≥2 secondary topics
  - Minimum 100 words per article
  - Excludes 20+ irrelevant keyword categories
- **AI Relevance Check**: 
  - Strict LLM prompt with 14 specific relevance criteria
  - Conservative parsing (ambiguous = NOT relevant)
  - Only highly important articles pass

**Features:**
- Parallel processing (up to 10 concurrent API calls)
- Rate limiting with exponential backoff retry
- Progress callbacks with detailed statistics
- Comprehensive error handling

### 4. Main Bot (`main.py`)

**Handlers:**
- `/start`: Welcome message
- `news` command: Daily news analysis
- PDF upload: Newspaper analysis
- Progress tracking and error handling

## ⚙️ Configuration & Customization

### Adjusting Article Limits
Edit `news_aggregator.py`:
```python
# In _prepare_news_for_analysis()
news_data = news_data[:60]  # Change max articles
if len(news_data) < 50:     # Change minimum threshold
```

### Modifying News Sources
Add new sources in `news_aggregator.py`:
```python
async def _fetch_from_new_source(self) -> List[Dict]:
    # Implement your source fetcher
    pass

# Add to fetch_upsc_news()
news_sources.append(self._fetch_from_new_source())
```

### Changing UPSC Keywords (News Aggregator)
Edit `upsc_relevant_topics` list in `NewsAggregator.__init__()`:
```python
self.upsc_relevant_topics = [
    "government policy", "economy", 
    # Add your keywords here
]
```

### Customizing Newspaper Filtering (Strict Relevance)
Edit `newspaper_analyzer.py` to adjust filtering strictness:

**Modify Critical Topics:**
```python
self.upsc_critical_topics = [
    "government policy", "government scheme",
    # Add/remove critical UPSC topics
]
```

**Modify Secondary Topics:**
```python
self.upsc_secondary_topics = [
    "economy", "economic", "gdp",
    # Add/remove secondary topics
]
```

**Adjust Filtering Criteria:**
```python
# In _quick_relevance_filter()
# Current: Need ≥2 critical OR ≥1 critical + ≥2 secondary
if critical_matches >= 2 or (critical_matches >= 1 and secondary_matches >= 2):
    # Make stricter: Change to >= 3 or >= 2 + >= 3
    # Make looser: Change to >= 1 or >= 1 + >= 1
```

**Modify Irrelevant Keywords:**
```python
self.irrelevant_keywords = [
    'advertisement', 'sports',
    # Add more irrelevant categories
]
```

### Adjusting Concurrency
Edit `NewsAggregator.__init__()`:
```python
self.semaphore = asyncio.Semaphore(10)  # Change max concurrent requests
```

### Customizing PDF Style
Edit `pdf_generator.py` in `_setup_custom_styles()`:
- Font sizes
- Colors
- Spacing
- Layout

## 🔍 Troubleshooting

### Bot Not Responding
- ✅ Check if bot is running: `python main.py`
- ✅ Verify `TELEGRAM_BOT_TOKEN` in `.env`
- ✅ Check internet connection
- ✅ Look for error messages in console

### News Analysis Fails
- ✅ Verify `NVIDIA_API_KEY` and `NVIDIA_MODEL` in `.env`
- ✅ Check API credits/quota
- ✅ Review console for specific error messages
- ✅ Ensure model name is correct

### 429 Rate Limit Errors
- ✅ Bot automatically retries with exponential backoff
- ✅ Reduce semaphore limit if issues persist (change `Semaphore(10)` to lower value)
- ✅ Check your API rate limits

### PDF Generation Errors
- ✅ Ensure write permissions in directory
- ✅ Verify all dependencies installed: `pip install -r requirements.txt --upgrade`
- ✅ Check uploaded PDF is valid and not corrupted
- ✅ Review error logs for HTML parsing issues

### Progress Mismatch
- ✅ Counts are now synchronized (fixed in latest version)
- ✅ Initial message shows accurate total
- ✅ Progress updates in real-time

### Newspaper Analysis - Too Many/Few Articles
- ✅ **Too many articles included**: 
  - System uses strict filtering - adjust critical/secondary topic lists
  - Modify `_quick_relevance_filter()` criteria to be stricter
  - Check LLM prompt in `_analyze_single_article_parallel()` for stricter criteria
- ✅ **Too few articles included**:
  - Add more keywords to `upsc_critical_topics` list
  - Relax filtering criteria in `_quick_relevance_filter()`
  - Modify minimum word count requirement (currently 100 words)

### File Size Issues (Newspaper PDFs)
- ✅ **"File is too big" error**: 
  - Telegram download limit is 20 MB
  - Compress PDF using online tools (e.g., SmallPDF, ILovePDF)
  - Split PDF into smaller files (10-15 pages each)
  - Use PDF compression services
- ✅ **Large files take long**: 
  - Expected for files >10 MB (5-15 minutes)
  - Progress tracking shows real-time status
  - Be patient - parallel processing speeds it up

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

## 📊 Performance & Limits

### Daily News Analysis
- **Analysis Speed**: ~2-5 minutes for 50-60 articles (parallel processing)
- **Concurrency**: Up to 10 simultaneous API calls
- **Article Limit**: Maximum 60 articles per analysis
- **Minimum Guarantee**: At least 50 articles analyzed
- **Rate Limiting**: Automatic with 3 retry attempts per article
- **Progress Updates**: Real-time via Telegram messages

### Newspaper PDF Analysis
- **File Size Limit**: 20 MB (Telegram download limit)
- **Processing Time**: 
  - Small PDFs (<5 MB): 2-5 minutes
  - Medium PDFs (5-10 MB): 5-10 minutes
  - Large PDFs (10-20 MB): 10-15 minutes
- **Extraction Speed**: ~10 pages/second
- **Analysis Speed**: Parallel processing of all articles simultaneously
- **Filtering**: Two-phase strict filtering (keyword + AI analysis)
- **Concurrency**: Up to 10 simultaneous API calls
- **Relevance Rate**: Typically 15-30% of articles pass strict filtering (ensures quality)

## 🔐 Security & Best Practices

- **API Keys**: Never commit `.env` file to version control
- **Rate Limiting**: Built-in to prevent API abuse
- **Error Handling**: Comprehensive try-catch blocks
- **Cleanup**: Temporary files automatically deleted
- **Validation**: Input validation for all user inputs

## 📝 Important Notes

### API Costs
- NVIDIA API usage may have associated costs
- Monitor usage through your NVIDIA dashboard
- Consider caching frequently accessed articles
- Newspaper analysis processes multiple articles - costs scale with PDF size

### Accuracy Disclaimer
- AI-generated analysis is for educational purposes
- Always verify facts from official sources
- Use as a study aid, not definitive answers
- Cross-reference with official UPSC resources
- Strict filtering may sometimes reject borderline-relevant articles for quality assurance

### Rate Limits
- Respect API provider rate limits
- Bot handles temporary limits automatically with exponential backoff
- For sustained limits, adjust semaphore value (default: 10 concurrent requests)
- Rate limiting is built-in for both news and newspaper analysis

### Newspaper Analysis - Quality vs Quantity
- **Strict Filtering Philosophy**: Quality over quantity
- Only highly relevant articles are included (typically 15-30% of total)
- Articles must meet strict UPSC relevance criteria
- If too many articles are rejected, you may need to adjust filtering criteria (see Configuration section)
- This ensures you only study truly important current affairs

## 🚧 Future Enhancements

Potential features to add:
- [ ] Scheduled daily news digest
- [ ] Topic-wise categorization
- [ ] Revision flashcards generation
- [ ] Previous year question mapping
- [ ] Multi-language support
- [ ] Voice note summaries
- [ ] Quiz mode for self-assessment
- [ ] Bookmark articles for later review
- [ ] Export to different formats (DOCX, EPUB)
- [ ] Integration with note-taking apps
- [ ] Adjustable strictness level for newspaper filtering
- [ ] Topic-based filtering (e.g., only Polity, Economy, Environment)
- [ ] Date range selection for news analysis
- [ ] Custom keyword addition for relevance filtering

## 🆘 Support & Contributing

### Getting Help
1. Check the troubleshooting section above
2. Review error messages in console output
3. Verify all environment variables are correctly set
4. Ensure API keys are valid and have sufficient credits

### Reporting Issues
When reporting issues, please include:
- Error message from console
- Steps to reproduce
- Your `.env` configuration (without actual keys)
- Python version: `python --version`
- Package versions: `pip list`

## 📄 License

This project is provided as-is for educational purposes. Feel free to modify and enhance it for your needs.

## 🙏 Acknowledgments

- News sources for providing RSS feeds
- NVIDIA for LLM inference capabilities
- Telegram for bot platform
- Open source libraries: LangChain, ReportLab, BeautifulSoup, and others

---

**Happy Learning! All the best for your UPSC preparation! 🎯📚**

For questions or issues, check the troubleshooting section or review the code comments for detailed explanations.