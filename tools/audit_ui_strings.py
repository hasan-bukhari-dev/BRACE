"""Conservative, deterministic source-language inventory; no runtime dependencies.

The ledger includes internal literals rather than guessing that they cannot be
rendered. Generated-template policies cover exact user/backend values. This is
a coverage/lint tool, not proof of human comprehension or scientific validity.
"""
import ast,csv,hashlib,html,json,re
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
FIELDS='route component state literal_or_template audience_task semantic_category data_precondition exact_meaning visible_context_or_definition action_or_output evidence_source ambiguity_risk decision_keep_rewrite_remove test_id'.split()
POLICIES={
 'app.js':('B / CE / E','Select task; retain current analysis; open saved evidence','BRACE task and current-run context','D3_HOME_HISTORY'),
 'race.js':('RACE / FACE','Inspect source-selected associations and within-study measurements','Full frozen family, signed within-study effects, target BH q <=0.05; separate cohort axes','D3_PUBLIC_RACE_FACE'),
 'ace.js':('ACE / record inspector','Evaluate supplied classification records; filter saved confidence points','Correct/all evaluated; confidence>=threshold; exact retained denominator; source OOF separated','D3_NEUTRAL_PREDICTIONS'),
 'legacy-results.js':('CE','Compare measured distributions and inspect actual feature data','Source-fit PCA; KS/BH and source-IQR definitions adjacent; no causal claim','D3_MODE_C'),
 'study.js':('CE / intake','Choose and check task-specific inputs','Existing parser contracts; checks do not authenticate acquisition or independence','D3_PREFLIGHT'),
 'trace.js':('E / TRACE','Inspect actual calculation steps and selected result','Actual run ID, selected feature/record, artifacts and status; not performed stays absent','D3_TRACE'),
 'wordmark.js':('global navigation','Choose one of five tools with pointer or keyboard','Captions name tasks; arrows move focus and Enter/Space selects; aria-current marks the current page','D3_NAV'),
 'theme.js':('global theme','Choose saved System, Light or Dark preference','Appearance only; current science and selection retained','D3_THEME'),
 'theme-init.js':('global theme initialization','Apply saved/system theme before paint','Appearance only; absent preference uses OS','D3_THEME'),
 'export.js':('E / export','Download a genuine evidence ZIP or retry failure','Actual response type/signature; raw inputs excluded; sharing caveat','D3_EXPORT'),
 'embrace.py':('exported HTML / ZIP','Read result-first evidence, methods, limits and reproduction','Actual saved result and recorded role; published view wording separate from immutable numeric artifacts','D3_EXPORT'),
 'presentation.py':('ACE / generic exported report','Read task-neutral interpretation limits','Known display-only warning mapping; no scientific record, identifier or number rewritten','D3_NEUTRAL_PREDICTIONS'),
 'task_capabilities.json':('task chooser / CE','Choose an implemented analysis and understand its file requirements','Capability labels match existing parser/API; unsupported tasks explicitly bounded','D3_CAPABILITIES'),
 'index.html':('B / RACE / ACE / CE / E','Navigate, choose inputs, open evidence','Task context and individual accessible names; real handlers in application modules','D3_NAV'),
}
POLICIES.update({
 'journey.js':('all routes','Go Back/Forward and restore the selected study, inspector and setup step','Committed history is distinct from hover; local file permissions are not persisted','V6_NAV_HISTORY'),
 'operation.js':('all analysis routes','Understand which operation will run and which evidence is loaded','Methods reflect the supported task; opening a description does not rerun it','V6_METHOD_RECEIPTS'),
 'space.js':('SPACE public discovery','Search official public metadata, compare candidates and acquire bounded original files','Public terms only; candidates and acquired files are not scientific eligibility approval','V6_DISCOVERY'),
 'discovery.py':('SPACE API','Retrieve bounded official GEO metadata and public matrices with receipts','No uploads transmitted; fixed HTTPS hosts; explicit actions, cache, hashes and review gates','V6_DISCOVERY_SECURITY'),
 'provenance_origin.py':('result provenance','Identify exact bundled inputs by all six hashes','File origin does not authenticate patient independence or scientific equivalence','V6_PUBLIC_ORIGIN'),
 'family.js':('contextual FACE / TRACE / EMBRACE / SPACE','Recognize the name family alongside a plain task label','Name decoration never changes the action or scientific result','V6_FAMILY'),
})

def source_files():
    # Third-party bundles are separately licensed and SHA-inventoried in docs/quality/VENDOR_HASHES.json.
    # Audit every authored source literal, without parsing minified library internals.
    return sorted([p for folder in ('brace_app','brace_core') for p in (ROOT/folder).rglob('*') if p.suffix in {'.py','.js','.html','.json','.css'} and '__pycache__' not in p.parts and 'vendor' not in p.parts])
