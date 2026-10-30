import csv, io, json, os, sqlite3, urllib.parse
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DB=ROOT/'regaintravel.db'
COUNTRIES={'United Kingdom':('verified','verified'),'United States':('verified','verified'),'Ireland':('verified','verified'),'Jamaica':('verified','verified'),'United Arab Emirates':('verified','verified'),'Mexico':('unverified','verified'),'Canada':('unverified','unverified'),'Australia':('unverified','unverified'),'Bahamas':('verified','unverified')}
SOURCES=['Google','Bing','Reddit','LinkedIn','Facebook','Travel forums']
def conn():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 with conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,url TEXT,source TEXT,country TEXT,notes TEXT,status TEXT DEFAULT "New",created TEXT)')
  c.execute('CREATE TABLE IF NOT EXISTS markets(country TEXT PRIMARY KEY,recruitment TEXT,travel TEXT,notes TEXT)')
  for name,(r,t) in COUNTRIES.items():c.execute('INSERT OR IGNORE INTO markets VALUES(?,?,?,?)',(name,r,t,'Confirm current eligibility before acting'))
def allrows(sql,args=()):
 with conn() as c:return [dict(x) for x in c.execute(sql,args)]
def esc(x):
 import html
 return html.escape(str(x or ''),quote=True)
def page(body):
 return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RegainTravel AI</title><style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#e8f1ff;background:#0b1424}*{box-sizing:border-box}body{margin:0}.shell{max-width:1200px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}h1{font-size:28px;margin:0}h2{margin-top:0}p,small{color:#aebdd2}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}a{color:#73d3ff}nav a,.btn,button{background:#1c3351;color:white;text-decoration:none;border:1px solid #34516e;border-radius:9px;padding:10px 14px;cursor:pointer;font-size:14px}nav a:hover,.btn:hover,button:hover{background:#285075}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:14px}.panel{background:#13233a;border:1px solid #2a405d;border-radius:14px;padding:20px;margin:12px 0}.stat{font-size:30px;font-weight:700;color:#7be4c5}input,select,textarea{width:100%;padding:10px;background:#0c192b;color:white;border:1px solid #415773;border-radius:8px;margin:6px 0 14px}label{font-weight:600;font-size:13px}table{width:100%;border-collapse:collapse;min-width:650px}td,th{padding:11px;text-align:left;border-bottom:1px solid #2b425c;vertical-align:top}th{color:#95dfff}.scroll{overflow:auto}.muted{color:#aebdd2}.warn{color:#ffcf84}.good{color:#81e3b7}.actions{display:flex;gap:8px;flex-wrap:wrap}button.danger{background:#602d39}.tag{font-size:12px;padding:4px 8px;border-radius:20px;background:#294462}.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:15px}code{color:#a5e9ff}</style></head><body><div class="shell"><header><div><h1>✈ RegainTravel AI</h1><small>International Finder • Local Windows edition</small></div><span class="tag">UK launch market</span></header><nav><a href="/">Dashboard</a><a href="/discover">Discover</a><a href="/leads?kind=recruitment">Recruitment</a><a href="/leads?kind=travel">Holiday customers</a><a href="/markets">Country checks</a><a href="/export">Export CSV</a></nav>'''+body+'''<p><small>Searches open in your browser. No platform scraping, automated messaging, or unverified lead claims. Verify consent, residency, and company rules before contact.</small></p></div></body></html>'''
def dashboard():
 rows=allrows('SELECT kind,status,count(*) n FROM leads GROUP BY kind,status');count=lambda kind:sum(x['n'] for x in rows if x['kind']==kind)
 recent=allrows('SELECT * FROM leads ORDER BY id DESC LIMIT 6')
 return page(f'<div class="grid"><div class="panel"><p>Recruitment leads</p><div class="stat">{count("recruitment")}</div></div><div class="panel"><p>Holiday enquiries</p><div class="stat">{count("travel")}</div></div><div class="panel"><p>Initial market</p><div class="stat">UK</div></div></div><div class="two"><div class="panel"><h2>Find business partners</h2><p>Discover public expressions of interest in independent travel businesses. Confirm market eligibility and age before discussing enrolment.</p><a class="btn" href="/discover?kind=recruitment">Find recruitment leads</a></div><div class="panel"><h2>Find holiday customers</h2><p>Discover travel planning requests and record only relevant, permitted information.</p><a class="btn" href="/discover?kind=travel">Find holiday enquiries</a></div></div><div class="panel"><h2>Recently saved</h2>'+leadtable(recent)+'</div>')
def leadtable(rows):
 if not rows:return '<p>No leads saved yet. Open Discover to begin.</p>'
 return '<div class="scroll"><table><tr><th>Lead</th><th>Pipeline</th><th>Country</th><th>Status</th><th>Actions</th></tr>'+''.join(f'<tr><td><strong>{esc(r["title"])}</strong><br><small>{esc(r["source"])} • {esc(r["created"])}</small><br>{("<a href="+chr(34)+esc(r["url"])+chr(34)+" target=_blank rel=noopener>Open source</a>") if r["url"] else ""}<br><small>{esc(r["notes"])}</small></td><td>{esc(r["kind"])}</td><td>{esc(r["country"])}</td><td>{esc(r["status"])}</td><td><form method="post" action="/status"><input type="hidden" name="id" value="{r["id"]}"><select name="status">'+''.join(f'<option {"selected" if r["status"]==s else ""}>{s}</option>' for s in ['New','Review','Contacted','Qualified','Closed'])+'</select><button>Update</button></form></td></tr>' for r in rows)+'</table></div>'
