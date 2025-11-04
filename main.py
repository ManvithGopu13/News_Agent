import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Import our custom modules
from news_aggregator import NewsAggregator
from newspaper_analyzer import NewspaperAnalyzer
from pdf_generator import PDFGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UPSCNewsBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")
        
        self.news_aggregator = NewsAggregator()
        self.newspaper_analyzer = NewspaperAnalyzer()
        self.pdf_generator = PDFGenerator()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        welcome_message = """
🎓 Welcome to UPSC News Agent! 📰

I can help you with:

1️⃣ **Daily News Analysis**
   - Send me the word "news"
   - I'll fetch, analyze, and summarize today's important news for UPSC
   - You'll get a detailed PDF with potential exam questions

2️⃣ **Newspaper Analysis**
   - Send me a PDF of any newspaper
   - I'll extract relevant UPSC content
   - Remove unnecessary articles
   - Provide detailed analysis with simplified explanations

Let's start your UPSC preparation journey! 🚀
"""
        await update.message.reply_text(welcome_message)

    async def handle_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the 'news' command to fetch and analyze daily news."""
        progress_message = None
        
        async def progress_callback(current: int, total: int, message: str):
            """Send progress updates to Telegram."""
            nonlocal progress_message
            progress_text = f"📊 Progress: {current}/{total}\n\n{message}"
            
            try:
                if progress_message is None:
                    progress_message = await update.message.reply_text(progress_text)
                else:
                    await progress_message.edit_text(progress_text)
            except Exception as e:
                # If message is too old to edit, send a new one
                if "message is not modified" not in str(e).lower():
                    logger.warning(f"Error updating progress message: {e}")
        
        await update.message.reply_text(
            "🔍 Starting comprehensive news analysis for UPSC...\n"
            "This may take a few minutes. Please wait..."
        )
        
        try:
            # Step 1: Aggregate news
            await update.message.reply_text("📊 Gathering news from multiple sources...")
            news_data, source_map = await self.news_aggregator.fetch_upsc_news()
            
            # Show detailed summary with source breakdown and links
            summary_message = self.news_aggregator.format_source_summary(source_map)
            # Send summary (parse_mode='HTML' for clickable links)
            await update.message.reply_text(
                summary_message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Prepare news data to get the actual count that will be analyzed
            # (this accounts for sample news additions if needed)
            prepared_news = self.news_aggregator._prepare_news_for_analysis(news_data)
            actual_count = len(prepared_news)
            
            # Show analysis start message with accurate count
            await update.message.reply_text(
                f"🤖 Starting analysis of {actual_count} articles..."
            )
            
            # Step 2: Analyze and generate content with progress updates
            analyzed_content = await self.news_aggregator.analyze_news(
                news_data, 
                progress_callback=progress_callback
            )
            
            # Step 3: Generate PDF
            if progress_message:
                await progress_message.edit_text("📄 Creating PDF report...")
            await update.message.reply_text("📄 Creating PDF report...")
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            pdf_path = f"UPSC_News_Analysis_{date_str}.pdf"
            
            self.pdf_generator.generate_news_pdf(analyzed_content, pdf_path)
            
            # Step 4: Send PDF to user
            if progress_message:
                await progress_message.edit_text("✅ Analysis complete! Sending your PDF...")
            await update.message.reply_text("✅ Analysis complete! Sending your PDF...")
            
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=pdf_path,
                    caption=f"📚 UPSC News Analysis - {date_str}\n\n"
                            f"Topics covered: {len(analyzed_content['articles'])}\n"
                            f"Stay informed, stay prepared! 💪"
                )
            
            # Cleanup
            os.remove(pdf_path)
            if progress_message:
                try:
                    await progress_message.delete()
                except:
                    pass
            logger.info(f"News analysis completed for user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in news analysis: {str(e)}")
            await update.message.reply_text(
                f"❌ Sorry, there was an error processing the news.\nError: {str(e)}"
            )
            if progress_message:
                try:
                    await progress_message.delete()
                except:
                    pass

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF newspaper uploads."""
        document = update.message.document
        
        if not document.file_name.endswith('.pdf'):
            await update.message.reply_text(
                "⚠️ Please send a PDF file only."
            )
            return
        
        await update.message.reply_text(
            "📄 Newspaper PDF received!\n"
            "🔍 Analyzing and extracting UPSC-relevant content...\n"
            "This may take several minutes..."
        )
        
        try:
            # Download the PDF
            file = await context.bot.get_file(document.file_id)
            input_pdf_path = f"temp_input_{document.file_id}.pdf"
            await file.download_to_drive(input_pdf_path)
            
            await update.message.reply_text("📖 Reading newspaper content...")
            
            # Analyze the newspaper
            analyzed_content = await self.newspaper_analyzer.analyze_newspaper(input_pdf_path)
            
            await update.message.reply_text("✍️ Generating analyzed PDF...")
            
            # Generate new PDF
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_pdf_path = f"UPSC_Newspaper_Analysis_{date_str}.pdf"
            
            self.pdf_generator.generate_newspaper_analysis_pdf(
                analyzed_content, 
                output_pdf_path
            )
            
            # Send the analyzed PDF
            await update.message.reply_text("✅ Analysis complete! Sending your PDF...")
            with open(output_pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=output_pdf_path,
                    caption=f"📰 Analyzed Newspaper - {date_str}\n\n"
                            f"Relevant articles: {len(analyzed_content['articles'])}\n"
                            f"Filtered and simplified for UPSC preparation! 📚"
                )
            
            # Cleanup
            os.remove(input_pdf_path)
            os.remove(output_pdf_path)
            logger.info(f"Newspaper analysis completed for user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in newspaper analysis: {str(e)}")
            await update.message.reply_text(
                "❌ Sorry, there was an error analyzing the newspaper. Please ensure it's a valid PDF."
            )
            if os.path.exists(input_pdf_path):
                os.remove(input_pdf_path)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        text = update.message.text.lower().strip()
        
        if text == "news":
            await self.handle_news_command(update, context)
        else:
            await update.message.reply_text(
                "I didn't understand that. Try:\n"
                "• Send 'news' for daily UPSC news analysis\n"
                "• Send a newspaper PDF for analysis"
            )

    def run(self):
        """Start the bot."""
        application = Application.builder().token(self.token).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        application.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        
        # Start the bot
        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = UPSCNewsBot()
    bot.run()