def js_literals(s):
    """Read quotes/templates/comments, recursively including template expressions.
    Regex bodies are skipped as syntax, including quotes in character classes.
    Division is distinguished by the preceding expression token in these modules.
    """
    found=[];n=len(s)
    def scan(i,expression=False):
        depth=0
        while i<n:
            if s.startswith('//',i):
                j=s.find('\n',i);i=n if j<0 else j+1;continue
            if s.startswith('/*',i):
                j=s.find('*/',i+2);i=n if j<0 else j+2;continue
            c=s[i]
            if c=='/':
                before=s[:i].rstrip()
                if before and (before[-1] in '(=:,[!?{;|&' or re.search(r'\breturn$',before)):
                    i+=1;in_class=False
                    while i<n:
                        if s[i]=='\\':i+=2;continue
                        if s[i]=='[':in_class=True
                        elif s[i]==']':in_class=False
                        elif s[i]=='/' and not in_class:
                            i+=1
                            while i<n and s[i].isalpha():i+=1
                            break
                        i+=1
                    continue
            if expression and c=='}' and depth==0:return i+1
            if c=='{':depth+=1
            elif c=='}':depth-=1
            if c not in "\"'`":i+=1;continue
            start=i;quote=c;i+=1
            while i<n:
                if s[i]=='\\':i+=2;continue
                if quote=='`' and s.startswith('${',i):i=scan(i+2,True);continue
                if s[i]==quote:
                    found.append((s.count('\n',0,start)+1,s[start+1:i],quote=='`'));i+=1;break
                i+=1
        return i
    scan(0);return found
class HtmlStrings(HTMLParser):
    def __init__(self):super().__init__();self.items=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        for k,v in attrs:
            if k in ('aria-label','title','placeholder','alt') and v:self.items.append((self.getpos()[0],v,False))
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():self.items.append((self.getpos()[0],data.strip(),False))
def literals(p,s):
    if p.suffix=='.js':return js_literals(s)
    if p.suffix=='.html':h=HtmlStrings();h.feed(s);return h.items
    if p.suffix=='.css':return [(s.count('\n',0,m.start())+1,m.group(1),True) for m in re.finditer(r'content\s*:\s*([^;}]+)',s)]
    if p.suffix=='.json':
        items=[]
        def visit(v):
            if isinstance(v,str):items.append((1,v,False))
            elif isinstance(v,dict):
                for x in v.values():visit(x)
            elif isinstance(v,list):
                for x in v:visit(x)
        visit(json.loads(s));return items
    tree=ast.parse(s);docstrings=set();joined=set()
    for node in ast.walk(tree):
        if isinstance(node,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str):docstrings.add(id(node.body[0].value))
        if isinstance(node,ast.JoinedStr):joined.update(id(n) for n in ast.walk(node) if n is not node and isinstance(n,(ast.Constant,ast.JoinedStr)))
    return [(node.lineno,ast.get_source_segment(s,node) if isinstance(node,ast.JoinedStr) else node.value,isinstance(node,ast.JoinedStr)) for node in ast.walk(tree) if id(node) not in joined and id(node) not in docstrings and (isinstance(node,ast.JoinedStr) or isinstance(node,ast.Constant) and isinstance(node.value,str))]
def category(value,template):
    if template or '<' in value and '>' in value:return 'generated_template'
    if re.search(r'\.(csv|json|html|zip|md|tsv)\b',value):return 'artifact_or_input_identifier'
    if re.search(r'\b(error|missing|invalid|blocked|cannot|must|required|exceed|duplicate|not found|mismatch|failed|unavailable)\b',value,re.I):return 'state_or_actionable_help'
    if re.search(r'\b(accuracy|confidence|support|variance|interval|q-value|median|count|mean|p-value|threshold|effect|BH|FDR|KS|PCA|recall|precision)\b',value,re.I):return 'measurement_or_definition'
    if re.search(r'\b(open|select|check|choose|download|export|return|close|retry|filter|compare|enter|view|inspect)\b',value,re.I):return 'action_or_task'
    if len(value.split())>1 or value[:1].isupper():return 'thing_state_or_recorded_method'
    return 'implementation_or_dynamic_field_literal'
