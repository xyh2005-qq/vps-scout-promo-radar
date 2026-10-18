# VPS Scout — design and quality review

Reviewed 2026-10-18. Live site: https://vps-scout-radar.pages.dev/

The design target is the level of craft associated with Awwwards, The Webby Awards and FWA. This is a self-review, not an award, nomination, jury score or guarantee of recognition. Automated scores measure a limited set of technical checks; they do not certify creative quality.

## Design concept

An independent VPS field guide: editorial typography, a white/navy palette with orange purchase actions, an original directional mark, and a real-data price–memory atlas. The interaction is connected to the buying decision rather than being a decorative simulation. All font files are self-hosted, with their open-font licenses included.

## Review rounds

1. Replaced the generic hero and equal-weight catalog with an editorial identity, an interactive price–memory atlas, explicit offer types and a focused shortlist. Added text search, budget/memory lenses, pagination and a three-plan comparison desk.
2. Increased small text, aligned chart ticks with its logarithmic coordinates, added chart previous/next controls and roving keyboard focus, improved touch layouts, added a swipe cue to mobile comparisons and applied the same visual system to detail, provider, comparison and 404 pages. Source timestamps now use a readable UTC format. No-JavaScript visitors retain the full catalog and ordinary source links.
3. Tested real browser interactions, responsive widths, reduced-motion preference, accessibility and online performance. Fixed low-contrast source numbers and the detail-page status label discovered by Lighthouse. Updated the social preview artwork to match the site.

4. Replaced the green palette at the user’s request with white, navy and orange. Orange is reserved for primary actions, special-offer accents and key headline emphasis. Updated cards, purchase panels, chart, comparison controls, favicon, browser theme and social artwork. Rechecked desktop and mobile views; homepage and detail mobile Lighthouse audits both scored 100 in accessibility, best practices and SEO with zero failures. This visual hierarchy is a design choice, not a measured conversion uplift. Existing tests and generated-page checks pass.

5. Expanded to six providers (97 plans / 107 sitemap pages). Added conservative adapters, stock exclusion, explicit quarterly billing and separate USD extraction. Atlas axes now fit the real data range. Sixteen tests pass. A live rerun removing only the GreenCloud provider row fetched five sources and built 72 plans / 81 pages, removing all GreenCloud pages and sitemap entries; see `quality/config-change-proof.json`. Homepage mobile Lighthouse remains 100/100/100 with no failed audits. Prior performance measurements below belong to the earlier two-provider release.

## Measured checks

| Check | Observed result |
| --- | --- |
| Live homepage Lighthouse, mobile mode | Accessibility 100; Best Practices 100; SEO 100; 0 failed audits |
| Live updated detail page Lighthouse, mobile mode | Accessibility 100; Best Practices 100; SEO 100; 0 failed audits |
| Live homepage cold-load performance trace | LCP 655 ms; CLS 0.00 |
| Performance test conditions | Chrome, 390 × 844 viewport, Fast 4G emulation, CPU 4× slowdown, cache bypass |
| Field / real-user performance data | Not available; laboratory results are not a real-user percentile |
| Responsive layout inspection | 320, 390, 768, 1024 and 1440px; no document-level horizontal overflow observed |
| Source integrity / configuration tests | 10 tests passing |
| Generated-page validation | 34 pages; valid JSON-LD syntax, canonical and local-link checks |
| JavaScript syntax / browser console | Syntax check passed; no application errors observed |

## Interaction checks

- The atlas contains 28 points from the 28 current source-backed plans; arrow keys change the active plan and move focus. The map shows actual quoted price/billing alongside the calculated monthly equivalent. It claims no performance benchmark.
- Budget lens uses the displayed rounded monthly equivalent, so a displayed $5.00 plan is not included in “Under $5”. Provider filtering and a reload of the resulting shareable URL preserved the same four matching RamNode plans.
- Search with no matches shows an explicit empty state and a working reset. The shortlist starts with nine visible plans; more plans can be revealed without navigation. All plans remain in server-rendered HTML.
- Selecting three plans prevents adding a fourth. Removing and clearing selections updates buttons, the comparison desk and the URL. The full price-index table also supports selection.
- The modal opens from a deliberate action. Escape closes it, removes the page scroll lock and returns focus to its trigger. Mobile comparison columns scroll inside the modal with a visible instruction; the document itself does not overflow.
- With reduced motion enabled, the hero has no animation. Below-fold reveals also honor that preference.
- Annual prices remain annual in cards, detail pages, map data and comparisons. IPv6-only restrictions remain visible. JSON embedded in HTML escapes source text that could otherwise terminate the script element.

## Remaining external limits

The public GitHub repository is https://github.com/xyh2005-qq/vps-scout-promo-radar. The six-hour refresh and Cloudflare Git deployment are connected; run 39124180394 completed successfully and its resulting commit triggered a successful Cloudflare deployment. See `quality/pipeline-proof.json`. Google Rich Results Test previously required account login and has not been marked passed. Affiliate fields remain empty. No registrations, awards submissions, paid services, social messages or claims of recognition were created by this work.

The catalog now covers six official providers with 97 plans in the 2026-10-18 source snapshot; independent user testing remains useful. Automated audit results do not establish market demand or search ranking.

Reference for the published content, navigation, visual design, functionality, interactivity, innovation and experience criteria: https://www.webbyawards.com/judging-criteria/

Machine-readable audit summary: `quality/audit-results.json`. Verified release: https://043a2692.vps-scout-preview.pages.dev
