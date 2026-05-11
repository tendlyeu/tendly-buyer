# Persona: Eve Jõesaar — Hankejuht (Procurement Manager)

## Organisation
**AS Hoolekandeteenused** — state-owned social welfare company (reg. 10399457), ~840 employees, 69 service units across Estonia, providing 24/7 care and community-based services to ~1800 adults with psychological special needs.

## Role & Background
- **Title**: Hankejuht (Procurement Manager)
- **Age**: ~45
- **Tech comfort**: Moderate — uses Excel daily, SharePoint for collaboration, Delta for document approval. Has tried CoPilot/GoPilot but found it unreliable for procurement work.
- **Languages**: Estonian (native), reads English technical documents with effort
- **Education**: Public administration or law background

## What She Procures
Services (real estate maintenance, repairs, logistics, construction, training, catering, workplace health), products (computers, printers, washing machines, hygiene supplies, small devices), software (real estate management systems, Microsoft licenses), and framework contracts. Thresholds start at €10,000 (internally stricter than required by law).

## Daily Work
Eve manages the annual procurement plan, coordinates across departments (real estate, HR, IT, catering, general management), and shepherds procurements through the full cycle: need identification → market survey → technical specification → board approval → document preparation → tender publication → evaluation → contract signing. She uses standard document templates (ITL IT procurement standard, marketing procurement standards) and maintains requirements lists in Excel. Documents start in SharePoint, then move to Delta for the formal approval cycle.

## Pain Points (from meeting notes)
1. **Technical specification writing is her #1 pain** — she is a procurement specialist, not a domain expert. When she needs to buy a car, a building, orthopedic supplies, or IT hardware, she Googles, researches, and guesses at specifications. This leads to ambiguous specs that bidders misinterpret, loopholes bidders exploit, legal challenges, and voided tenders.
2. **Price benchmarking is guesswork** — she has no way to know fair market prices. Historical tender data could help but isn't accessible in a usable format.
3. **Base document reuse is manual and slow** — adapting templates per tender (especially technical descriptions) takes too much time.
4. **CoPilot is a "black box"** — it doesn't pull data well from the state procurement register (Riigihangete Register), hallucinates after 3-4 sentences, and can't adapt templates for specific care services contexts.

## How She Would Use Tendly Buyer
- Search for **similar past tenders** to understand what others procured, what specs they used, what they paid
- Get AI-generated **draft technical descriptions** as a starting point, then refine
- Use the chat as a **"learning partner" (õpipartner)** — describe what she needs to procure and get guided through formulating proper documents, with laws and regulations built in
- **Price benchmarking** — find what similar procurements cost elsewhere to set realistic budgets
- **Contract review** — have AI check completed contracts for completeness and correctness

## Typical Queries She Would Type (in Estonian)
- "Näita mulle sarnaseid IT-riistvara hankeid viimase aasta jooksul"
- "Mis on keskmine hind koristusteenus hankele Tallinnas?"
- "Aita mul koostada tehniline kirjeldus pesumasinate ostmiseks hoolekandeasutustele"
- "Millised on levinumad vead kinnisvarahoolduse hangetes?"
- "Otsi hankeid CPV koodiga 50000000"
- "Kui palju maksis viimane sarnane IT-hanke Eestis?"

## Test Scenarios

### Scenario 1: New IT Hardware Procurement
Eve needs to procure 50 laptops for service unit staff across Estonia. She doesn't know current market prices, what specs to require, or what similar procurements looked like.
- **Goal**: Find similar past tenders, understand pricing, get a draft technical specification
- **Success criteria**: She gets usable comparable data and a starting point for her technical description within the chat
- **Failure indicators**: System returns irrelevant tenders, gives prices in wrong currency/context, or produces a generic spec not adapted to care services

### Scenario 2: Real Estate Maintenance Framework Contract
Eve needs to set up a 2-year framework contract for building maintenance across 12 service units in Harju county.
- **Goal**: Find similar framework contracts, understand typical pricing structures, identify common evaluation criteria
- **Success criteria**: Returns relevant Estonian real estate maintenance tenders, shows pricing ranges, suggests evaluation criteria
- **Failure indicators**: Returns construction tenders instead of maintenance, mixes up framework contracts with one-off purchases

### Scenario 3: Unfamiliar Domain — Catering Services
Eve has never procured catering services before. A department head says they need meal delivery for 200 residents.
- **Goal**: Use the chat as a learning partner — understand what to include in the technical description, what regulations apply, what pitfalls to avoid
- **Success criteria**: AI asks clarifying questions, references relevant regulations, suggests spec elements she wouldn't have thought of
- **Failure indicators**: AI just generates a generic document without understanding the specific context of care facility catering

### Scenario 4: Price Sanity Check
The board asks Eve if €4M for orthopedic supplies is reasonable. She has no idea.
- **Goal**: Find comparable procurements and their values to determine if the budget is realistic
- **Success criteria**: Shows historical data for similar procurements with clear value ranges
- **Failure indicators**: No relevant price data found, or data shown without sufficient context to compare

## Behaviour Patterns
- Types in Estonian, expects Estonian UI
- Starts with vague queries, refines as she sees results
- Wants to see the source data (which tender, which authority, what year) — doesn't trust "black box" answers
- Will bookmark useful tenders and come back to them
- Often works under time pressure — board meetings have fixed dates
- Frequently switches between Tendly, Excel, SharePoint, and Delta
