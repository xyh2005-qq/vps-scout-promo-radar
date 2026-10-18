# ::ILANG
# ::STATE{@FILE, role:从I-Lang和真实数据生成静态页与索引}
# ::BOUNDARY{never:生成虚假价格日期库存 或把历史报价当有效优惠}
import json
import shutil
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from html import escape
from pathlib import Path
from string import Template
from config import ROOT, load_config, slug
from presentation import card as design_card, atlas, client_offers
from billing import monthly_value, DURATIONS, UPFRONT

def e(x):return escape(str(x),quote=True)
def monthly(o):return monthly_value(o)
def money(o):return '$'+format(Decimal(o['price']),'.2f')
def equivalent(o):
    note=o.get('billing_note','')
    return ('≈ $'+format(monthly(o),'.2f')+'/mo equivalent · '+UPFRONT[o['billing']].lower()+'. '+note) if o['billing']!='month' else (note or 'Monthly billing')

def live_offers(data,cfg,now=None):
    now=now or datetime.now(timezone.utc);names={p['name'] for p in cfg['providers']};out=[]
    for o in data['offers']:
        if o['provider'] not in names:continue
        stamp=datetime.fromisoformat(o['fetched_at'])
        if now-stamp>timedelta(hours=cfg['stale_hours']):continue
        if o.get('valid_until') and datetime.fromisoformat(o['valid_until'].replace('Z','+00:00')).replace(tzinfo=timezone.utc)<now:continue
        if o.get('status') in ('expired','error','removed'):continue
        out.append(o)
    return out

