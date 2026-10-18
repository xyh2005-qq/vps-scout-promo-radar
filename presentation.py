# ::ILANG
# ::STATE{@FILE, role:把可溯源套餐转换为可访问的图鉴与卡片}
# ::BOUNDARY{never:把计算值伪装成报价 或推断未公布性能}
import json
import math
import re
from decimal import Decimal
from html import escape
from billing import monthly_value, UPFRONT

def esc(value): return escape(str(value), quote=True)
def memory(offer):
    for spec in offer.get('specs', []):
        m=re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB)\s+(?:Dedicated\s+)?RAM\b',spec,re.I)
        if m:return float(m[1])/(1024 if m[2].upper()=='MB' else 1)
    return None

def client_offers(offers):
    return json.dumps([dict(id=o['id'],name=o['title'],provider=o['provider'],price=o['price'],billing=o['billing'],monthly=float(monthly_value(o)),memory=memory(o),kind=o['kind'],specs=o['specs'],url='/deals/'+o['id']+'/',source=o['source_url']) for o in offers],separators=(',',':')).replace('<','\\u003c')

def card(offer, provider, index):
    o,p=offer,provider
    prepaid=o['billing']!='month';ram=memory(o)
    specs=o['specs'][:4]
    ipv6=any('IPv6 only' in s for s in o['specs'])
    kind='Special' if o['kind']=='special' else 'Regular price'
    equivalent=f'≈ ${monthly_value(o):.2f} / month equivalent' if prepaid else 'Published monthly price'
    return f'''<article class="card" data-id="{esc(o['id'])}" data-provider="{esc(p['slug'])}" data-kind="{esc(o['kind'])}" data-monthly="{monthly_value(o)}" data-ram="{ram or 0}" data-index="{index}" data-search="{esc(o['title']+' '+o['provider']+' '+' '.join(o['specs']))}">
<div class="card-top"><a class="provider" href="/providers/{p['slug']}/"><span class="provider-glyph" aria-hidden="true">{esc(p['name'][:1])}</span>{esc(p['name'])}</a><span class="badge {o['kind']}"><i></i>{kind}</span></div>
<h3><a href="/deals/{o['id']}/">{esc(o['title'])}</a></h3><div class="price">${Decimal(o['price']):.2f}<span> / {o['billing']}</span></div><p class="equiv">{esc(equivalent)}</p>
<ul>{''.join('<li>'+esc(s)+'</li>' for s in specs)}</ul>{'<div class="ip-note">IPv6 only · no IPv4</div>' if ipv6 else ''}
<div class="card-bottom"><button class="compare-toggle" data-compare="{esc(o['id'])}" aria-pressed="false" aria-label="Compare {esc(o['provider']+' '+o['title'])}"><span aria-hidden="true">+</span> Compare</button><a class="card-link" href="/deals/{o['id']}/">Inspect plan <span aria-hidden="true">↗</span></a></div></article>'''

def atlas(offers):
    rows=[o for o in offers if memory(o)]
    if not rows:return '<div class="atlas-empty">Waiting for the next verified source check.</div>'
    chosen=min(rows,key=monthly_value);points=[]
    max_cost=max(200,10**math.ceil(math.log10(max(float(monthly_value(o)) for o in rows))))
    min_cost=min(1,10**math.floor(math.log10(min(float(monthly_value(o)) for o in rows))))
    max_ram=max(32,2**math.ceil(math.log2(max(memory(o) for o in rows))))
    min_ram=min(.5,2**math.floor(math.log2(min(memory(o) for o in rows))))
    mid_ram=math.sqrt(max_ram*min_ram)
    mid_cost=10**round((math.log10(min_cost)+math.log10(max_cost))/2)
    mid_x=5+90*math.log(mid_cost/min_cost)/math.log(max_cost/min_cost)
    for i,o in enumerate(rows):
        x=5+90*min(1,max(0,math.log(float(monthly_value(o))/min_cost)/math.log(max_cost/min_cost)))
        y=92-84*min(1,max(0,math.log2(memory(o)/min_ram)/math.log2(max_ram/min_ram)))
        selected=o['id']==chosen['id']
        label=f'{o["provider"]} {o["title"]}, ${monthly_value(o):.2f} monthly equivalent'
        points.append(f'<button class="map-point {o["kind"]}{" is-active" if selected else ""}" style="--x:{x:.2f}%;--y:{y:.2f}%" data-plan="{esc(o["id"])}" aria-label="{esc(label)}" aria-pressed="{str(selected).lower()}" tabindex="{0 if selected else -1}"><span></span></button>')
    return f'''<div class="map-frame"><div class="map-y"><span style="top:8%">{max_ram:g} GB</span><span style="top:50%">{mid_ram:g} GB</span><span style="top:92%">{min_ram:g} GB</span></div><div class="map-plot" role="group" aria-label="VPS map: monthly equivalent cost against RAM. Use arrow keys to explore plans."><div class="map-grid" aria-hidden="true"></div><div class="map-guide" aria-hidden="true"><span>MORE MEMORY</span>↑</div>{''.join(points)}</div><div class="map-x"><span style="left:5%">$${min_cost:g}</span><span style="left:{mid_x:.2f}%">$${mid_cost:g}</span><span style="left:95%">$${max_cost:g}</span></div></div><div class="map-selection" aria-live="polite"><div><span class="micro" id="map-provider">{esc(chosen['provider'])}</span><a id="map-name" href="/deals/{chosen['id']}/">{esc(chosen['title'])} <span>↗</span></a><span id="map-billing">${Decimal(chosen['price']):.2f} / {chosen['billing']} published price</span></div><strong id="map-price">${monthly_value(chosen):.2f}<small>/mo equiv.</small></strong></div>'''.replace('$$','$')
