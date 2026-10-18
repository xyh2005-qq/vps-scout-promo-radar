# ::ILANG
# ::STATE{@FILE, role:遵守robots抓取官方套餐并保留字段证据}
# ::BOUNDARY{never:猜价格 绕反爬 登录抓取 执行远端代码}
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser
from config import ROOT, load_config, safe_url, slug

class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())
    def find(self, tag=None, cls=None):
        found=[]
        for c in self.children:
            if isinstance(c, Node):
                if (tag is None or c.tag==tag) and (cls is None or cls in c.attrs.get('class','').split()): found.append(c)
                found.extend(c.find(tag,cls))
        return found

class Tree(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.root=Node();self.stack=[self.root];self.feed(body)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}: self.stack.append(n)
    def handle_startendtag(self,tag,attrs): self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag: self.stack=self.stack[:i];break
    def handle_data(self,data): self.stack[-1].children.append(data)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class Fetcher:
    def __init__(self,cfg):
        self.ua='VPSScoutBot/1.0 (+%s/methodology/)' % cfg['domain']
        self.opener=urllib.request.build_opener(NoRedirect())
        self.robots={};self.last={}
    def raw(self,url):
        req=urllib.request.Request(safe_url(url),headers={'User-Agent':self.ua,'Accept':'text/html,text/plain;q=0.9'})
        with self.opener.open(req,timeout=25) as r:
            b=r.read(5_000_001)
            if len(b)>5_000_000: raise ValueError('Source too large')
            return b.decode(r.headers.get_content_charset() or 'utf-8')
    def policy(self,url):
        p=urllib.parse.urlsplit(url);origin=p.scheme+'://'+p.netloc
        if origin not in self.robots:
            u=origin+'/robots.txt'
            try:
                for _ in range(4):
                    try: body=self.raw(u);break
                    except urllib.error.HTTPError as e:
                        if e.code in (301,302,303,307,308): u=urllib.parse.urljoin(u,e.headers['Location']);continue
                        raise
                else: raise ValueError('Too many robots redirects')
                if '<html' in body.lower() or not re.search(r'user-agent\s*:',body,re.I): raise ValueError('Unusable robots.txt')
            except urllib.error.HTTPError as e:
                if e.code in (404,410): body='User-agent: *\nAllow: /'
                else: raise
            rp=urllib.robotparser.RobotFileParser();rp.parse(body.splitlines());self.robots[origin]=rp
        return origin,self.robots[origin]
    def get(self,url):
        for _ in range(5):
            origin,rp=self.policy(url)
            if not rp.can_fetch('VPSScoutBot',url): raise ValueError('Blocked by robots.txt')
            delay=max(1,rp.crawl_delay('VPSScoutBot') or rp.crawl_delay('*') or 0)
            rate=rp.request_rate('VPSScoutBot') or rp.request_rate('*')
            if rate: delay=max(delay,rate.seconds/rate.requests)
            if delay>30: raise ValueError('Crawl delay too long for bounded job')
            time.sleep(max(0,delay-(time.monotonic()-self.last.get(origin,0))))
            self.last[origin]=time.monotonic()
            try: return self.raw(url),url
            except urllib.error.HTTPError as e:
                if e.code in (301,302,303,307,308): url=urllib.parse.urljoin(url,e.headers['Location']);continue
                raise
        raise ValueError('Too many redirects')

def racknerd(body,p):
    offers=[]
    for n in Tree(body).root.find('article','sn-plan'):
        title=n.find('h3')[0].text()
        if 'VPS' not in title: continue
        price_text=n.find('p','sn-price')[0].text()
        m=re.fullmatch(r'\$\s*(\d+(?:\.\d{1,2})?)\s*/year',price_text)
        links=[a.attrs['href'] for a in n.find('a') if 'Order now' in a.text()]
        if not m or len(links)!=1: raise ValueError('RackNerd pricing layout changed')
        specs=[x.text() for x in n.find('li')]
        offers.append(dict(title=title,price=m[1],billing='year',offer_url=safe_url(links[0]),specs=specs,evidence=title+' | '+price_text+' | '+' | '.join(specs)))
    return offers

