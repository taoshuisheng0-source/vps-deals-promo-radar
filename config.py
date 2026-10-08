# ::ILANG [TYPE:code][PROJECT:vps-deals]
# ::STATE{@SELF, role:读取唯一I-Lang配置}
# ::BOUNDARY{never:硬编码厂商清单 静默接受坏配置}
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

def load(path=None):
    text = Path(path or ROOT / '.ilang/site.ilang').read_text(encoding='utf-8')
    if not text.startswith('::ILANG\n'):
        raise ValueError('Missing I-Lang header')
    state = re.search(r'::STATE\{@SITE, (.*?)\}', text).group(1)
    cfg = dict(re.findall(r'(\w+):([^,}]+)', state))
    cfg = {k: v.strip() for k, v in cfg.items()}
    cfg['providers'] = []
    section = text.split('::MODULE{PROVIDERS', 1)[1].split('\n', 1)[1].split('::MODULE', 1)[0]
    for line in section.splitlines():
        if not line.strip() or line.startswith('::'): continue
        parts = [s.strip() for s in line.split('|')]
        if len(parts) != 4: raise ValueError('Provider needs four pipe-separated fields')
        name, home, source, affiliate = parts
        for url in (home, source, affiliate):
            if url and (urlparse(url).scheme != 'https' or not urlparse(url).hostname):
                raise ValueError('HTTPS URLs required')
        cfg['providers'].append(dict(name=name, home=home, source=source, affiliate=affiliate))
    cfg['fields'] = text.split('::MODULE{FIELDS',1)[1].split('\n',1)[1].split('::MODULE',1)[0].splitlines()[0].split()
    cfg['disclosure'] = re.search(r'affiliate_disclosure: (.+)', text).group(1)
    if cfg['locale'] != 'en-US': raise ValueError('v1 supports en-US only; add region-specific sources and templates first')
    return cfg

def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