def inventory():
    rows=[];coverage={};seen=set()
    for p in source_files():
        rel=p.relative_to(ROOT).as_posix();s=p.read_text(encoding='utf-8-sig');sha=hashlib.sha256(p.read_bytes()).hexdigest();items=literals(p,s);coverage[rel]={'sha256':sha,'literal_count':len(items)}
        route,task,context,test=POLICIES.get(p.name,('shared API / scientific intake / recorded output','Read exact parser errors, warnings, recorded identifiers or methods','Existing scientific contract and issue code; raw data fields retain exact saved meaning','D3_API_REGRESSION'))
        for line,value,template in sorted(items,key=lambda a:(a[0],a[1])):
            value=str(value)
            if not value.strip():continue
            key=(rel,line,value)
            if key in seen:continue
            seen.add(key);cat=category(value,template);short=html.unescape(re.sub('<[^>]+>',' ',value));short=re.sub(r'\s+',' ',short).strip()
            internal=cat=='implementation_or_dynamic_field_literal'
            meaning=('Internal key/selector/encoding/format; if shown in exact JSON or provenance, it retains its documented field meaning: ' if internal else 'Literal label/message or exact generated view: ')+short
            rows.append(dict(zip(FIELDS,[route,p.name,'applicable declared task / loaded, empty, busy, failed or recorded result branch',value,task,cat,'The surrounding source branch and data checks must hold; dynamic values are actual saved or user-supplied fields',meaning,context,'Specific handler, generated artifact or recorded field at the source location; no invented completion',f'{rel}:{line}; sha256={sha}','Internal field is not a freestanding task label' if internal else 'Dynamic declarations are unverified; scientific thresholds and denominators require adjacent definitions or recorded methods','keep',test])))
    policies=[
        ('GENERATED_USER_VALUES','User-supplied IDs, labels, filenames, study names and metadata','Render exact values through esc/html.escape; never certify declarations or infer biological meaning; no translated class IDs. Scientific CSV encoding has its own reversible ledger.'),
        ('GENERATED_ISSUES','Backend InputProblem / HTTP / compatibility warnings and errors','All production Python message literals are conservatively inventoried below. Preserve issue code, reason and actionable next_action; generic known independence warning has a display-only neutral mapping.'),
        ('GENERATED_JSON','Expandable raw scientific JSON / TRACE configuration, hashes and method fields','Exact saved keys/values and numerical nulls; JSON is evidence, not task copy. Original scientific artifacts remain unchanged. User data/metadata are not exhaustively enumerable in a source ledger.'),
        ('GENERATED_DOWNLOADS','Allowlisted export filenames and run IDs','Actual server-provided inventory; quoted/escaped and path-checked. Evidence ZIP named BRACE_EMBRACE_<actual run ID>.zip. No raw-input self-contained reproduction claim.'),
        ('GENERATED_NUMBERS','All counts, table cells, plot axes, point titles and uncertainty','Compute/display actual active result. fmt/pct rounding is presentation only; raw JSON/CSV exact. Zero-denominator values explicitly undefined/unavailable; target family stays frozen.'),
        ('GENERATED_STATUS','Real request progress, completion and failure','Only request/response-driven state. Failed requests remain failed/blocked, preserve files and expose retry. No timer-generated percentages or completed labels after failures.'),
        ('GENERATED_ARCHIVES','Historical pre-redesign HTML/CSV/JSON opened as original artifacts','Historical snapshots retain their archived wording and hashes. They are not current app copy or claims of current calculation; current EMBRACE report has task-aware result-first copy.'),
        ('GENERATED_CLI','Preserved CLI reports and help strings','Existing CLI compatibility and scientific reports retained; conservative source inventory includes their strings even when not rendered by current web UI. Full current app report uses embrace.report.'),
    ]
    for key,title,meaning in policies:rows.insert(0,dict(zip(FIELDS,['all','generated-template policy','all applicable states',title,'Preserve task accuracy and evidence identity','generated_value_policy','Actual checked result/input only',meaning,'Adjacent current-task context; original artifacts explicitly identified','Exact escaped display or allowlisted download','tools/audit_ui_strings.py policy '+key,'No authentication or independent human comprehension implied','keep',key])))
    return rows,coverage
BAN=re.compile(r'hold up|unlock|discover insights|AI[- ]powered|revolutionary|powerful platform|seamless|generalizabl|validated biomarker|\brobust\b|\breliable\b|\bconfident\b|\bsignificant\b|\bunsupported\b|\bcompleted\b|^(?:Run|Analyze|Explore|Next|Learn more)$',re.I)
def findings(rows):
    found=[]
    for r in rows:
        if r['semantic_category']=='generated_value_policy':continue
        matches=sorted(set(m.group().lower() for m in BAN.finditer(r['literal_or_template'])))
        if matches:
            found.append({'source':r['evidence_source'].split(';')[0],'matches':matches,'literal_or_template':r['literal_or_template'],'review':'Context required: unsupported means rejected input capability; completed is a genuine persisted state or a negated failure. Significant/robust/reliable require method-context review; no automatic replacement.'})
    return found
def generate():
    rows,coverage=inventory();out=ROOT/'docs/quality';out.mkdir(parents=True,exist_ok=True)
    with (ROOT/'docs/quality/UI_STRING_LEDGER.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,FIELDS);w.writeheader();w.writerows(rows)
    (out/'STRING_SOURCE_COVERAGE.json').write_text(json.dumps(coverage,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (out/'UI_LANGUAGE_LINT_FINDINGS.json').write_text(json.dumps(findings(rows),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ledger_rows':len(rows),'source_files':len(coverage),'lint_findings':len(findings(rows))}))
if __name__=='__main__':generate()