def ramnode(body,p):
    offers=[]
    for n in Tree(body).root.find('section'):
        headings=n.find('h2')
        if not headings:continue
        title=headings[0].text()
        if 'VPS' not in title:continue
        tables=n.find('table','pricing-table')
        if not tables:continue
        for row in tables[0].find('tr'):
            cells=[x.text() for x in row.find('td')]
            if not cells:continue
            if len(cells)!=5:raise ValueError('RamNode columns changed')
            mem,cpu,disk,transfer,price_text=cells
            m=re.match(r'^\$(\d+(?:\.\d{1,2})?)/mo\b',price_text)
            if not m:raise ValueError('RamNode price format changed')
            headings_text=[x.text() for x in tables[0].find('th')]
            specs=[mem+' RAM',cpu,disk+' '+headings_text[2],transfer+' transfer']
            if 'IPv6' in title:specs.append('IPv6 only — no IPv4')
            offers.append(dict(title=mem+' '+title.split(' – ')[0],price=m[1],billing='month',offer_url=p['source_url']+'#'+n.attrs.get('id',''),specs=specs,evidence=' | '.join(cells),billing_note='Published monthly rate; provider bills hourly.'))
    return offers

def greencloud(body,p):
    offers=[]
    for n in Tree(body).root.find('div','product'):
        stock=n.find('span','qty')
        if not stock or not re.fullmatch(r'\d+ Available',stock[0].text()):
            raise ValueError('GreenCloud stock format changed')
        if int(stock[0].text().split()[0])==0:continue
        title=n.find('header')[0].find('span')[0].text()
        price_text=n.find('div','product-pricing')[0].text()
        price=re.fullmatch(r'\$(\d+(?:\.\d{1,2})?) USD (Annually|Quarterly)',price_text)
        links=n.find('a','btn-order-now')
        if not price or len(links)!=1:raise ValueError('GreenCloud annual pricing changed')
        specs=[x.text() for x in n.find('li')]
        note=n.find('div','product-desc')[0].find('p')[0].text()
        offers.append(dict(title=title,price=price[1],billing='year' if price[2]=='Annually' else 'quarter',offer_url=safe_url(urllib.parse.urljoin(p['source_url'],links[0].attrs['href'])),specs=specs,billing_note=note,evidence=title+' | '+price_text+' | '+stock[0].text()+' | '+note+' | '+' | '.join(specs)))
    return offers

def cloudcone(body,p):
    offers=[]
    for n in Tree(body).root.find('div','pricing'):
        headings=n.find('h3')
        if not headings or not headings[0].text().startswith('SSD VPS '):continue
        billed=n.find('span','type--fine-print')[0].text()
        price=re.fullmatch(r'Billed \$(\d+(?:\.\d{1,2})?) per year, USD',billed)
        if not price:raise ValueError('CloudCone annual billing changed')
        title=headings[0].text();specs=[x.text() for x in n.find('li')]
        links=[a for a in n.find('a') if a.text() in ('Deploy VPS','Purchase Plan')]
        if len(links)!=1:raise ValueError('CloudCone order link changed')
        offers.append(dict(title=title,price=price[1],billing='year',offer_url=safe_url(links[0].attrs['href']),specs=specs,evidence=title+' | '+billed+' | '+' | '.join(specs)))
    return offers

