# ::ILANG [TYPE:code][PROJECT:vps-deals]
# ::STATE{@SELF, role:验证拒绝假报价及配置生效}
# ::BOUNDARY{never:将测试夹具当真实优惠发布}
import json, tempfile, unittest
from pathlib import Path
from config import ROOT, load
from scraper import extract
from build import build

class PipelineTests(unittest.TestCase):
    def test_no_price_from_marketing_text(self):
        self.assertEqual(extract('<h2>Super VPS</h2><p>Was $99 now $5 renewal $20</p>',load()['providers'][1]),[])
    def test_named_structured_plan_and_expiry(self):
        p=load()['providers'][1]
        html='<script type="application/ld+json">'+json.dumps({'@type':'Product','name':'KVM 1','offers':{'@type':'Offer','price':'4.99','priceCurrency':'USD','priceValidUntil':'2020-01-01'}})+'</script>'
        rows=extract(html,p); self.assertEqual(rows[0]['price'],'4.99'); self.assertEqual(rows[0]['valid_until'],'2020-01-01')
    def test_config_changes_rendered_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=Path(folder)/'site.ilang'; cfg.write_text((ROOT/'.ilang/site.ilang').read_text(encoding='utf-8').replace('Vultr |','TestProvider |'),encoding='utf-8')
            out=Path(folder)/'site'; build(cfg,out,preview=True)
            self.assertTrue((out/'providers/testprovider/index.html').exists()); self.assertFalse((out/'providers/vultr/index.html').exists())
            self.assertIn('TestProvider',(out/'index.html').read_text(encoding='utf-8'))
    def test_cron_matches_config(self):
        self.assertIn("cron: '"+load()['update_cron']+"'",(ROOT/'.github/workflows/update.yml').read_text(encoding='utf-8'))
    def test_price_cannot_leak_from_next_card(self):
        html='<article class="sn-plan"><h3>1 GB KVM VPS</h3></article><article class="sn-plan"><h3>2 GB KVM VPS</h3><p class="sn-price"><span>$</span>35.99<small>/year</small></p><a href="https://my.racknerd.com/cart.php?a=add&amp;pid=953">Order</a></article>'
        rows=extract(html,load()['providers'][0]); self.assertEqual(len(rows),1); self.assertEqual(rows[0]['model'],'2 GB KVM VPS')

if __name__=='__main__': unittest.main()
