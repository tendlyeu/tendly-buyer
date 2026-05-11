# Persona: Marika Lepp — Valdkonna spetsialist (Domain Specialist, IT)

## Organisation
**AS Hoolekandeteenused** — state-owned social welfare company, ~840 employees, 69 service units across Estonia.

## Role & Background
- **Title**: IT-spetsialist / valdkonna spetsialist (IT Domain Specialist)
- **Age**: ~35
- **Tech comfort**: High — manages IT infrastructure across service units, comfortable with technical specifications, uses multiple software tools daily. Has used ChatGPT for personal tasks.
- **Languages**: Estonian (native), English (good — reads technical docs, vendor communications)
- **Education**: IT / Computer Science

## What She Does in Procurement
When IT equipment or software needs to be procured, Marika writes the actual technical specifications: laptop specs, network requirements, software feature lists, server capacity. She's the domain expert Eve (procurement manager) relies on to define what exactly should be purchased. She also evaluates bids — she can tell if a vendor's proposed laptop actually meets the requirements or if they're cutting corners.

## Her Connection to RIT
Hoolekandeteenused is connected to RIT (Riigi Infosüsteemi Amet / state IT centre) systems. Some IT comes through RIT's workplace services (töökohateenus), some is procured independently. Microsoft licenses come from the state. Marika navigates this dual-track system daily.

## Pain Points
1. **Writing specs for non-IT colleagues to understand** — she knows the technical requirements but struggles to write them in procurement-compatible language that passes legal review
2. **Vendor lock-in / licensing complexity** — Microsoft licensing is a "headache". Prices on the website differ from what sellers offer in Estonia. She needs to understand what's already covered by state agreements vs what needs to be separately procured.
3. **Keeping specs neutral** — procurement law requires she can't write specs that favour one vendor. But when you need specific software compatibility, writing truly neutral specs is hard.
4. **Evaluating bids takes forever** — comparing 5-6 competing offers against 40+ technical requirements, manually checking each line

## How She Would Use Tendly Buyer
- **Generate technical specifications** from a description of needs — "I need laptops for field workers who travel, need to be rugged, run Windows, battery life 8+ hours" → structured procurement spec
- **Check if her spec is vendor-neutral** — AI reviews and flags requirements that might be seen as discriminatory
- **Find similar IT tenders** to see how others structured their requirements
- **Competitive analysis** — which vendors typically bid on similar tenders, what are typical prices for this type of IT equipment
- **Software procurement catalogue** — track what's already purchased across the organisation (they currently use Excel for this)

## Typical Queries (mix of Estonian and technical English terms)
- "Koosta tehniline kirjeldus 50 sülearvuti ostmiseks, nõuded: Windows 11 Pro, 16GB RAM, 512GB SSD, 14-tolline ekraan"
- "Kas see tehniline kirjeldus on piisavalt neutraalne? [pastes spec]"
- "Näita sarnaseid IT-riistvara hankeid riigisektoris"
- "Millised firmad on varem võitnud sülearvuti hankeid Eestis?"
- "Mis on tüüpiline hind enterprise sülearvutile riigihangetes?"
- "Kuidas kirjutada tehniline kirjeldus serverite jaoks ilma et see oleks Delli spetsiifiline?"

## Test Scenarios

### Scenario 1: Generate Laptop Procurement Spec
Marika needs to write a technical specification for 50 laptops for care staff who visit clients at home.
- **Goal**: Get a structured, procurement-ready technical specification with all required fields
- **Expected behaviour**: Starts with a fairly detailed technical query, expects the AI to know procurement document structure. Will iterate — add requirements, adjust specs, check neutrality.
- **Success criteria**: Output follows Estonian procurement spec format, includes CPV codes, is vendor-neutral, covers key technical and warranty requirements
- **Failure indicators**: Generic consumer laptop comparison, missing procurement-specific structure (evaluation criteria, delivery terms, warranty requirements), or specs that clearly describe one vendor's product line

### Scenario 2: Vendor Neutrality Check
Marika wrote a spec that requires "Intel Core i7 or equivalent". She wants to verify this is acceptable and not overly restrictive.
- **Goal**: AI reviews the specification for neutrality and suggests improvements
- **Expected behaviour**: Pastes her spec (or key parts) and asks for review. Expects specific, actionable feedback.
- **Success criteria**: AI identifies potentially restrictive requirements, suggests neutral alternatives (e.g., "processor with PassMark score ≥ 15000" instead of naming Intel), references procurement law
- **Failure indicators**: AI just says "looks fine" without analysis, or flags everything as restrictive (over-cautious)

### Scenario 3: Software Licence Procurement Research
Marika needs to procure additional Microsoft 365 licences beyond what RIT provides. She wants to understand the procurement landscape.
- **Goal**: Find how other state organisations procure Microsoft licences, what frameworks exist, typical pricing
- **Expected behaviour**: Technical query mixing procurement and IT terminology
- **Success criteria**: Shows relevant IT licence tenders, distinguishes between state-level agreements and individual procurements, provides pricing context
- **Failure indicators**: Confuses RIT-provided licences with independently procured ones, or gives consumer pricing instead of procurement pricing

### Scenario 4: Bid Evaluation Support
Marika received 4 bids for a server procurement. She needs to evaluate them against the technical specification.
- **Goal**: Structured comparison of bids against requirements
- **Expected behaviour**: Wants to upload or describe the bids and get a comparison matrix
- **Success criteria**: Clear requirement-by-requirement comparison, flags where bids don't meet specs, highlights significant differences
- **Failure indicators**: Can't handle structured comparison, gives vague "all bids look similar" response

## Behaviour Patterns
- Technically precise in her queries — uses model numbers, specific measurements, technical standards
- Expects the AI to understand IT terminology without explanation
- Will test the AI's knowledge — if it gives wrong technical info, she loses trust immediately
- Uses the system intensively during procurement preparation (2-3 weeks), then not at all for months
- Comfortable switching between Estonian and English technical terms in the same query
- Will copy-paste output directly into procurement documents, so formatting matters
