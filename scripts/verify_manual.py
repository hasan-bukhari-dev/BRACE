from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parents[1];out=r/'work/manual-review';out.mkdir(exist_ok=True)
receipts={}
for filename in ['USER_MANUAL.pdf','QUICK_START.pdf']:
 path=r/'docs'/filename;doc=fitz.open(path);pages=[]
 for i,page in enumerate(doc):
  text=page.get_text();assert len(text.strip())>35,(filename,i)
  assert 'DRAFT' not in text,(filename,i)
  for block in page.get_text('blocks'):
   assert 0<=block[0]<block[2]<=page.rect.width+1 and 0<=block[1]<block[3]<=page.rect.height+1,(filename,i,block[:4])
  links=page.get_links()
  for link in links:
   if link['kind']==fitz.LINK_GOTO:assert 0<=link['page']<len(doc)
  png=out/(filename[:-4]+f'-{i+1:02}.png');page.get_pixmap(matrix=fitz.Matrix(1,1)).save(png)
  pages.append({'page':i+1,'text_characters':len(text),'links':len(links),'render_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
 receipts[filename]={'pages':len(doc),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'page_checks':pages}
 images=[Image.open(out/(filename[:-4]+f'-{i+1:02}.png')).convert('RGB') for i in range(len(doc))]
 for start in range(0,len(images),6):
  sheet=Image.new('RGB',(900,920),'#b9c3ce')
  for offset,im in enumerate(images[start:start+6]):
   im.thumbnail((290,420));x=(offset%3)*300+5;y=(offset//3)*460+20;sheet.paste(im,(x,y));ImageDraw.Draw(sheet).text((x,y-15),f'{filename} page {start+offset+1}',fill='black')
  sheet.save(out/(filename[:-4]+f'-sheet-{start//6+1}.jpg'))
receipts['screenshots']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'docs/manual/screenshots').glob('*.jpg')}
receipts['status']='LAYOUT_CHECKS_PASS_VISUAL_REVIEW_PENDING'
(out/'checks.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print({k:v['pages'] for k,v in receipts.items() if isinstance(v,dict) and 'pages'in v})
