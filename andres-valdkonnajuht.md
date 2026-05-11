# Persona: Andres Tamm — Valdkonna juht (Field/Domain Manager)

## Organisation
**AS Hoolekandeteenused** — state-owned social welfare company, ~840 employees, 69 service units across Estonia.

## Role & Background
- **Title**: Kinnisvara valdkonna juht (Real Estate Domain Manager)
- **Age**: ~52
- **Tech comfort**: Low — uses email, basic Excel, occasionally Word. Calls the procurement manager for most questions. Has never used an AI chat tool purposefully.
- **Languages**: Estonian only
- **Education**: Technical/vocational background in facilities management

## What He Does
Andres manages real estate and facilities for a cluster of service units. When something needs to be procured — building repairs, new furniture, cleaning services, fire safety equipment — the need starts with him. He's supposed to conduct market surveys, write technical descriptions, and prepare materials for the board. In practice, he knows what's needed but struggles to turn operational knowledge into formal procurement documents.

## Daily Work
Most of his day is spent managing facilities, responding to maintenance requests, coordinating with contractors. Procurement work is something he does "on top of" his main job, usually under deadline pressure when the board meeting is approaching. He writes specs in Word, tracks things in his own Excel sheet, and emails everything to Eve (the procurement manager) for review.

## Pain Points
1. **Doesn't know how to write technical specifications** — he knows he needs "roof repair for 3 buildings" but doesn't know the CPV codes, the correct legal phrasing, or what requirements to set
2. **Market surveys feel like busywork** — he's supposed to check what similar things cost but doesn't know where to look beyond calling a few contractors he already knows
3. **Afraid of getting it wrong** — a badly written spec can lead to legal challenges, voided tenders, or buying the wrong thing. He's been burned before.
4. **Doesn't understand procurement law** — relies on Eve for all legal questions, which creates bottlenecks
5. **No time** — procurement prep competes with his actual job of managing facilities

## How He Would Use Tendly Buyer
- As a **"digital colleague"** he can ask basic questions to ("Kuidas ma pean selle hanke kirjelduse tegema?")
- To **find examples** of how others have procured similar things ("Näita mulle kuidas teised on koristusteenus hanke teinud")
- To **generate a first draft** that he can then send to Eve for refinement
- To understand **what CPV codes** to use
- As a substitute for calling Eve with every small question

## Typical Queries (in Estonian, often vague/conversational)
- "Mul on vaja osta 3 pesumasinat, kuidas ma hanke teen?"
- "Kas keegi on varem katuse remondi hanget teinud?"
- "Mis see CPV kood on?"
- "Palju koristus maksab?"
- "Aita mind"
- "Meil on vaja uut köögi seadmeid Pärnu kodule"

## Test Scenarios

### Scenario 1: First-Time AI User — Simple Product Purchase
Andres needs to buy 10 washing machines for service units. He's never used the Tendly Buyer portal before.
- **Goal**: Figure out how to use the system, find relevant information, get started on a procurement document
- **Expected behaviour**: Vague first query, probably types something like "pesumasinad" or "mul on vaja pesumasinaid". May not understand suggestions. Needs the system to guide him step-by-step.
- **Success criteria**: System asks clarifying questions, guides him to relevant past tenders, helps him understand what a technical description should contain
- **Failure indicators**: System dumps a wall of text, uses procurement jargon he doesn't understand, or shows English-language results

### Scenario 2: Market Survey for Building Repair
Andres needs to show the board that he's done a market survey for facade renovation on a care home.
- **Goal**: Find comparable tenders and their prices to include in his board presentation
- **Expected behaviour**: Searches in Estonian, expects to see Estonian tenders. May not know the correct CPV code. Might type "maja remont" instead of "fassaadi renoveerimine".
- **Success criteria**: System handles his vague query, suggests relevant CPV codes, shows comparable tenders with prices
- **Failure indicators**: Returns results from Latvia/Lithuania that he can't use, or gives prices without source attribution

### Scenario 3: Urgent Kitchen Equipment
A kitchen in the Pärnu service unit broke down. Andres needs to procure new commercial kitchen equipment urgently. The board meets in 3 days.
- **Goal**: Quickly get a draft technical description and price estimate he can present to the board
- **Expected behaviour**: Rushed, incomplete queries. May type "köögiseadmed Pärnu KIIRE". Expects immediate, actionable output.
- **Success criteria**: System provides a usable draft within 2-3 exchanges, includes realistic price range
- **Failure indicators**: System asks too many clarifying questions when time is short, or produces a draft that would take hours to adapt

## Behaviour Patterns
- Types only in Estonian, often with typos and informal language
- Gets frustrated if the interface is complex or requires multiple clicks
- Doesn't read long responses — skips to the actionable part
- Will give up after 2-3 failed attempts and call Eve instead
- Needs hand-holding — the system should proactively suggest next steps
- Doesn't know what he doesn't know — won't ask about regulations unless prompted
