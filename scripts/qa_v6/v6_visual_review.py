from pathlib import Path
import json,base64
from playwright.sync_api import sync_playwright
A=Path(__file__).resolve().parents[2];O=A/'docs/v6/review';O.mkdir(exist_ok=True)
files=sorted((A/'docs/v6/screens').glob('*.png'))+sorted((A/'docs/v6/unseen').glob('*.png'))+list((A/'docs/v6/final_paths').glob('*.png'))+list((A/'docs/v6/navigation').glob('*.png'))
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);pg=b.new_page(viewport={'width':1440,'height':1100})
 for i in range(0,len(files),20):
  batch=files[i:i+20];html='<style>body{margin:0;background:#e0e4e9;font:12px Arial;display:grid;grid-template-columns:repeat(4,1fr);gap:8px}figure{margin:0;background:white;overflow:hidden}img{width:100%;height:200px;object-fit:contain;object-position:top}figcaption{padding:5px;white-space:nowrap;font-size:10px}</style>'
  for f in batch:html+='<figure><img src="data:image/png;base64,'+base64.b64encode(f.read_bytes()).decode()+'"><figcaption>'+f.parent.name+'/'+f.name+'</figcaption></figure>'
  pg.set_content(html);pg.screenshot(path=str(O/f'contact_{i//20+1:02}.png'),full_page=True)
 b.close()
(O/'INDEX.json').write_text(json.dumps([str(f.relative_to(A)) for f in files],indent=2))