def servarica(body,p):
    offers=[]
    for n in Tree(body).root.find('tr','plan-row'):
        tags=[x.text() for x in n.find('span','pt-ff')]
        if 'VPS' not in tags or n.attrs.get('data-status')!='current' or 'Out of stock' in n.text():continue
        cells={c.attrs.get('data-label'):c for c in n.find('td')}
        title=cells['Plan'].find('a','pt-name')[0].text()
        annual=cells['Price'].find('span','pt-annual')[0].find('span','m-usd')[0].text()
        price=re.fullmatch(r'\$(\d+(?:\.\d{1,2})?)/yr',annual)
        if not price:raise ValueError('ServaRica annual USD price changed')
        monthly=cells['Price'].find('strong')[0].find('span','m-usd')[0].text()
        if not re.fullmatch(r'\$\d+(?:\.\d{1,2})?',monthly):raise ValueError('ServaRica monthly USD price changed')
        specs=[cells['CPU'].text()+' ('+cells['CPU Type'].text()+')',cells['RAM'].text()+' RAM']
        specs += [cells[k].text()+' storage' for k in ('NVMe / SSD','HDD') if cells[k].text()!='—']
        specs.append(cells['BW transfer cap'].text()+' transfer cap')
        links=n.find('a','pt-order')
        if len(links)!=1:raise ValueError('ServaRica order link changed')
        note='Annual prepayment price; separate monthly option published at '+monthly+'/month.'
        offers.append(dict(title=title,price=price[1],billing='year',offer_url=safe_url(links[0].attrs['href']),specs=specs,billing_note=note,evidence=title+' | USD '+annual+' | USD '+monthly+'/mo | '+' | '.join(specs)))
    return offers

def vpsdime(body,p):
    offers=[]
    for n in Tree(body).root.find('tr'):
        links=[a for a in n.find('a') if '/buy/linux' in a.attrs.get('href','')]
        if not links:continue
        cells=[c.text() for c in n.find('td')]
        if len(cells)!=8 or len(links)!=1:raise ValueError('VPSDime columns changed')
        cpu,cores,ram,disk,transfer,port,price_text,_=cells
        price=re.fullmatch(r'\$(\d+(?:\.\d{1,2})?)/mo',price_text)
        if not price:raise ValueError('VPSDime monthly price changed')
        title=ram.split()[0]+' Linux VPS'
        specs=[cores+' ('+cpu+')',ram.split()[0]+' RAM',disk+' storage',transfer+' transfer',port+' port']
        offers.append(dict(title=title,price=price[1],billing='month',offer_url=safe_url(links[0].attrs['href']),specs=specs,evidence=' | '.join(cells[:-1])))
    return offers

PARSERS={'racknerd':racknerd,'ramnode':ramnode,'greencloud':greencloud,'cloudcone':cloudcone,'servarica':servarica,'vpsdime':vpsdime}

def scrape(cfg=None,dest=None):
    cfg=cfg or load_config();fetcher=Fetcher(cfg);offers=[];sources=[]
    for p in cfg['providers']:
        now=datetime.now(timezone.utc).isoformat(timespec='seconds')
        status=dict(provider=p['name'],source_url=p['source_url'],attempted_at=now)
        try:
            body,final=fetcher.get(p['source_url'])
            rows=PARSERS[p['parser']](body,p)
            if not rows: raise ValueError('No offers parsed; source needs review')
            digest=hashlib.sha256(body.encode()).hexdigest()
            for o in rows:
                if float(o['price'])<=0: raise ValueError('Non-positive price')
                o.update(id=p['slug']+'-'+slug(o['title']),provider=p['name'],currency=p['currency'],kind=p['kind'],source_url=final,fetched_at=now,source_sha256=digest)
            if len({o['id'] for o in rows})!=len(rows):raise ValueError('Duplicate offer IDs')
            offers.extend(rows);status.update(status='ok',count=len(rows),sha256=digest)
        except Exception as e:
            status.update(status='error',count=0,error=str(e)[:240])
        sources.append(status)
        print(p['name'],status['status'],status.get('count'),status.get('error',''))
    result=dict(generated_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),offers=offers,sources=sources)
    dest=Path(dest) if dest else ROOT/'data/offers.json';dest.parent.mkdir(exist_ok=True)
    tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');tmp.replace(dest)
    return result

if __name__=='__main__': scrape()
