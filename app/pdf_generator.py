"""PDF generation using ReportLab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
from pathlib import Path
import tempfile


class PDFGenerator:
    """Generate PDF reports using ReportLab."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#003366'),
            spaceAfter=12,
            alignment=1  # center
        ))
        
        # Heading2 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#003366'),
            spaceAfter=8,
            spaceBefore=8
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            alignment=4  # justify
        ))
    
    def generate_pdf(self, title: str, content: str, source_docs: list = None, output_path: str = None) -> str:
        """
        Generate PDF from text content.
        
        Args:
            title: Report title
            content: Report body text
            source_docs: List of source documents info
            output_path: Where to save PDF (default: temp file)
        
        Returns:
            Path to generated PDF
        """
        if not output_path:
            # Create temp file
            fd, output_path = tempfile.mkstemp(suffix=".pdf", prefix="report_")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Build story (content elements)
        story = []
        
        # Header
        story.append(Paragraph("Deutsche Bahn AG", self.styles['Normal']))
        story.append(Paragraph("DB Systemtechnik", self.styles['Normal']))
        story.append(Spacer(1, 0.3*cm))
        
        # Title
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*cm))
        
        # Metadata
        meta_text = f"Generiert: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        story.append(Paragraph(meta_text, self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        # Main content
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Check if it's a heading (starts with uppercase + colon)
                if ':' in para and len(para.split(':')[0]) < 50:
                    heading = para.split(':')[0]
                    rest = ':'.join(para.split(':')[1:])
                    
                    story.append(Paragraph(heading, self.styles['CustomHeading']))
                    if rest.strip():
                        story.append(Paragraph(rest, self.styles['CustomBody']))
                else:
                    story.append(Paragraph(para, self.styles['CustomBody']))
                
                story.append(Spacer(1, 0.3*cm))
        
        # Page break before sources
        if source_docs:
            story.append(PageBreak())
            story.append(Paragraph("Quelldokumente", self.styles['CustomHeading']))
            story.append(Spacer(1, 0.3*cm))
            
            # Source table
            source_data = [['Report ID', 'Heading', 'Pages', 'Ähnlichkeit']]
            for doc in source_docs:
                source_data.append([
                    doc.get('report_id', ''),
                    doc.get('heading', '')[:30],
                    doc.get('page_range', ''),
                    f"{doc.get('similarity', 0):.1%}"
                ])
            
            source_table = Table(source_data)
            source_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            
            story.append(source_table)
        
        # Build PDF
        doc.build(story)
        
        return output_path


if __name__ == "__main__":
    # Test
    generator = PDFGenerator()
    
    test_content = """
    Einleitung
    Dies ist ein Test-Bericht, der via ReportLab generiert wurde.
    
    Beschreibung
    Der Fahrzeugrahmen zeigt Belastungen unter Windbedingungen.
    
    Ergebnisse
    Die Strukturmechanik-Simulation zeigt kritische Punkte.
    """
    
    output = generator.generate_pdf(
        title="Test Report: Fahrzeugrahmen Analyse",
        content=test_content,
        source_docs=[
            {'report_id': '001', 'heading': 'Wind', 'page_range': '5-7', 'similarity': 0.65}
        ]
    )
    
    print(f"✅ PDF generated: {output}")
