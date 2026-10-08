# VPS Deals

Independent, official-source VPS plan and promotion radar. Default niche: VPS hosting. Brand: VPS Deals. Locale: en-US. Seeds: RackNerd, Vultr, DigitalOcean. Regular pricing is labeled **plan**, never an invented discount.

Production URL: pending verification.

## Run

Python 3.12+, standard library only. `python scraper.py` checks robots.txt and fetches the configured official sources. `python build.py --preview` builds a local preview; production `python build.py` requires the confirmed `base_url` and `domain` in `.ilang/site.ilang`. Run `python -m unittest discover -s tests` for parser and configuration checks.

The I-Lang text configuration is actually parsed by both programs. Change a provider name or source there and both scraping and rendering change. Locale expansion requires real local sources and localized templates; v1 rejects unsupported locales.

## Data policy

Named plan, current price, currency, source URL, fetch timestamp and source hash are required. JSON-LD Product/Service Offers and a narrow RackNerd annual KVM card adapter are supported. Ambiguous, conflicting, expired and stale prices are excluded. A failed source loses its current prices immediately. A source without verified prices retains a transparent provider page. Crawl errors fail closed, including unavailable robots.txt. Source HTML evidence is attached to workflow runs for seven days. No paid API, scraping proxy, inference, invented coupon, fake expiry, or estimated commission.

This conservative v1 does not infer a discount from ordinary pricing. Sitemap/feed discovery alone is not proof of a price; new formats need a tested adapter. No FAQ section means no FAQ schema. Offer availability and expiry are omitted unless verified. Structured data does not guarantee a Google rich result.

## Automatic updates and deployment

GitHub Actions runs at 00:23, 06:23, 12:23 and 18:23 UTC (08:23, 14:23, 20:23 and 02:23 Asia/Shanghai), with manual dispatch available. The cron in the workflow must match `update_cron` in configuration; tests enforce this. Actions uses GitHub's automatically issued `GITHUB_TOKEN`, not a user API key. No runtime inference or external API secret.

Connect **Cloudflare Pages Git integration** to this public repo, production branch `main`, build command `python build.py`, output `site`. Initially provision the Pages project, then write its actual production hostname to `domain` and HTTPS origin to `base_url`; do not guess a suffix. Retry the build after updating the config. Each data commit should trigger Pages Git deployment; verify an actual scheduled-data commit deploys, not just a manual code commit.

GitHub schedules may be delayed or disabled after inactivity; provider markup and platform terms can change. Monitor failed runs and missing observations. This is unattended automation, not a promise of perpetual operation. Free tiers have limits; no paid plan is required for this implementation.

## Monetization

No affiliate enrollment or commission is claimed. Approved provider-specific affiliate URLs can be added in the fourth provider column after reviewing the applicable public terms. Links are then marked as affiliate and `rel=sponsored`, with visible disclosure. Do not invent enrollment, cookie attribution, income or recurring rates. Future sponsored placements must be labeled; a future sale requires verifiable domain ownership, operating history and income records. X/Facebook posting is deliberately deferred.

An owned domain can improve brand continuity and transferability, but domain age, commits and repository links do not guarantee rankings. Keep a consistent domain, useful comparisons, real sources and policy compliance. No purchase is required for launch.

站点规则用 I-Lang 协议描述，见 .ilang/site.ilang，协议说明 ilang.ai。
