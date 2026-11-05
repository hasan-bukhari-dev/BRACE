"""Build the editable Markdown manual with real, locally captured screenshots.

Authoring dependencies: reportlab 4.4.3. Final builds reject missing images.
"""
from pathlib import Path
import argparse
import re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT/'VERSION').read_text().strip()


class WorkspaceIllustration(Flowable):
    """Explicit manual overlays on an unchanged authentic source screenshot."""
    def __init__(self, path, width, height):
        super().__init__()
        self.path, self.width, self.height = path, width, height

    def draw(self):
        c = self.canv
        image_width, image_height = ImageReader(str(self.path)).getSize()
        sx, sy = self.width/image_width, self.height/image_height
        c.drawImage(str(self.path), 0, 0, self.width, self.height)
        c.linkURL(f'https://github.com/hasan-bukhari-dev/BRACE/blob/v{VERSION}/docs/manual/screenshots/'+self.path.name,
                  (0,0,self.width,self.height), relative=1, thickness=0)
        if self.path.name != '01-workspace.jpg':
            return
        c.setStrokeColor(HexColor('#ffbd59'))
        c.setLineWidth(1.4)
        for number, (x,y,w,h), (label_x,label_y) in [
            (1,(342,14,545,66),(950,45)),
            (2,(57,335,148,56),(255,365))]:
            left, bottom = x*sx, (image_height-y-h)*sy
            c.rect(left,bottom,w*sx,h*sy)
            lx,ly = label_x*sx,(image_height-label_y)*sy
            end_x,end_y = left+w*sx,bottom+h*sy/2
            c.line(lx-8,ly,end_x+2,end_y)
            c.line(end_x+2,end_y,end_x+7,end_y+3)
            c.line(end_x+2,end_y,end_x+7,end_y-3)
            c.setFillColor(HexColor('#ffbd59'));c.circle(lx,ly,7,fill=1,stroke=0)
            c.setFillColor(HexColor('#132331'));c.setFont('Helvetica-Bold',9)
            c.drawCentredString(lx,ly-3,str(number))


def build(source, target, draft=False, quick=False):
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].spaceAfter = 10
    if quick:
        styles['Normal'].fontSize = 12
        styles['Normal'].leading = 17
    for name in ['Title', 'Heading1', 'Heading2']:
        styles[name].textColor = HexColor('#1c3948')
    text = source.read_text(encoding='utf-8')
    sections = re.split(r'^## ', text, flags=re.M)
    story = [Paragraph("BRACE", styles['Title']),
             Paragraph('Quick start' if quick else "Illustrated Researcher's Guide", styles['Heading1']),
             Paragraph('From Research Data to Verifiable Evidence', styles['Normal'])]
    if not quick:
        story += [Paragraph('Contents', styles['Heading2'])]
        for i, section in enumerate(sections[1:]):
            title = section.splitlines()[0]
            story.append(Paragraph(f'<link href="#chapter-{i}">{escape(title)}</link>', styles['Normal']))
        story.append(PageBreak())
    figure_number = 0
    for i, section in enumerate(sections[1:]):
        title, _, body = section.partition('\n')
        if quick and i == 2:
            story.append(PageBreak())
        if i and not quick:
            story.append(PageBreak())
        story.append(Paragraph(f'<a name="chapter-{i}"/>{escape(title)}', styles['Heading2']))
        for block in body.strip().split('\n\n'):
            match = re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)', block.strip())
            if match:
                path = source.parent / match[2]
                if not path.is_file():
                    if not draft:
                        raise FileNotFoundError(path)
                    story.append(Paragraph('DRAFT: verified screenshot pending.', styles['Normal']))
                    continue
                width, height = ImageReader(str(path)).getSize()
                scale = min(475 / width, 335 / height)
                figure_number += 1
                story.append(WorkspaceIllustration(path,width*scale,height*scale))
                story.append(Paragraph(f'Figure {figure_number}. {escape(match[1])}. Controls and measurements are actual application output.', styles['Caption'] if 'Caption' in styles else styles['Normal']))
                if path.name == '01-workspace.jpg':
                    story.append(Paragraph('Manual callouts: <b>1</b> choose a BRACE destination; <b>2</b> begin with your own data. Arrows and outlines are guide annotations.', styles['Normal']))
            else:
                value = escape(block).replace('\n', '<br/>')
                value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
                value = re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#176477">\1</link>', value)
                value = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'\1', value)
                story.append(Paragraph(value, styles['Normal']))
    target.parent.mkdir(exist_ok=True, parents=True)
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#465766'))
        canvas.drawString(48, 26, 'BRACE | Research software | ' + ('DRAFT' if draft else VERSION))
        canvas.drawRightString(A4[0]-48, 26, str(doc.page))
    SimpleDocTemplate(str(target), pagesize=A4, rightMargin=48, leftMargin=48,
                      topMargin=40, bottomMargin=45, title='BRACE Illustrated Researcher Guide',
                      author='BRACE').build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft', action='store_true')
    args = parser.parse_args()
    out = ROOT/'work' if args.draft else ROOT/'docs'
    build(ROOT/'docs/manual/USER_MANUAL.md', out/'USER_MANUAL.pdf', args.draft)
    build(ROOT/'docs/QUICK_START.md', out/'QUICK_START.pdf', args.draft, quick=True)
