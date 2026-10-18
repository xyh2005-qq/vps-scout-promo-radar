# ::ILANG
# ::STATE{@FILE, role:验证数据真实性边界与I-Lang配置实际生效}
# ::BOUNDARY{never:使用虚构优惠作为生产数据}
import copy
import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from config import ROOT,load_config
from scraper import racknerd,ramnode,greencloud,cloudcone,servarica,vpsdime,Fetcher,scrape,PARSERS
from build import build,live_offers

class PipelineTests(unittest.TestCase):
    def test_annual_price_and_plan_are_bound(self):
        p=load_config()['providers'][0]
        o=racknerd((ROOT/'tests/fixtures/racknerd.html').read_text(),p)[0]
        self.assertEqual(o['price'],'21.99');self.assertEqual(o['billing'],'year')
        self.assertEqual(o['title'],'1 GB KVM VPS');self.assertIn('pid=952',o['offer_url'])
    def test_ipv6_constraint_and_monthly_rate(self):
        p=load_config()['providers'][1]
        o=ramnode((ROOT/'tests/fixtures/ramnode.html').read_text(),p)[0]
        self.assertEqual(o['price'],'2');self.assertEqual(o['billing'],'month')
        self.assertIn('IPv6 only — no IPv4',o['specs'])
    def test_changed_unit_is_rejected(self):
        html=(ROOT/'tests/fixtures/racknerd.html').read_text().replace('/year','/week')
        with self.assertRaises(ValueError):racknerd(html,load_config()['providers'][0])
    def test_expired_stale_removed_are_not_live(self):
        now=datetime.now(timezone.utc);base=dict(provider='RackNerd',fetched_at=now.isoformat())
        data={'offers':[base,dict(base,valid_until='2001-01-01'),dict(base,fetched_at=(now-timedelta(days=3)).isoformat()),dict(base,status='expired'),dict(base,provider='Unlisted')]}
        self.assertEqual(live_offers(data,load_config(),now),[base])
    def test_robots_denial_never_fetches_page(self):
        f=Fetcher(load_config())
        with patch.object(f,'raw',return_value='User-agent: *\nDisallow: /') as raw:
            with self.assertRaises(ValueError):f.get('https://example.com/deals')
            self.assertEqual(raw.call_count,1)
    def test_invalid_robots_fails_closed(self):
        f=Fetcher(load_config())
        with patch.object(f,'raw',return_value='<html>Challenge</html>'):
            with self.assertRaises(ValueError):f.get('https://example.com/deals')
    def test_ilang_provider_change_changes_output(self):
        original=(ROOT/'.ilang/site.ilang').read_text()
        modified='\n'.join(x for x in original.splitlines() if not x.startswith('RamNode |'))
        data=json.loads((ROOT/'data/offers.json').read_text())
        for offer in data['offers']:offer['fetched_at']=datetime.now(timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'site.ilang';path.write_text(modified)
            cfg=load_config(path);out=Path(td)/'site';build(cfg,data,out)
            self.assertFalse((out/'providers/ramnode').exists())
            self.assertNotIn('RamNode',(out/'index.html').read_text())
            self.assertTrue((out/'providers/racknerd/index.html').exists())
    def test_greencloud_stock_and_quarterly_billing(self):
        p=next(p for p in load_config()['providers'] if p['parser']=='greencloud')
        rows=greencloud((ROOT/'tests/fixtures/greencloud.html').read_text(),p)
        self.assertEqual(len(rows),3)
        self.assertEqual([(o['price'],o['billing']) for o in rows],[('25.00','year'),('35.00','year'),('20.00','quarter')])
        from billing import monthly_value
        self.assertAlmostEqual(float(monthly_value(rows[2])),20/3)
        self.assertIn('No refund',rows[2]['billing_note'])
        from build import equivalent
        self.assertIn('full quarter upfront',equivalent(rows[2]))
    def test_cloudcone_uses_billed_total_not_headline_monthly(self):
        p=next(p for p in load_config()['providers'] if p['parser']=='cloudcone')
        rows=cloudcone((ROOT/'tests/fixtures/cloudcone.html').read_text(),p)
        self.assertEqual(rows[0]['price'],'28');self.assertEqual(rows[0]['billing'],'year')
        from presentation import memory
        self.assertEqual(memory(rows[0]),1)
    def test_servarica_currency_stock_and_product_type(self):
        p=next(p for p in load_config()['providers'] if p['parser']=='servarica')
        rows=servarica((ROOT/'tests/fixtures/servarica.html').read_text(),p)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['title'],'V3 KVM Slim Slice 2')
        self.assertEqual(rows[0]['price'],'77');self.assertEqual(rows[0]['billing'],'year')
        self.assertIn('$7/month',rows[0]['billing_note'])
    def test_vpsdime_price_bound_to_same_row(self):
        p=next(p for p in load_config()['providers'] if p['parser']=='vpsdime')
        rows=vpsdime((ROOT/'tests/fixtures/vpsdime.html').read_text(),p)
        self.assertEqual(rows[0]['price'],'5.00');self.assertEqual(rows[0]['billing'],'month')
        self.assertIn('4GB RAM',rows[0]['specs'])
        bad=(ROOT/'tests/fixtures/vpsdime.html').read_text().replace('/mo','/week')
        with self.assertRaises(ValueError):vpsdime(bad,p)
    def test_config_removal_changes_scrape_and_build(self):
        original=(ROOT/'.ilang/site.ilang').read_text()
        modified='\n'.join(line for line in original.splitlines() if not line.startswith('GreenCloud |'))
        fetched=[]
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);config_path=td/'site.ilang';config_path.write_text(modified)
            cfg=load_config(config_path)
            def fixture_fetch(url):
                fetched.append(url)
                provider=next(p for p in cfg['providers'] if p['source_url']==url)
                return (ROOT/'tests/fixtures'/f"{provider['parser']}.html").read_text(),url
            with patch.object(Fetcher,'get',side_effect=fixture_fetch):data=scrape(cfg,td/'offers.json')
            self.assertEqual(len(fetched),len(cfg['providers']))
            self.assertFalse(any('greencloud' in u for u in fetched))
            self.assertTrue(all(s['status']=='ok' for s in data['sources']))
            out=td/'site';build(cfg,data,out)
            self.assertFalse((out/'providers/greencloud').exists())
            self.assertNotIn('GreenCloud',(out/'index.html').read_text())
            self.assertNotIn('greencloud',(out/'sitemap.xml').read_text())
    def test_quarter_schema_and_dynamic_atlas(self):
        data=json.loads((ROOT/'data/offers.json').read_text())
        for offer in data['offers']:offer['fetched_at']=datetime.now(timezone.utc).isoformat()
        quarter=next(o for o in data['offers'] if o['billing']=='quarter')
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'site';build(data=data,out=out)
            detail=(out/'deals'/quarter['id']/'index.html').read_text()
            self.assertIn('P3M',detail);self.assertIn('/ quarter',detail)
            self.assertIn('full quarter upfront',detail)
            self.assertIn('No refund',detail)
        from presentation import atlas,memory
        graph=atlas(data['offers'])
        self.assertEqual(graph.count('data-plan='),sum(bool(memory(o)) for o in data['offers']))
    def test_atlas_preserves_published_annual_price(self):
        from presentation import client_offers, memory
        provider=load_config()['providers'][0]
        annual=racknerd((ROOT/'tests/fixtures/racknerd.html').read_text(),provider)[0]
        annual.update(id='racknerd-fixture',provider=provider['name'],kind='special',source_url=provider['source_url'])
        client=json.loads(client_offers([annual]))[0]
        self.assertEqual(client['price'],annual['price'])
        self.assertEqual(client['billing'],'year')
        self.assertAlmostEqual(client['monthly'],float(annual['price'])/12)
        self.assertEqual(memory(annual),1)
    def test_embedded_source_text_cannot_close_json_script(self):
        from presentation import client_offers
        provider=load_config()['providers'][0]
        offer=racknerd((ROOT/'tests/fixtures/racknerd.html').read_text(),provider)[0]
        offer.update(id='racknerd-fixture',provider=provider['name'],kind='special',source_url=provider['source_url'],title='</script><script>alert(1)</script>')
        encoded=client_offers([offer])
        self.assertNotIn('</script>',encoded)
        self.assertEqual(json.loads(encoded)[0]['name'],offer['title'])
    def test_empty_data_renders_honest_empty_state(self):
        now=datetime.now(timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as td:
            build(data={'generated_at':now,'offers':[],'sources':[]},out=Path(td)/'site')
            self.assertIn('No fresh verified offers',(Path(td)/'site/index.html').read_text())
if __name__=='__main__':unittest.main()
