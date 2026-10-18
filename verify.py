# ::ILANG
# ::STATE{@FILE, role:验证生成HTML的链接 元数据 JSON-LD和真实数据对应}
# ::BOUNDARY{never:把本地校验冒充Google富媒体测试}
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit
from config import ROOT, load_config

def verify(root=None):
    root=Path(root or ROOT/'site');cfg=load_config();count=0
    offers=json.loads((root/'data/offers.json').read_text())['offers']
    for path in root.rglob('index.html'):
        body=path.read_text();count+=1
        canonical=re.findall(r'<link rel="canonical" href="([^"]+)"',body)
        assert len(canonical)==1,(path,'canonical')
        assert not re.search(r'</[a-z]+\s+[a-z]+=',body), (path,'Malformed closing tag')
        assert canonical[0].startswith(cfg['domain']),path
        assert (root/'assets/social.png').exists(), 'Missing social card'
        for key in ('name="description"','property="og:image"','name="twitter:card"','<title>'):
            assert key in body,(path,key)
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',body,re.S):
            graph=json.loads(raw);assert graph['@context']=='https://schema.org'
        for attr,url in re.findall(r'(href|src)="([^"]+)"',body):
            url=unescape(url)
            if url.startswith('/') and not url.startswith('//'):
                target=root/urlsplit(url).path.lstrip('/')
                if target.is_dir():target/='index.html'
                assert target.exists(),(path,url)
        assert not re.search(r'\$(?:brand|cards|schema|body)\b',body),path
    for o in offers:
        page=root/'deals'/o['id']/'index.html'
        assert page.exists(),o['id']
        assert o['source_sha256'] in page.read_text()
        assert o['source_url'] and o['evidence'] and o['fetched_at']
    print(f'Validated {count} pages; {len(offers)} source-backed offers; local links and JSON-LD parse correctly.')
if __name__=='__main__':verify()
