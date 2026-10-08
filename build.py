# ::ILANG [TYPE:code][PROJECT:vps-deals]
# ::STATE{@SELF, role:从I-Lang与已核验数据构建静态站}
# ::BOUNDARY{never:编价格 编优惠幅度 猜生产地址 发布过期报价}
import argparse, json, os, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html import escape
from string import Template
from urllib.parse import urlparse
from config import ROOT, load, slug

def build(config=None, output=None, preview=False):
    cfg=load(config); out=Path(output or ROOT/'site'); base=cfg['base_url'].rstrip('/')
    if base=='pending':
        if preview: base='http://localhost:8000'
        else: raise ValueError('Set actual production base_url and domain in .ilang/site.ilang after Pages assigns it')
    if not preview and (urlparse(base).scheme!='https' or urlparse(base).netloc!=cfg['domain']): raise ValueError('Production domain/base_url mismatch')
    dataset=json.loads((ROOT/'data/offers.json').read_text(encoding='utf-8')); now=datetime.now(timezone.utc)
    providers={p['name']:p for p in cfg['providers']}; offers=[]
    for o in dataset['offers']:
        try:
            fetched=datetime.fromisoformat(o['fetched_at']); fresh=now-fetched <= timedelta(hours=int(cfg['stale_hours'])) and fetched<=now
            until=datetime.fromisoformat(o['valid_until'].replace('Z','+00:00')) if o.get('valid_until') else None
            if until and len(o['valid_until'])==10: until=until.replace(hour=23,minute=59,second=59)
            active=until is None or until.replace(tzinfo=until.tzinfo or timezone.utc)>=now
            if fresh and active and o['provider'] in providers and o['source_url']==providers[o['provider']]['source']: offers.append(o)
        except (ValueError,KeyError): continue
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True); sitemap=[]
    month=now.strftime('%B %Y'); brand=cfg['brand']; esc=lambda s:escape(str(s),quote=True)
    checked={x['provider']:x for x in dataset['checks']}
    def link(o): return '/deals/'+o['id']+'/'
    def card(o):
        return '<article><span class="badge">Official plan · '+esc(o['billing_period'])+'</span><h3><a href="'+link(o)+'">'+esc(o['title'])+'</a></h3><p class="price">'+esc(o['currency']+' '+o['price'])+'</p><p>Checked '+esc(o['fetched_at'][:16].replace('T',' '))+' UTC</p><a class="source" href="'+esc(o['source_url'])+'">Official source ↗</a></article>'
    def itemlist(rows): return {'@context':'https://schema.org','@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':base+link(o)} for i,o in enumerate(rows)]}
    def schemaoffer(o):
        s={'@type':'Offer','name':o['title'],'price':o['price'],'priceCurrency':o['currency'],'url':o['offer_url']}
        if o.get('valid_until'): s['priceValidUntil']=o['valid_until']
        return s
    def page(path,title,description,body,schema,lastmod=None):
        canonical=base+path
        kind='index' if path=='/' else 'provider' if path.startswith('/providers/') else 'deal' if path.startswith('/deals/') else 'compare'
        body=Template((ROOT/'templates'/ (kind+'.html')).read_text(encoding='utf-8')).substitute(content=body)
        breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':brand,'item':base+'/'},{'@type':'ListItem','position':2,'name':title,'item':canonical}]} if path!='/' else None
        graph=[schema]+([breadcrumb] if breadcrumb else [])
        values=dict(title=esc(title),description=esc(description),canonical=esc(canonical),base=esc(base),brand=esc(brand),body=body,disclosure=esc(cfg['disclosure']),jsonld=json.dumps(graph,ensure_ascii=False).replace('<','\\u003c'))
        rendered=Template((ROOT/'templates/layout.html').read_text(encoding='utf-8')).substitute(values)
        target=out/path.strip('/')/'index.html' if path!='/' else out/'index.html'; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(rendered,encoding='utf-8')
        sitemap.append((canonical,lastmod))
    provider_nav=''.join('<a class="pill" href="/providers/'+slug(p['name'])+'/">'+esc(p['name'])+'</a>' for p in cfg['providers'])
    content='<div class="eyebrow">INDEPENDENT • OFFICIAL SOURCES</div><h1>Find your next VPS.<br><span>Know the real price.</span></h1><p class="intro">Named plans, direct sources, transparent checks. Standard prices are labeled as plans. No invented coupons.</p><div class="stats"><strong>'+str(len(offers))+' verified plans</strong><span>'+str(len(providers))+' providers</span><span>Checked every 6 hours</span></div><nav class="filters">'+provider_nav+'<a class="pill" href="/compare/">Compare plans →</a></nav><h2>Latest verified plans</h2><div class="grid">'+''.join(card(o) for o in offers)+'</div>'
    if not offers: content+='<div class="empty"><h3>No verified prices available right now</h3><p>Our sources did not return an unambiguous current plan price. Visit a provider below for its official offers.</p></div>'
    content+='<h2>Source transparency</h2><div class="grid">'
    for p in cfg['providers']:
        c=checked.get(p['name'],{}); content+='<article><h3><a href="/providers/'+slug(p['name'])+'/">'+esc(p['name'])+'</a></h3><p>'+esc(c.get('status','not_checked').replace('_',' '))+'</p><p>Last attempt: '+esc(c.get('checked_at','Not yet checked'))+'</p><a href="'+esc(p['source'])+'">Official pricing ↗</a></article>'
    content+='</div>'
    latest=max((o['fetched_at'] for o in offers),default=None)
    page('/',brand+' — VPS plans and deals | '+month,'Compare '+', '.join(providers)+' official VPS plans in '+month+'. Only verified prices; no unverified discounts.',content,itemlist(offers),latest)
    for p in cfg['providers']:
        rows=[o for o in offers if o['provider']==p['name']]
        body='<div class="eyebrow">PROVIDER / OFFICIAL SOURCES</div><h1>'+esc(p['name'])+'</h1><p class="intro">Verified VPS plans for '+esc(month)+'. Prices and availability can change; confirm before purchase.</p><div class="grid">'+''.join(card(o) for o in rows)+'</div>'
        if not rows: body+='<div class="empty">No verified current prices available for this provider.</div>'
        body+='<p><a href="'+esc(p['source'])+'">Visit official pricing ↗</a></p>'
        schema={'@context':'https://schema.org','@type':'Service','name':p['name']+' VPS hosting','provider':{'@type':'Organization','name':p['name'],'url':p['home']}}
        if rows: schema['offers']=[schemaoffer(o) for o in rows]
        # Aggregate only comparable prices sharing currency AND billing period.
        if len(rows)>1 and len({(o['currency'],o['billing_period']) for o in rows})==1:
            schema['offers']={'@type':'AggregateOffer','lowPrice':min(float(o['price']) for o in rows),'highPrice':max(float(o['price']) for o in rows),'priceCurrency':rows[0]['currency'],'offerCount':len(rows),'offers':[schemaoffer(o) for o in rows]}
        page('/providers/'+slug(p['name'])+'/',p['name']+' VPS plans | '+month,p['name']+' official VPS pricing and source checks for '+month+'.',body,schema,max((o['fetched_at'] for o in rows),default=None))
    for o in offers:
        p=providers[o['provider']]; affiliate=bool(p['affiliate']); url=p['affiliate'] or o['offer_url']
        desc=o['provider']+' '+o['model']+': '+o['currency']+' '+o['price']+' ('+o['billing_period']+'), checked against the official source.'
        body='<div class="eyebrow">VERIFIED PLAN / '+esc(o['provider'])+'</div><h1>'+esc(o['title'])+'</h1><p class="price">'+esc(o['currency']+' '+o['price'])+' <small>/ '+esc(o['billing_period'])+'</small></p><p>'+esc(desc)+'</p><p>Verified '+esc(o['fetched_at'])+'</p><p>Taxes, renewal terms and regional eligibility: confirm with the provider.</p><a class="cta" href="'+esc(url)+'" rel="'+('sponsored noopener' if affiliate else 'noopener')+'">'+('Affiliate link · ' if affiliate else '')+'View official plan ↗</a><p><a href="'+esc(o['source_url'])+'">View price source</a></p>'
        schema=schemaoffer(o); schema['@context']='https://schema.org'
        page(link(o),o['title']+' — '+o['currency']+' '+o['price']+' | '+month,desc,body,schema,o['fetched_at'])
    rows=''.join('<tr><td><a href="'+link(o)+'">'+esc(o['title'])+'</a></td><td>'+esc(o['currency']+' '+o['price'])+'</td><td>'+esc(o['billing_period'])+'</td></tr>' for o in offers)
    page('/compare/','Compare VPS plans | '+month,'Compare official '+', '.join(providers)+' VPS prices by billing period and currency.','<h1>Compare verified plans</h1><p>Compare like-for-like currencies and billing periods. No inferred discounts.</p><div class="table"><table><thead><tr><th>Plan</th><th>Price</th><th>Billing period</th></tr></thead><tbody>'+rows+'</tbody></table></div>',itemlist(offers),latest)
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+esc(url)+'</loc>'+('<lastmod>'+esc(date)+'</lastmod>' if date else '')+'</url>' for url,date in sitemap)+'</urlset>'
    (out/'sitemap.xml').write_text(xml,encoding='utf-8'); (out/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+base+'/sitemap.xml\n',encoding='utf-8')
    shutil.copy(ROOT/'templates/style.css',out/'style.css'); shutil.copy(ROOT/'templates/favicon.svg',out/'favicon.svg')
    shutil.copy(ROOT/'templates/social.png',out/'social.png')
    (out/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Content-Security-Policy: default-src \'self\'; script-src \'none\'; style-src \'self\'; img-src \'self\' data:; base-uri \'none\'; frame-ancestors \'none\'\n',encoding='utf-8')
    print(json.dumps({'pages':len(sitemap),'deal_pages':len(offers),'base_url':base})); return len(offers)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--preview',action='store_true'); args=parser.parse_args(); build(preview=args.preview)
