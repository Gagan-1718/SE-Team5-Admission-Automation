# Refinement log (after v1.0)

Every point raised while reviewing the running product, what it means, and what was done.
Status: Open, Decided, Fixed (with commit or PR), Won't change (with reason).

## Round 1 (5 November 2026)

| # | Point raised | Explanation | Decision / fix | Status |
|---|---|---|---|---|
| R1-1 | College names should be Karnataka colleges | The seed uses two invented colleges (Meridian, Cedarwood) in invented cities. They appear in 18 places in 10 test files. | Six real Karnataka colleges (RV, BMS, PES, M S Ramaiah, Siddaganga, NIE) with fictional seats; tests updated; README note | Fixed (ui/redesign) |
| R1-2 | Approved and rejected documents are blank pages | The demo generator writes an empty one-page PDF for every document. | Each candidate gets a drawn marksheet, ID card and category certificate with their own details and a SPECIMEN · FICTIONAL watermark; rejected ones are blurred to match the reason | Fixed (ui/redesign) |
| R1-3 | All candidate names look the same | The generator picks from 10 first and 10 last names and adds "Candidate 0001". | 50 first names × 40 surnames shuffled per seed, every candidate different, no suffix; guardians, schools and home cities also realistic | Fixed (ui/redesign) |
| R1-4 | Admin dashboard is too simple, no negative cases, no charts | It only shows candidate, application and document counts as tables. | Charts and figures for the whole cycle, including rejected documents, not eligible, unlocked choices, not allocated and rejected seats | Open |
| R1-5 | Newest uploaded documents should be on top | The review queue and dashboard queue sort oldest first. | Both queues list the newest upload first. Limitation: a resubmitted file keeps its original place because documents have no upload time stored | Fixed (ui/redesign) |
| R1-6 | Candidate buttons open the admin page | One browser holds one login. Logging in as admin in another tab turns every tab into the admin; candidate pages then refuse and offer the admin dashboard. Not a broken link. | Not a bug (one login per browser). The access-denied page now says who is signed in and suggests an incognito window for the second user | Fixed (ui/redesign) |
| R1-7 | The UI looks AI-generated and boring | Rounded pill buttons, gradients and soft shadows everywhere. | "Official portal" style (decided): white pages, navy header strip, square corners, dense tables, serif headings, thin saffron accent; no change to features or behaviour | Decided |
| R1-8 | Keep only what will be shown, remove the rest | Every menu item maps to an SRS requirement; a few extras do not. | Remove the long home-page journey list (replace with a short landing page) and the unused endpoints /accounts/dashboard and /accounts/admin-check (decided); everything in the menu stays because each item is an SRS requirement. Endpoints removed; home page is done with R1-7 | Partly fixed |
