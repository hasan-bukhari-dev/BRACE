"""Display-only identification by exact hashes; never changes scientific results."""
import hashlib
from pathlib import Path

def identify_public(inputs):
 from brace_app.study_api import public_paths
 try:
  root=public_paths()/'prepared'
  for role in ('source','target'):
   for kind,suffix in (('expression','.tsv'),('metadata','.tsv'),('manifest','.json')):
    key=role+'_'+kind
    if inputs.get(key,{}).get('sha256')!=hashlib.sha256((root/(key+suffix)).read_bytes()).hexdigest():return False
  return True
 except Exception:return False


def public_preparation(inputs):
 if not identify_public(inputs):return {}
 import json
 from brace_app.study_api import public_paths
 root=public_paths()
 return {'input_origin':'verified_public','public_preparation':json.loads((root/'prepared/summary.json').read_text()),'public_data_document':(root/'README.md').read_text(encoding='utf-8')}
