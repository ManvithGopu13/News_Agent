from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from datetime import datetime
from typing import Dict, List
import re

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#3f51b5'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=14
        ))
        
        # Question style
        self.styles.add(ParagraphStyle(
            name='Question',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#c62828'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))

    def generate_news_pdf(self, content: Dict, output_path: str):
        """Generate PDF for daily news analysis - organized by sections."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Title
        title = Paragraph(
            f"UPSC Daily News Analysis<br/>{content['date']}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary box
        summary_data = [
            ['Total Articles Analyzed', str(content['total_articles'])],
            ['Generated On', datetime.now().strftime('%Y-%m-%d %H:%M')]
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0d47a1')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1976d2'))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.4*inch))
        
        # SECTION 1: ALL TOPICS/TITLES
        story.append(PageBreak())
        story.append(Paragraph(
            "📋 ALL TOPICS COVERED",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            story.append(Paragraph(
                f"{idx}. {article['title']}",
                self.styles['SubsectionHeading']
            ))
            story.append(Paragraph(
                f"<i>Source: {article['source']} | Date: {article['date']}</i>",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 0.1*inch))
        
        # SECTION 2: ALL UPSC RELEVANCE SECTIONS
        story.append(PageBreak())
        story.append(Paragraph(
            "🎯 UPSC RELEVANCE - ALL TOPICS",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            parsed = article.get('parsed', {})
            relevance = parsed.get('upsc_relevance', '')
            if not relevance and article.get('analysis'):
                # Fallback: extract from full analysis
                relevance = self._extract_section(article['analysis'], 'UPSC Relevance')
            
            if relevance:
                story.append(Paragraph(
                    f"<b>{idx}. {article['title']}</b>",
                    self.styles['SubsectionHeading']
                ))
                # Clean and properly format HTML for reportlab
                cleaned_relevance = self._clean_html_for_reportlab(relevance)
                story.append(Paragraph(
                    cleaned_relevance,
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 0.15*inch))
        
        # SECTION 3: ALL KEY POINTS
        story.append(PageBreak())
        story.append(Paragraph(
            "🔑 KEY POINTS - ALL TOPICS",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            parsed = article.get('parsed', {})
            key_points = parsed.get('key_points', [])
            if not key_points and article.get('analysis'):
                key_points = self._extract_bullet_points(article['analysis'], 'Key Points')
            
            if key_points:
                story.append(Paragraph(
                    f"<b>{idx}. {article['title']}</b>",
                    self.styles['SubsectionHeading']
                ))
                for point in key_points:
                    story.append(Paragraph(
                        f"• {point}",
                        self.styles['CustomBody']
                    ))
                story.append(Spacer(1, 0.15*inch))
        
        # SECTION 4: ALL CONCEPTS
        story.append(PageBreak())
        story.append(Paragraph(
            "📚 CONCEPTS TO UNDERSTAND - ALL TOPICS",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            parsed = article.get('parsed', {})
            concepts = parsed.get('concepts', [])
            if not concepts and article.get('analysis'):
                concepts = self._extract_bullet_points(article['analysis'], 'Concepts to Understand')
            
            if concepts:
                story.append(Paragraph(
                    f"<b>{idx}. {article['title']}</b>",
                    self.styles['SubsectionHeading']
                ))
                for concept in concepts:
                    story.append(Paragraph(
                        f"• {concept}",
                        self.styles['CustomBody']
                    ))
                story.append(Spacer(1, 0.15*inch))
        
        # SECTION 5: ALL PRELIMS QUESTIONS
        story.append(PageBreak())
        story.append(Paragraph(
            "📝 PRELIMS PERSPECTIVE - ALL QUESTIONS",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            parsed = article.get('parsed', {})
            prelims = parsed.get('prelims_questions', [])
            if not prelims and article.get('analysis'):
                prelims = self._extract_questions(article['analysis'], 'Prelims')
            
            if prelims:
                story.append(Paragraph(
                    f"<b>Topic {idx}: {article['title']}</b>",
                    self.styles['SubsectionHeading']
                ))
                for q in prelims:
                    # Clean and properly format HTML for reportlab
                    cleaned_q = self._clean_html_for_reportlab(q)
                    story.append(Paragraph(
                        cleaned_q,
                        self.styles['Question']
                    ))
                story.append(Spacer(1, 0.15*inch))
        
        # SECTION 6: ALL MAINS QUESTIONS
        story.append(PageBreak())
        story.append(Paragraph(
            "✍️ MAINS PERSPECTIVE - ALL QUESTIONS",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            parsed = article.get('parsed', {})
            mains = parsed.get('mains_questions', [])
            if not mains and article.get('analysis'):
                mains = self._extract_questions(article['analysis'], 'Mains')
            
            if mains:
                story.append(Paragraph(
                    f"<b>Topic {idx}: {article['title']}</b>",
                    self.styles['SubsectionHeading']
                ))
                for q in mains:
                    # Clean and properly format HTML for reportlab
                    cleaned_q = self._clean_html_for_reportlab(q)
                    story.append(Paragraph(
                        cleaned_q,
                        self.styles['Question']
                    ))
                story.append(Spacer(1, 0.15*inch))
        
        # SECTION 7: ALL STATIC PORTIONS
        story.append(PageBreak())
        story.append(Paragraph(
            "📜 STATIC PORTION - ALL TOPICS",
            self.styles['SectionHeading']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, article in enumerate(content['articles'], 1):
            parsed = article.get('parsed', {})
            static = parsed.get('static_portion', '')
            if not static and article.get('analysis'):
                static = self._extract_section(article['analysis'], 'Static Portion')
            
            if static:
                story.append(Paragraph(
                    f"<b>{idx}. {article['title']}</b>",
                    self.styles['SubsectionHeading']
                ))
                # Clean and properly format HTML for reportlab
                cleaned_static = self._clean_html_for_reportlab(static)
                story.append(Paragraph(
                    cleaned_static,
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 0.15*inch))
        
        # Footer
        story.append(PageBreak())
        story.append(Paragraph(
            "<b>Disclaimer:</b> This analysis is generated for educational purposes. "
            "Please verify facts from official sources.",
            self.styles['CustomBody']
        ))
        
        # Build PDF
        doc.build(story)
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from analysis text."""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            if in_section:
                if line.strip() and (line.strip().startswith('**') or 
                                     any(header in line.lower() for header in 
                                         ['upsc relevance', 'key points', 'concepts', 'prelims', 'mains', 'static'])):
                    break
                if line.strip():
                    section_content.append(line.strip())
        
        return ' '.join(section_content)
    
    def _extract_bullet_points(self, text: str, section_name: str) -> List[str]:
        """Extract bullet points from a section."""
        lines = text.split('\n')
        in_section = False
        points = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            if in_section:
                if line.strip() and (line.strip().startswith('**') or 
                                     any(header in line.lower() for header in 
                                         ['upsc relevance', 'key points', 'concepts', 'prelims', 'mains', 'static'])):
                    break
                stripped = line.strip()
                if stripped.startswith(('•', '-', '*')):
                    points.append(stripped.lstrip('•-* '))
                elif stripped and any(char.isupper() or char.isdigit() for char in stripped[:2]):
                    points.append(stripped)
        
        return points
    
    def _extract_questions(self, text: str, section_name: str) -> List[str]:
        """Extract questions from a section."""
        lines = text.split('\n')
        in_section = False
        questions = []
        current_q = None
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            if in_section:
                if line.strip() and (line.strip().startswith('**') or 
                                     any(header in line.lower() for header in 
                                         ['upsc relevance', 'key points', 'concepts', 'prelims', 'mains', 'static'])):
                    break
                stripped = line.strip()
                if stripped.startswith(('Q', 'q')) or (stripped and any(char.isdigit() for char in stripped[:3])):
                    if current_q:
                        questions.append(current_q)
                    current_q = stripped
                elif current_q and stripped:
                    current_q += ' ' + stripped
        
        if current_q:
            questions.append(current_q)
        
        return questions
    
    def _clean_html_for_reportlab(self, text: str) -> str:
        """Clean and properly format HTML text for reportlab Paragraph.
        
        Reportlab requires:
        - <br/> (self-closing) not <br> or <br></br>
        - Proper HTML entity escaping
        - No unclosed tags
        """
        if not text:
            return ""
        
        # Remove any <para> tags that might be in the text
        text = re.sub(r'</?para[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Replace newlines with <br/>
        text = text.replace('\n', '<br/>')
        text = text.replace('\r\n', '<br/>')
        text = text.replace('\r', '<br/>')
        
        # Fix common HTML issues - normalize <br> tags
        text = re.sub(r'<br\s*/?>', '<br/>', text, flags=re.IGNORECASE)
        text = re.sub(r'<br></br>', '<br/>', text, flags=re.IGNORECASE)
        text = re.sub(r'<BR>', '<br/>', text)
        text = re.sub(r'<BR/>', '<br/>', text)
        
        # Escape & but preserve existing entities
        # First, protect existing HTML entities
        entities_map = {
            '&amp;': '__AMP__',
            '&lt;': '__LT__',
            '&gt;': '__GT__',
            '&quot;': '__QUOT__',
            '&apos;': '__APOS__',
            '&nbsp;': '__NBSP__'
        }
        
        for entity, placeholder in entities_map.items():
            text = text.replace(entity, placeholder)
        
        # Escape remaining & symbols
        text = text.replace('&', '&amp;')
        
        # Restore entities
        for entity, placeholder in entities_map.items():
            text = text.replace(placeholder, entity)
        
        # Fix any remaining unclosed or malformed tags (except <br/>, <b>, <i>, <u>)
        # Escape any other HTML tags
        allowed_tags = ['br/', 'b', '/b', 'i', '/i', 'u', '/u', 'strong', '/strong', 'em', '/em']
        tag_pattern = r'<([^>]+)>'
        
        def escape_tag(match):
            tag_content = match.group(1)
            # Check if it's an allowed tag
            for allowed in allowed_tags:
                if tag_content.strip().lower().startswith(allowed.lower()):
                    return match.group(0)  # Keep allowed tags
            # Escape disallowed tags
            return f'&lt;{tag_content}&gt;'
        
        text = re.sub(tag_pattern, escape_tag, text)
        
        return text

    def generate_newspaper_analysis_pdf(self, content: Dict, output_path: str):
        """Generate PDF for newspaper analysis."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Title
        title = Paragraph(
            f"UPSC Newspaper Analysis<br/>{datetime.now().strftime('%Y-%m-%d')}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        summary_text = f"<b>Relevant Articles Extracted:</b> {content['total_articles']}"
        story.append(Paragraph(summary_text, self.styles['CustomBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Process each article
        for article in content['articles']:
            # Article heading
            story.append(Paragraph(
                f"Article {article['article_number']}",
                self.styles['SectionHeading']
            ))
            story.append(Spacer(1, 0.1*inch))
            
            # Summary
            if article.get('summary'):
                story.append(Paragraph(
                    "<b>Summary:</b>",
                    self.styles['SubsectionHeading']
                ))
                story.append(Paragraph(
                    article['summary'],
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 0.1*inch))
            
            # Simplified explanation
            if article.get('simplified_explanation'):
                story.append(Paragraph(
                    "<b>Simplified Explanation:</b>",
                    self.styles['SubsectionHeading']
                ))
                story.append(Paragraph(
                    article['simplified_explanation'],
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 0.1*inch))
            
            # Key concepts
            if article.get('key_concepts'):
                story.append(Paragraph(
                    "<b>Key Concepts:</b>",
                    self.styles['SubsectionHeading']
                ))
                for concept in article['key_concepts'][:5]:
                    story.append(Paragraph(
                        f"• {concept}",
                        self.styles['CustomBody']
                    ))
                story.append(Spacer(1, 0.1*inch))
            
            # UPSC Relevance
            if article.get('upsc_relevance'):
                story.append(Paragraph(
                    "<b>UPSC Relevance:</b>",
                    self.styles['SubsectionHeading']
                ))
                story.append(Paragraph(
                    article['upsc_relevance'],
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 0.1*inch))
            
            # Prelims questions
            if article.get('prelims_questions'):
                story.append(Paragraph(
                    "<b>Potential Prelims Questions:</b>",
                    self.styles['SubsectionHeading']
                ))
                for q in article['prelims_questions'][:3]:
                    story.append(Paragraph(q, self.styles['Question']))
                story.append(Spacer(1, 0.1*inch))
            
            # Mains questions
            if article.get('mains_questions'):
                story.append(Paragraph(
                    "<b>Potential Mains Questions:</b>",
                    self.styles['SubsectionHeading']
                ))
                for q in article['mains_questions'][:2]:
                    story.append(Paragraph(q, self.styles['Question']))
                story.append(Spacer(1, 0.1*inch))
            
            # Related topics
            if article.get('related_topics'):
                story.append(Paragraph(
                    "<b>Related Topics to Study:</b>",
                    self.styles['SubsectionHeading']
                ))
                related_text = ', '.join(article['related_topics'][:5])
                story.append(Paragraph(related_text, self.styles['CustomBody']))
            
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph('_' * 100, self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Page break after each article
            story.append(PageBreak())
        
        # Build PDF
        doc.build(story)