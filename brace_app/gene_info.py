"""Optional public identifier annotation, separate from statistical evidence."""
import csv
import hashlib
import json
import re
from pathlib import Path
from functools import lru_cache
from urllib.parse import urlencode

from brace_app.persistence import atomic_json

NOTE = 'Reference biology, not a causal explanation of this result. Probe mappings may be historical; inspect the source.'


@lru_cache(maxsize=4)
def platform_rows(path, sha):
    with Path(path).open(encoding='utf-8',newline='') as stream:
        return {row['probe_id']:row for row in csv.DictReader(stream,delimiter='\t')}


def identity(feature, namespace, platform=None):
    result = {'feature_id': feature, 'feature_namespace': namespace, 'status': 'unmapped'}
    if namespace == 'entrez_gene' and re.fullmatch(r'[1-9][0-9]{0,11}', feature):
        return {**result, 'status': 'resolved', 'entrez_id': feature}
    if namespace in ('gene_symbol', 'ensembl_gene'):
        return {**result, 'status': 'query_required'}
    if namespace != 'probe_id' or platform != 'GPL570':
        return {**result, 'reason': 'No reviewed mapping for this probe platform. Import a curated gene-ID mapping before interpreting gene function.'}
    from brace_app import server
    root = server.BASE / 'examples/public_er_pair/evidence'
    path = root / 'GPL570_mapping.tsv'
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != (root / 'GPL570_mapping.sha256').read_text().split()[0]:
        return {**result, 'reason': 'Pinned platform mapping failed its checksum.'}
    row = platform_rows(str(path),sha).get(feature)
    if not row:
        return result
    ids = [v.strip() for v in row['entrez_gene_id'].split('///') if v.strip().isdigit()]
    if len(ids) != 1:
        return {**result, 'status': 'ambiguous', 'candidate_entrez_ids': ids,
                'reason': 'This platform probe has no single gene assignment. No function was chosen.'}
    return {**result, 'status': 'resolved', 'entrez_id': ids[0], 'gene_symbol': row['gene_symbol'],
            'mapping_sha256': sha, 'mapping_source': 'Pinned GEO GPL570 annotation'}


def lookup(feature, namespace, platform=None, online=False):
    from brace_app import server, discovery
    mapped = identity(feature, namespace, platform)
    if mapped['status'] in ('unmapped', 'ambiguous'):
        return mapped
    key = hashlib.sha256(json.dumps([feature, namespace, platform]).encode()).hexdigest()
    cache = server.RUNS / '_annotations' / (key + '.json')
    if cache.is_file():
        try:
            envelope = json.loads(cache.read_text(encoding='utf-8'))
            if hashlib.sha256(json.dumps(envelope['record'], sort_keys=True).encode()).hexdigest() == envelope['sha256']:
                return envelope['record']
        except (OSError, ValueError, KeyError):
            pass
    pinned = json.loads(Path(__file__).with_name('gene_context.json').read_text(encoding='utf-8'))
    if mapped.get('entrez_id') in pinned:
        return {**mapped, 'biological_context': pinned[mapped['entrez_id']]}
    if not online:
        return mapped
    identifier = mapped.get('entrez_id')
    receipts = []
    if not identifier:
        valid = r'ENSG[0-9]+(?:\.[0-9]+)?' if namespace == 'ensembl_gene' else r'[A-Za-z][A-Za-z0-9_.-]{0,79}'
        if not re.fullmatch(valid, feature):
            return {**mapped, 'status': 'unmapped', 'reason': 'Identifier is not a supported exact human gene identifier.'}
        value = feature.split('.')[0] if namespace == 'ensembl_gene' else feature
        field = 'All Fields' if namespace == 'ensembl_gene' else 'Gene Name'
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?' + urlencode(
            {'db': 'gene', 'term': f'"{value}"[{field}] AND 9606[Taxonomy ID]', 'retmode': 'json', 'retmax': 3})
        raw = discovery.public_bytes(url)
        receipts.append({'url': url, 'sha256': discovery.sha(raw)})
        search = json.loads(raw)['esearchresult']
        if int(search['count']) != 1:
            return {**mapped, 'status': 'ambiguous', 'reason': 'NCBI did not return one exact human gene. No function was assigned.'}
        identifier = search['idlist'][0]
        if namespace == 'ensembl_gene':
            import xml.etree.ElementTree as ET
            xurl='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urlencode({'db':'gene','id':identifier,'retmode':'xml'})
            xml=discovery.public_bytes(xurl)
            try:
                tags=ET.fromstring(xml).findall('.//Dbtag')
            except ET.ParseError as exc:
                raise ValueError('NCBI returned malformed gene XML.') from exc
            matched=any(tag.findtext('Dbtag_db')=='Ensembl' and tag.findtext('.//Object-id_str')==value for tag in tags)
            if not matched:
                return {**mapped,'status':'unmapped','reason':'NCBI search did not supply an exact Ensembl cross-reference. Use a reviewed Entrez ID.'}
            receipts.append({'url':xurl,'sha256':discovery.sha(xml)})
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?' + urlencode({'db':'gene','id':identifier,'retmode':'json'})
    raw = discovery.public_bytes(url)
    record = json.loads(raw)['result'][identifier]
    if record.get('organism', {}).get('taxid') != 9606 or str(record.get('currentid') or '0') not in ('0', identifier):
        return {**mapped, 'status': 'unmapped', 'reason': 'Gene is not a current human record. Review the NCBI identifier.'}
    # Symbol queries must match the official symbol, not an alias expansion.
    symbol = record.get('nomenclaturesymbol') or record['name']
    if namespace == 'gene_symbol' and symbol.casefold() != feature.casefold():
        return {**mapped, 'status': 'ambiguous', 'reason': 'The identifier matched an alias, not the current symbol. Use a reviewed Entrez ID.'}
    context = {'current_symbol': symbol, 'name': record['description'],
        'function_excerpt': record.get('summary') or 'NCBI supplies no functional summary for this gene.',
        'source_url': 'https://www.ncbi.nlm.nih.gov/gene/' + identifier,
        'retrieved_date': discovery.now(), 'source_snapshot_sha256': discovery.sha(raw), 'note': NOTE,
        'lookup_receipts': receipts + [{'url':url, 'sha256':discovery.sha(raw)}]}
    result = {**mapped, 'status':'resolved', 'entrez_id':identifier, 'gene_symbol':symbol, 'biological_context':context}
    atomic_json(cache, {'record':result, 'sha256':hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()})
    return result
