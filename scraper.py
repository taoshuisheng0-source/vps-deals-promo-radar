# ::ILANG [TYPE:code][PROJECT:vps-deals]
# ::STATE{@SELF, role:robots许可后读取官方报价}
# ::BOUNDARY{never:推测价格 绕反爬 沿用失败来源旧报价}
import json, re, time, hashlib
from datetime import datetime, timezone
from html.parser import HTMLParser
from html import unescape
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from config import ROOT, load, slug

AGENT = 'VPSDealsBot/1.0'
MAX_BYTES = 4_000_000

def download(url):
    req = Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,application/json,text/plain'})
    with urlopen(req, timeout=25) as response:
        if urlparse(response.url).hostname != urlparse(url).hostname:
            raise ValueError('Cross-host redirect requires source review')
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES: raise ValueError('Source exceeds size cap')
        return data.decode('utf-8', errors='replace')

def permitted(url):
    origin = '{0.scheme}://{0.netloc}'.format(urlparse(url))
    robot_url = origin + '/robots.txt'
    # Fail closed on errors, including missing robots: review source before enabling.
    robots = RobotFileParser(robot_url)
    robots.parse(download(robot_url).splitlines())
    if not robots.can_fetch(AGENT, url): raise ValueError('robots.txt disallows this source')
    delay = robots.crawl_delay(AGENT) or robots.crawl_delay('*') or 1
    time.sleep(min(max(delay, 1), 60))
    if delay > 60: raise ValueError('Crawl delay exceeds run budget')

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.scripts=[]; self.current=None; self.text=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='script' and attrs.get('type')=='application/ld+json': self.current=[]
        if tag in ('script','style','del','s'): self.hidden += 1
        if tag in ('div','p','h1','h2','h3','h4','li','br','td','tr'): self.text.append('\n')
    def handle_endtag(self,tag):
        if tag=='script' and self.current is not None:
            self.scripts.append(''.join(self.current)); self.current=None
        if tag in ('script','style','del','s'): self.hidden=max(0,self.hidden-1)
        if tag in ('div','p','h1','h2','h3','h4','li','td','tr'): self.text.append('\n')
    def handle_data(self,data):
        if self.current is not None: self.current.append(data)
        if not self.hidden: self.text.append(data)

def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values(): yield from walk(child)
    elif isinstance(value,list):
        for child in value: yield from walk(child)

def extract(html, provider):
    page=Page(); page.feed(html); found=[]
    for script in page.scripts:
        try: nodes=walk(json.loads(script))
        except (ValueError,TypeError): continue
        for node in nodes:
            if node.get('@type') not in ('Product','Service'): continue
            name=node.get('name','')
            if not isinstance(name,str) or not 2 <= len(name) <= 80: continue
            # Named VPS plans only, not broad product marketing headings.
            if not re.search(r'\d|KVM|CX\w+|CPX\w+',name,re.I): continue
            offers=node.get('offers',[])
            if isinstance(offers,dict): offers=[offers]
            for offer in offers:
                if not isinstance(offer,dict) or offer.get('@type')!='Offer': continue
                if offer.get('availability') not in (None,'https://schema.org/InStock','http://schema.org/InStock'): continue
                price=str(offer.get('price',''))
                currency=offer.get('priceCurrency','')
                if not re.fullmatch(r'\d+(?:\.\d{1,2})?',price) or float(price)<=0 or not re.fullmatch(r'[A-Z]{3}',currency): continue
                url=urljoin(provider['source'],offer.get('url') or provider['source'])
                if urlparse(url).scheme!='https' or urlparse(url).hostname != urlparse(provider['source']).hostname: continue
                row=dict(model=name,price=price,currency=currency,offer_url=url,kind='plan',billing_period='See official terms')
                if offer.get('priceValidUntil'): row['valid_until']=offer['priceValidUntil']
                found.append(row)
    # A narrow, explicit adapter for RackNerd's official annual KVM cards.
    if urlparse(provider['source']).hostname == 'www.racknerd.com' and '/BlackFriday/' in provider['source']:
        for card in re.findall(r'<article\b[^>]*class="sn-plan[^\"]*"[^>]*>(.*?)</article>',html,re.S):
            heading=re.search(r'<h3>([^<]+)</h3>',card)
            priceblock=re.search(r'<p class="sn-price">(.*?)</p>',card,re.S)
            if not heading or not priceblock: continue
            model=unescape(heading[1]).strip()
            if not re.fullmatch(r'\d+(?:\.\d+)?\s*(?:GB|MB)\s+KVM\s+VPS',model,re.I): continue
            # Current price is isolated inside the explicit price node of this card.
            pricepage=Page(); pricepage.feed(priceblock[1]); text=''.join(pricepage.text)
            match=re.fullmatch(r'\s*\$\s*(\d+\.\d{2})\s*/year\s*',text)
            order=re.search(r'href="(https://my\.racknerd\.com/cart\.php\?[^\"]+)"',card)
            if match and order:
                found.append(dict(model=model,price=match[1],currency='USD',offer_url=unescape(order[1]),kind='plan',billing_period='year'))
    return found

def run():
    cfg=load(); now=datetime.now(timezone.utc).isoformat(timespec='seconds'); offers=[]; checks=[]
    for provider in cfg['providers']:
        check={'provider':provider['name'],'source_url':provider['source'],'checked_at':now}
        try:
            permitted(provider['source']); html=download(provider['source'])
            digest=hashlib.sha256(html.encode()).hexdigest()
            evidence=ROOT/'data/evidence'; evidence.mkdir(parents=True,exist_ok=True)
            (evidence/(slug(provider['name'])+'.html')).write_text(html,encoding='utf-8')
            rows=extract(html,provider); check.update(status='verified' if rows else 'no_verified_prices',source_sha256=digest)
            for row in rows:
                if row.get('valid_until'):
                    try:
                        until=datetime.fromisoformat(row['valid_until'].replace('Z','+00:00'))
                        if len(row['valid_until'])==10: until=until.replace(hour=23,minute=59,second=59)
                        if until.replace(tzinfo=until.tzinfo or timezone.utc) < datetime.now(timezone.utc): continue
                    except ValueError: continue
                row.update(provider=provider['name'],title=provider['name']+' '+row['model'],source_url=provider['source'],fetched_at=now,source_sha256=digest)
                row['id']=slug(provider['name']+' '+row['model']+' '+row['currency'])
                offers.append(row)
        except Exception as error:
            check.update(status='unavailable',error=str(error)[:240])
        checks.append(check)
    unique={}
    conflicts=set()
    for offer in offers:
        key=(offer['provider'],offer['model'],offer['currency'])
        if key in unique and (unique[key]['price'],unique[key]['billing_period']) != (offer['price'],offer['billing_period']): conflicts.add(key)
        unique[key]=offer
    offers=[v for k,v in unique.items() if k not in conflicts]
    target=ROOT/'data'; target.mkdir(exist_ok=True)
    (target/'offers.json').write_text(json.dumps({'offers':offers,'checks':checks},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verified_plans':len(offers),'checks':checks}))

if __name__=='__main__': run()
