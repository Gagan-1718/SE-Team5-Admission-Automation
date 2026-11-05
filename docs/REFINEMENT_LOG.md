# Refinement log (after v1.0)

Every point raised while reviewing the running product, what it means, and what was done.
Status: Open, Decided, Fixed (with commit or PR), Won't change (with reason).

## Round 1 (5 November 2026)

| # | Point raised | Explanation | Decision / fix | Status |
|---|---|---|---|---|
| R1-1 | College names should be Karnataka colleges | The seed uses two invented colleges (Meridian, Cedarwood) in invented cities. They appear in 18 places in 10 test files. | Six real Karnataka colleges (RV, BMS, PES, M S Ramaiah, Siddaganga, NIE) with fictional seats; tests updated; README note | Fixed (ui/redesign) |
| R1-2 | Approved and rejected documents are blank pages | The demo generator writes an empty one-page PDF for every document. | Each candidate gets a drawn marksheet, ID card and category certificate with their own details and a SPECIMEN · FICTIONAL watermark; rejected ones are blurred to match the reason | Fixed (ui/redesign) |
| R1-3 | All candidate names look the same | The generator picks from 10 first and 10 last names and adds "Candidate 0001". | 50 first names × 40 surnames shuffled per seed, every candidate different, no suffix; guardians, schools and home cities also realistic | Fixed (ui/redesign) |
| R1-4 | Admin dashboard is too simple, no negative cases, no charts | It only shows candidate, application and document counts as tables. | New dashboard: headline figures, needs-attention list with links, admission funnel, segmented bars for applications, documents, eligibility, choices, allotment outcome and seat decisions, seats by college. Segmented bars instead of pies because close slices are hard to compare | Fixed (ui/redesign) |
| R1-5 | Newest uploaded documents should be on top | The review queue and dashboard queue sort oldest first. | Both queues list the newest upload first. Limitation: a resubmitted file keeps its original place because documents have no upload time stored | Fixed (ui/redesign) |
| R1-6 | Candidate buttons open the admin page | One browser holds one login. Logging in as admin in another tab turns every tab into the admin; candidate pages then refuse and offer the admin dashboard. Not a broken link. | Not a bug (one login per browser). The access-denied page now says who is signed in and suggests an incognito window for the second user | Fixed (ui/redesign) |
| R1-7 | The UI looks AI-generated and boring | Rounded pill buttons, gradients and soft shadows everywhere. | Official portal style across every page: navy header strip with saffron rule, horizontal menu, footer, square corners, serif headings, rectangular status tags, navy table headers; features unchanged | Fixed (ui/redesign) |
| R1-8 | Keep only what will be shown, remove the rest | Every menu item maps to an SRS requirement; a few extras do not. | Endpoints /accounts/dashboard and /accounts/admin-check removed (their 401/403 tests now use real routes); long home-page journey list replaced by a short landing page | Fixed (ui/redesign) |

## Round 2 (5 November 2026)

| # | Point raised | Explanation | Decision / fix | Status |
|---|---|---|---|---|
| R2-1 | The home (hero) page needs work | The short landing page is one panel; it does not feel like a real portal home. | Portal home: full-width navy hero with register and log-in buttons, counselling-at-a-glance box, six-step how-it-works strip, candidate and administrator sections, participating colleges read from the catalogue | Fixed (ui/redesign) |
| R2-2 | The font is bad for this kind of website | Serif (Georgia) headings feel like a newspaper, not an admission portal. | Serif removed; one sans-serif family (Segoe UI on Windows, system font elsewhere) for headings and text, no download needed | Fixed (ui/redesign) |
| R2-3 | The left sidebar looked better than the top bar | The portal top menu replaced the earlier sidebar. | Left sidebar back in the portal colours (navy, square, saffron edge and active marker, icons, user block); slide-out menu on phones; public pages keep the top header | Fixed (ui/redesign) |