def build(cfg=None,data=None,out=None):
    cfg=cfg or load_config();data=data or json.loads((ROOT/'data/offers.json').read_text());out=Path(out or ROOT/'site')
    if out.exists():shutil.rmtree(out)
    out.mkdir(parents=True);shutil.copytree(ROOT/'assets',out/'assets')
    offers=live_offers(data,cfg);providers={p['name']:p for p in cfg['providers']};base=cfg['domain'].rstrip('/');pages=[]
    stamp=data['generated_at'];month=datetime.fromisoformat(stamp).strftime('%B %Y')
    def render(template,**context):return Template((ROOT/'templates'/template).read_text()).substitute(context)
    def offer_schema(o):
        s={'@type':'Offer','name':o['title'],'url':o['offer_url'],'seller':{'@type':'Organization','name':o['provider']}}
        if o.get('price') is not None:
            s.update(price=o['price'],priceCurrency=o['currency'],priceSpecification={'@type':'UnitPriceSpecification','price':o['price'],'priceCurrency':o['currency'],'unitText':'per '+o['billing'],'billingDuration':DURATIONS[o['billing']]})
        if o.get('valid_until'):s['priceValidUntil']=o['valid_until'][:10]
        if o.get('availability'):s['availability']=o['availability']
        return s
    def itemlist(rows):return {'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':base+'/deals/'+o['id']+'/'} for i,o in enumerate(rows)]}
    def page(path,title,description,body,schema=None,lastmod=stamp):
        canonical=base+path;schema=schema or []
        if path!='/':schema.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':base+'/'},{'@type':'ListItem','position':2,'name':title,'item':canonical}]})
        html=render('base.html',title=e(title),description=e(description),canonical=e(canonical),domain=e(base),brand=e(cfg['brand']),body=body,client_data=client_offers(offers),repository=(' · <a href="'+e(cfg['repository_url'])+'">GitHub</a>') if cfg['repository_url'] else '',schema=json.dumps({'@context':'https://schema.org','@graph':schema},ensure_ascii=False).replace('<','\\u003c'))
        target=out/path.strip('/')/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(html)
        pages.append((canonical,lastmod))
    def card(o,i):
        return design_card(o,providers[o['provider']],i)
    def cards(rows):return ''.join(card(o,i) for i,o in enumerate(rows)) or '<p class="notice">No fresh verified offers. Check back after the next successful source fetch.</p>'
    opts=''.join('<option value="'+p['slug']+'">'+e(p['name'])+'</option>' for p in cfg['providers'])
    page('/',f'{cfg["brand"]} — VPS deals & published prices | {month}',f'Compare {len(offers)} source-checked VPS plans from '+', '.join(providers)+f'. Real billing terms and official sources, {month}.',render('index.html',offer_count=len(offers),provider_count=len(providers),checked=e(stamp.replace('T',' ')[:16]+' UTC'),deployment_status=e(cfg['deployment_status']),provider_options=opts,cards=cards(offers),atlas=atlas(offers),special_count=sum(o['kind']=='special' for o in offers)),[itemlist(offers),{'@type':'WebSite','name':cfg['brand'],'url':base+'/'}])
    for p in cfg['providers']:
        rows=[o for o in offers if o['provider']==p['name']]
        services=[]
        for billing in ('year','quarter','month'):
            group=[o for o in rows if o['billing']==billing]
            if group:services.append({'@type':'Service','name':p['name']+' VPS '+billing+'ly plans','provider':{'@type':'Organization','name':p['name']},'offers':{'@type':'AggregateOffer','priceCurrency':p['currency'],'lowPrice':str(min(Decimal(o['price']) for o in group)),'highPrice':str(max(Decimal(o['price']) for o in group)),'offerCount':len(group),'offers':[offer_schema(o) for o in group]}})
        page('/providers/'+p['slug']+'/',f'{p["name"]} VPS offers & prices — {month}',f'{len(rows)} {p["name"]} VPS plans with original price, billing term and source evidence.',render('provider.html',provider_name=e(p['name']),intro=e(f'{len(rows)} fresh plans from the official provider page. Listing does not imply a hands-on review or endorsement.'),source_url=e(p['source_url']),cards=cards(rows)),services)
    for o in offers:
        p=providers[o['provider']];aff=p['affiliate_url'];target=aff or o['offer_url']
        body=render('deal.html',provider_path='/providers/'+p['slug']+'/',provider_name=e(p['name']),kind_label='Provider special' if o['kind']=='special' else 'Regular price',deal_title=e(o['title']),checked=e(datetime.fromisoformat(o['fetched_at']).strftime('%d %b %Y, %H:%M UTC')),specs=''.join('<li>'+e(s)+'</li>' for s in o['specs']),billing_note=e(equivalent(o)),price=money(o),billing=o['billing'],equivalent=e(equivalent(o)),offer_url=e(target),rel='sponsored noopener noreferrer' if aff else 'noopener noreferrer',link_disclosure='Affiliate link: we may earn a commission. Confirm the exact plan at the provider.' if aff else 'Direct provider link. No affiliate tracking added.',source_url=e(o['source_url']),expiry=e(o.get('valid_until','Not published')),evidence=e(o['evidence']),fingerprint=e(o['source_sha256']))
        page('/deals/'+o['id']+'/',f'{o["provider"]} {o["title"]} — {money(o)}/{o["billing"]} | {month}',f'{o["provider"]} {o["title"]}: {money(o)} per {o["billing"]}. Source evidence, specifications and billing notes.',body,[{'@type':'Service','name':o['title'],'provider':{'@type':'Organization','name':o['provider']},'offers':offer_schema(o)}],o['fetched_at'])
    rows=''.join(f'<tr><td><a href="/deals/{o["id"]}/">{e(o["title"])}</a><small>{e(o["provider"])}</small></td><td>{money(o)} / {o["billing"]}</td><td>${monthly(o):.2f}<small>{UPFRONT[o["billing"]]}</small></td><td>{e(o["kind"])}</td><td><button class="compare-toggle" data-compare="{e(o["id"])}" aria-pressed="false" aria-label="Compare {e(o["provider"]+" "+o["title"])}"><span aria-hidden="true">+</span> Compare</button></td></tr>' for o in sorted(offers,key=monthly))
    page('/compare/',f'Compare VPS prices & billing terms — {month}',f'Compare {len(offers)} VPS plans by real billing term and monthly equivalent. No fabricated discounts.',render('compare.html',rows=rows),[itemlist(offers)])
    method='<div class="page-heading"><p class="eyebrow">TRANSPARENCY BY DESIGN</p><h1>Show the source.<br>Explain the terms.</h1></div><article class="prose"><h2>What we publish</h2><p>VPS Scout is an independent directory of provider specials and regular published prices. We extract a plan name, price, billing term and specifications from the same official plan block. We do not claim to have tested uptime, support or performance.</p><h2>How freshness works</h2><p>Sources are checked against robots.txt. Failed sources contribute no current offers. Offers older than '+str(cfg['stale_hours'])+' hours are excluded on the next build. Expired offers are excluded. A static page can remain outdated if the update pipeline stops; always inspect its displayed source-check time.</p><p>Configured schedule: every six hours. '+e(cfg['deployment_status'])+'. Scheduling is best effort and may be delayed or disabled.</p><h2>How to compare</h2><p>Annual and quarterly prices are charged upfront for twelve or three months. Monthly equivalents divide by the actual billing-period length and are labeled as calculations. Explicitly sold-out plans are excluded by the relevant source adapters. Hourly billing, IPv6-only plans, taxes, extra traffic, region availability and renewal terms need separate attention. No stock or expiry claims are made unless published.</p><h2>Affiliate disclosure</h2><p>Current links are direct unless explicitly labeled affiliate links. Approved affiliate links may earn us commission. They are marked sponsored and do not change our price extraction. No fabricated commission figures, cookie injection, self-referrals or brand bidding.</p><h2>Sources</h2><ul>'+''.join('<li><a href="'+e(p['source_url'])+'">'+e(p['name'])+' official source</a></li>' for p in cfg['providers'])+'</ul><h2>Privacy</h2><p>No account, advertising pixels, analytics scripts or cookies are added by this site. Hosting and outbound providers may process request data under their own policies. Filters and selected comparison plans can be reflected in the page URL. No personal information is requested.</p><h2>Corrections</h2><p>If a source changes, offers are withheld until the parser is repaired. Source evidence and timestamps are available in the public dataset. Provider checkout is the final authority for price and availability.</p></article>'
    page('/methodology/','Sources, methodology & affiliate disclosure | '+cfg['brand'],'How VPS Scout checks official prices, handles failed sources and discloses affiliate links.',method)
    status='<div class="page-heading"><h1>Update status</h1><p>'+e(cfg['deployment_status'])+'</p></div><div class="table-wrap"><table><thead><tr><th>Provider</th><th>Last attempt (UTC)</th><th>Status</th><th>Plans</th></tr></thead><tbody>'+''.join('<tr><td>'+e(s['provider'])+'</td><td>'+e(s['attempted_at'])+'</td><td>'+e(s['status'])+'</td><td>'+str(s['count'])+'</td></tr>' for s in data['sources'] if s['provider'] in providers)+'</tbody></table></div>'
    page('/status/','Source update status | '+cfg['brand'],'Check source fetch timestamps and status.',status)
    (out/'data').mkdir();(out/'data/offers.json').write_text(json.dumps(dict(data,offers=offers),indent=2)+'\n')
    sitemap='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(url)+'</loc><lastmod>'+e(date)+'</lastmod></url>' for url,date in pages)+'</urlset>'
    (out/'sitemap.xml').write_text(sitemap);(out/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+base+'/sitemap.xml\n')
    (out/'404.html').write_text(render('base.html', title='Page not found | '+e(cfg['brand']), description='This plan may no longer be published. Explore current source-backed offers.', canonical=e(base+'/404.html'), domain=e(base), brand=e(cfg['brand']), repository='', client_data='[]', schema='{}', body='<section class="page-heading not-found"><span class="eyebrow">404 / SIGNAL NOT FOUND</span><h1>This signal<br><em>went quiet.</em></h1><p>The page may have moved, or the offer may no longer be published. There are other places to look.</p><a class="button" href="/">Back to the field guide <span>↗</span></a></section>'))
    (out/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: DENY\n')
    workflow=(ROOT/'templates/update.yml').read_text().replace('__CRON__',cfg['cron'])
    (ROOT/'.github/workflows/update.yml').write_text(workflow)
    print(f'Built {len(pages)} pages / {len(offers)} fresh offers into {out}')
    return pages
if __name__=='__main__':build()