def discover(q):
 kind=q.get('kind',['travel'])[0];kind=kind if kind in ('travel','recruitment') else 'travel';terms={'travel':['looking for travel agent UK','recommend a travel advisor UK','help booking family holiday UK','looking for cruise travel agent UK','honeymoon travel agent recommendations UK'],'recruitment':['interested in becoming independent travel agent UK','how to start a travel business UK','become home based travel advisor UK','independent travel advisor opportunity UK']}[kind]
 links=[]
 for term in terms:
  for source,domain in [('Google',''),('Reddit','site:reddit.com '),('LinkedIn','site:linkedin.com/posts/ '),('Facebook','site:facebook.com '),('Travel forums','site:tripadvisor.co.uk/ShowTopic '),('Bing','')]:
   engine='https://www.bing.com/search?q=' if source=='Bing' else 'https://www.google.com/search?q='
   url=engine+urllib.parse.quote(domain+'"'+term+'"')
   links.append(f'<a class="btn" target="_blank" rel="noopener" href="{esc(url)}">{esc(source)}: {esc(term)}</a>')
 return page('<h2>Public discovery — '+('Recruitment' if kind=='recruitment' else 'Holiday customers')+'</h2><p>Choose a public search. Review results yourself; only save genuine, relevant enquiries where outreach is permitted. Search results are not confirmed leads.</p><div class="actions">'+''.join(links)+'</div>'+form(kind))
def form(kind):
 return f'''<div class="panel"><h2>Save a reviewed public enquiry</h2><form method="post" action="/add"><input type="hidden" name="kind" value="{kind}"><div class="two"><div><label>Lead description</label><input name="title" required maxlength="180" placeholder="e.g. Public request for cruise advice"></div><div><label>Public source URL</label><input name="url" type="url" placeholder="https://..."></div><div><label>Source</label><select name="source">{''.join('<option>'+esc(x)+'</option>' for x in SOURCES)}</select></div><div><label>Customer or prospect's country (not destination)</label><select name="country">{''.join('<option>'+esc(x)+'</option>' for x in COUNTRIES)}</select></div></div><label>Notes (avoid sensitive personal information)</label><textarea name="notes" rows="3"></textarea><button>Save lead</button></form></div>'''
def leads(q):
 kind=q.get('kind',['travel'])[0];kind=kind if kind in ('travel','recruitment') else 'travel'
 rows=allrows('SELECT * FROM leads WHERE kind=? ORDER BY id DESC',(kind,))
 return page('<h2>'+('Recruitment pipeline' if kind=='recruitment' else 'Holiday customer pipeline')+'</h2><p>Separate workflow • '+str(len(rows))+' saved enquiries</p><a class="btn" href="/discover?kind='+kind+'">Discover and add</a><div class="panel">'+leadtable(rows)+'</div>')
def markets():
 rows=allrows('SELECT * FROM markets ORDER BY country');return page('<h2>Country eligibility checks</h2><p><span class="good">Verified</span> means a published company source identifies the market; it is not approval for every individual or activity. <span class="warn">Unverified</span> means do not assume eligibility. Confirm current policies directly.</p><div class="panel scroll"><table><tr><th>Country</th><th>PlanNet recruitment</th><th>InteleTravel sales</th><th>Notes</th></tr>'+''.join(f'<tr><td>{esc(x["country"])}</td><td>{esc(x["recruitment"])}</td><td>{esc(x["travel"])}</td><td>{esc(x["notes"])}</td></tr>' for x in rows)+'</table></div><p>Official references: <a href="https://plannetmarketing.com/en-ie/Downloads" target="_blank">PlanNet legal documents</a> · <a href="https://www2.inteletravel.com/contact" target="_blank">InteleTravel market statement</a></p>')
class Handler(BaseHTTPRequestHandler):
 def send(self,body,typ='text/html; charset=utf-8',code=200):
  raw=body.encode('utf-8') if isinstance(body,str) else body;self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  u=urllib.parse.urlsplit(self.path);q=urllib.parse.parse_qs(u.query)
  if u.path=='/':return self.send(dashboard())
  if u.path=='/discover':return self.send(discover(q))
  if u.path=='/leads':return self.send(leads(q))
  if u.path=='/markets':return self.send(markets())
  if u.path=='/export':
   out=io.StringIO();w=csv.writer(out);w.writerow(['id','kind','title','url','source','country','notes','status','created']);[w.writerow(list(x.values())) for x in allrows('SELECT id,kind,title,url,source,country,notes,status,created FROM leads ORDER BY id')];return self.send(out.getvalue(),'text/csv; charset=utf-8')
  self.send('Not found',code=404)
 def do_POST(self):
  length=min(int(self.headers.get('Content-Length','0')),20000);p=urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8','replace'));get=lambda k:p.get(k,[''])[0].strip()
  if self.path=='/add':
   kind=get('kind');title=get('title')[:180];url=get('url')[:2000];country=get('country')
   if kind not in ('travel','recruitment') or not title or country not in COUNTRIES or (url and not url.startswith(('https://','http://'))):return self.send('Invalid lead',code=400)
   with conn() as c:c.execute('INSERT INTO leads(kind,title,url,source,country,notes,created) VALUES(?,?,?,?,?,?,?)',(kind,title,url,get('source')[:80],country,get('notes')[:1500],datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')))
   dest='/leads?kind='+kind
  elif self.path=='/status':
   status=get('status');id=get('id');
   if status not in ['New','Review','Contacted','Qualified','Closed'] or not id.isdigit():return self.send('Invalid status',code=400)
   with conn() as c:c.execute('UPDATE leads SET status=? WHERE id=?',(status,int(id)))
   dest='/'
  else:return self.send('Not found',code=404)
  self.send_response(303);self.send_header('Location',dest);self.end_headers()
if __name__=='__main__':
 init();print('RegainTravel AI: http://127.0.0.1:8765');ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
