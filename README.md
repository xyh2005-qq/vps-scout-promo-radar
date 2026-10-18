# VPS Scout

Official prices. Clear terms. Your next server.

An independent English-language VPS offer directory. The six official sources are RackNerd, RamNode, GreenCloud, CloudCone, ServaRica and VPSDime. Regular prices are explicitly separated from promotions. Brand is a working name, not a trademark clearance claim.

Live site: https://vpsscout.site/

Original preview URL: https://vps-scout-preview.pages.dev/ (redirects to the Git-integrated site).

Public repository: https://github.com/xyh2005-qq/vps-scout-promo-radar

**Status (2026-10-18):** public repository, six official sources, 97 plans and 107 sitemap entries. GitHub Actions refreshes every six hours and Cloudflare Pages deploys repository commits automatically. The complete refresh → commit → Git-triggered deployment chain passed a real manual run of the scheduled workflow: [run 39124180394](https://github.com/xyh2005-qq/vps-scout-promo-radar/actions/runs/39124180394). Future scheduled runs are best effort; this observation is not an uptime guarantee. No affiliate accounts or commissions are claimed.

## Design and quality

The second design iteration adds an interactive price–memory atlas, search and budget/memory lenses, shareable filter URLs, a three-plan comparison desk, responsive layouts and reduced-motion support. Read `QUALITY.md` for the review rounds, laboratory measurements and limitations. Fonts are served locally with their open-font licenses. Rendering, scraping and scheduled builds still use only Python’s standard library; browser interactions use a small local JavaScript file.

## Run

Python 3.9+; standard library only; no pip dependencies, scraping API keys or LLM calls.

```sh
python3 scraper.py
python3 -m unittest discover -s tests -v
python3 build.py
python3 verify.py
python3 -m http.server 8797 --directory site
```

`config.py`, `scraper.py` and `build.py` read `.ilang/site.ilang`. `PROVIDERS` determines what gets fetched and rendered; `ADAPTER` selects a supported parser and records source semantics. Removing a provider row changes both scraping and rendering. The regression suite verifies that removing GreenCloud prevents its source request and removes its cards, provider page, details and sitemap entries. `quality/config-change-proof.json` records a live, isolated rerun after removing that same row. Adding a new provider with a different HTML layout requires a tested adapter: changing a name is not sufficient to understand arbitrary websites.

The I-Lang parser supports `STATE`, provider rows, JSON-valued `CONFIG` and `ADAPTER` directives. Other rules document the project's boundaries; their important constraints are implemented and tested in Python. It is a project-defined text grammar, not an external I-Lang runtime. No configuration text is evaluated as executable code.

## Data integrity

Each offer records its official source URL, extraction timestamp, minimal plan evidence and source SHA-256. Price and specifications are extracted from the same plan block. Annual and quarterly charges retain their actual billing periods; monthly equivalents divide by 12 or 3 and are labeled calculations. CloudCone’s advertised monthly equivalent is not treated as a monthly bill. GreenCloud zero-stock rows and ServaRica sold-out/non-VPS rows are excluded; ServaRica USD and CAD spans are parsed separately. Published no-refund notes remain visible. RamNode Lite plans retain the IPv6-only restriction. No claimed percentage savings, renewal price, expiry or inventory is invented.

Robots are fetched with the declared VPSScoutBot user agent. An unavailable, denied or malformed robots file fails closed except a genuine 404/410. Source 403/429 responses are not bypassed. Redirected source URLs receive another robots check; crawl delays are honored. Failed parsers remove that provider from the fresh dataset rather than retaining old prices as current. A failed source is recorded in `data/offers.json`; the job exits with an error only after publishing that failure state.

Build excludes removed providers, expired offers and data older than 30 hours. Static pages cannot remove themselves if all future builds stop; their displayed check times must be consulted. No uptime or checkout availability testing is implied.

## Connected update pipeline

- Public GitHub repository: `xyh2005-qq/vps-scout-promo-radar`, branch `main`.
- Git-integrated Cloudflare Pages project: `vps-scout-radar`. Build command: `python3 build.py`; output: `site`.
- Schedule: `17 */6 * * *` UTC (01:17, 07:17, 13:17, 19:17 Asia/Shanghai). `build.py` derives `.github/workflows/update.yml` from I-Lang and `templates/update.yml`.
- A refresh runs parser/configuration tests, fetches public sources, builds and validates pages, and commits actual source data/status. Cloudflare's Git integration then builds and deploys that commit. GitHub supplies its automatic job token; no personal API key or paid inference is used by the runtime.
- A failed source is removed from current results. The workflow publishes that failure state before reporting failure. Follow the workflow run and the public `/status/` page.
- The original Direct Upload preview could not become a Git-integrated project, so the Git-connected project is the production destination. The original preview redirects there.
- GitHub cron is best effort. Public repositories may have scheduled workflows disabled after 60 days without activity. Do not manufacture repository activity for ranking.

`quality/pipeline-proof.json` records the successful refresh commit and the matching Cloudflare Git-triggered deployment.

Four scheduled builds per day are roughly 120–124 per month. Cloudflare's documented Free quota is currently 500 builds/month; extra commits also use it. GitHub standard hosted runners for public repositories are free under current published terms. No paid plan, card or custom domain is required for this preview; future platform policy changes are outside this project's control.

## Structured data and SEO

Pages include a self canonical, Open Graph, Twitter card, breadcrumb data, real timestamps and generated sitemap/robots. Lists use `ItemList`; VPS detail pages use `Service` with an `Offer`; provider pages use billing-cycle-separated `AggregateOffer`. Missing inventory/expiry fields are omitted. Schema.org validity does not guarantee Google rich-result eligibility; a VPS Service is not relabeled as a physical Product merely to force Product results. `verify.py` checks JSON syntax, links and metadata; it is not Google's Rich Results Test.

Domain age, commit counts and public GitHub links do not guarantee rankings or authority. A custom domain helps control branding, URLs and portability; buying it today does not buy search ranking. The owner registered vpsscout.site with Spaceship and configured Cloudflare nameservers. The canonical domain is controlled by .ilang/site.ilang; builds generate canonical URLs, structured-data URLs, robots.txt and sitemap.xml from that value. Configure Search Console after ownership is verified. Domain ownership and portability are distinct from search ranking.

Sitemap `lastmod` reflects the source check time displayed on each page, not a made-up publication date. This v1 is en-US only and does not claim that other locales are disjoint markets. Add actual local offers and translated editorial content before expanding, then add reciprocal hreflang and x-default.

## Monetization without invented earnings

Affiliate fields start blank. After approval under a provider's current official program, insert your own approved link in its provider row. Links become `rel="sponsored noopener noreferrer"` and a visible affiliate disclosure appears. Confirm permitted destination/deep-link behavior before using the field: a generic account-level referral URL may not lead to the exact plan. Do not infer an affiliate relationship from directory membership.

RackNerd's official program terms: https://www.racknerd.com/affiliates-terms-of-service

No RamNode program or payout is asserted. No recurring commission or managed-hosting product is assumed from these unmanaged VPS listings. Additional revenue options, once there is genuine demand, include separately labeled sponsorships and original paid comparison/reporting work. They are not enabled in v1. Keep verifiable costs, commissions, disclosures and transfer rights if later selling the site; no sale value is promised. X/Facebook posting is not configured or sent.

## Source coverage

| Provider | Official source | Current plans | Interpretation |
| --- | --- | ---: | --- |
| RackNerd | https://www.racknerd.com/specials/ | 5 | Annual specials |
| RamNode | https://ramnode.com/pricing/ | 23 | Published monthly/hourly rates |
| GreenCloud | https://greencloudvps.com/billing/store/premium-kvm-sale | 25 | Annual/quarterly specials; zero stock excluded |
| CloudCone | https://cloudcone.com/vps/ | 6 | Annual total, not headline monthly equivalent |
| ServaRica | https://servarica.com/browse/ | 27 | Annual VPS offers; excludes sold-out and non-VPS |
| VPSDime | https://vpsdime.com/linux-vps | 11 | Published monthly Linux VPS plans |

Counts describe the 2026-10-18 snapshot and can change on each scrape. Promotional and regular offers remain distinct. Crunchbits returned 403 and was not bypassed; CloudCone’s promotion-app robots response was unusable, so its accessible official VPS pricing page is used. GreenCloud’s budget sale was all sold out; its premium sale had available plan blocks.

## Verification record

Initial two-provider release: on 2026-10-18, the production preview host returned HTTP 200 for the homepage, comparison page, RackNerd detail page, dataset, sitemap and social card. Browser checks confirmed 28 cards, 5 specials, 23 regular plans, provider filters and ascending monthly-equivalent sorting. Desktop and 390px mobile layouts were inspected. Eight unit tests passed, including removal of a provider through I-Lang and conservative handling of unavailable robots. Local validation checked 34 pages.

Google Rich Results Test was attempted against the live RackNerd detail URL. Google returned “Something went wrong — Log in and try again”; no Google validation success is claimed. Repeat the test in an authenticated browser.

Wrangler 4.151.1 initially redirected project creation into Workers. A separate actual Pages project was then created with its explicit opt-out and deployed successfully. The accidentally created temporary Worker was removed. The Pages preview is the intended result. For future deployments use the existing Pages project; do not create a new Worker.

## Official operating references

- https://developers.cloudflare.com/pages/configuration/git-integration/
- https://developers.cloudflare.com/pages/get-started/direct-upload/
- https://developers.cloudflare.com/pages/platform/limits/
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow
- https://developers.google.com/search/docs/appearance/structured-data/sd-policies

站点规则用 I-Lang 协议描述，见 `.ilang/site.ilang`；协议说明：ilang.ai。
