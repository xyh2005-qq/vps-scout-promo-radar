# ::ILANG
# ::STATE{@FILE, role:读取并验证站点I-Lang配置}
# ::BOUNDARY{never:执行配置中的代码或隐式加载厂商}
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parent

def safe_url(value):
    p = urlsplit(value)
    if p.scheme != 'https' or not p.netloc or p.username or p.password:
        raise ValueError('Expected public HTTPS URL')
    return value

def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def load_config(path=None):
    text = Path(path or ROOT / '.ilang/site.ilang').read_text()
    if not text.startswith('::ILANG\n'):
        raise ValueError('Missing I-Lang header')
    state = re.search(r'::STATE\{@SITE, (.*?)\}', text).group(1)
    cfg = dict(x.strip().split(':', 1) for x in state.split(','))
    cfg = {k:v.strip() for k,v in cfg.items()}
    cfg.update(json.loads(re.search(r'^::CONFIG(.*)$', text, re.M).group(1)))
    safe_url(cfg['domain'])
    if cfg['locale'] != 'en-US':
        raise ValueError('This v1 supports en-US only; add regional sources before expanding')
    adapters = [json.loads(x) for x in re.findall(r'^::ADAPTER(.*)$', text, re.M)]
    by_name = {a['provider']:a for a in adapters}
    section = re.search(r'::MODULE\{PROVIDERS[^\n]*\}\n(.*?)(?=::MODULE)', text, re.S).group(1)
    cfg['providers'] = []
    for line in section.splitlines():
        if not line.strip(): continue
        name, home, source, affiliate = [x.strip() for x in line.split('|')]
        p = dict(by_name[name], name=name, slug=slug(name), home=safe_url(home), source_url=safe_url(source), affiliate_url=safe_url(affiliate) if affiliate else '')
        cfg['providers'].append(p)
    if len({p['slug'] for p in cfg['providers']}) != len(cfg['providers']):
        raise ValueError('Duplicate provider')
    return cfg
