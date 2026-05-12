# Tendly Buyer — Demo Notes
## Meeting with AS Hoolekandeteenused

**URL:** https://buyer.tendly.eu  
**Login:** kamelbelkadhi2@gmail.com  
**Language:** Set to Eesti (bottom-left corner)

---

## Demo Flow (15–20 min)

### 1. Welcome Screen (1 min)
- Open buyer.tendly.eu → show the Estonian welcome page
- Point out: "Tere, mina olen sinu AI hankespetsialist"
- Highlight the 4 quick-start cards: Loo uus hange, Koosta RFP, Hinda eelarvet, Leia pakkujad

### 2. Create a Procurement Plan (5 min)
- Type: **"Loo uus hange toitlustusteenuse ostmiseks hoolekandeasutusele, eeldatav maksumus 50000 eurot"**
- AI asks follow-up questions in Estonian — answer naturally:
  - Duration: "24 kuud"
  - Start: "jaanuar 2027"
  - Deadline: "30 päeva"
  - Criteria: "50% hind ja 50% kvaliteet"
  - Say: "Koosta hange kohe"
- **Show:** Right panel opens with plan summary (category, CPV code, value, criteria)
- **Show:** "Ava plaan" button → opens the procurement detail page

### 3. Generate a Document (5 min)
- Go back to chat, type: **"koosta tehniline kirjeldus"**
- Wait ~15 sec for AI to generate
- **Show:** AI response summarizes the document in Estonian
- **Show:** Right panel opens with full document preview — all in Estonian
- **Show:** Three action buttons at top:
  - "Kopeeri" — copies markdown to clipboard
  - "Lae alla .md" — downloads as markdown
  - **"Lae alla .docx"** — downloads as Word document
- Click "Lae alla .docx" to demonstrate the export

### 4. Search Existing Tenders (3 min)
- Open new chat, type: **"Otsi hoolekandeteenuste hanked Eestis"**
- **Show:** Matching tenders appear as compact list cards
- Click a tender → detail panel slides in from right with full info
- Mention: data comes from the real Estonian procurement registry

### 5. Procurement Dashboard (2 min)
- Click "Hanked" in sidebar → show the procurements list
- Click "Ülevaade" → show the dashboard overview
- Show "Dokumendid" → document management area

---

## Key Talking Points

- **AI understands Estonian** — all queries and responses in Estonian
- **RHS 2017 compliant** — follows Estonian procurement law
- **Full document generation** — technical specs, contracts, evaluation methodology, ESPD
- **Export to Word** — documents can be downloaded as .docx for editing
- **5-step workflow** — matches their actual process (need review → market research → plan review → budget approval → document prep)
- **Built for their team roles** — domain lead, procurement manager, board, specialist

## Known Limitations (don't demo these)

- Evaluation criteria names may appear in English in the plan panel (descriptions are Estonian)
- Document generation takes 10–20 seconds (Gemini API)
- Some older conversations in sidebar are test data

## If Something Breaks

- Refresh the page and try again
- If AI seems stuck (loading > 30 sec), start a new chat
- The system is in BETA — set expectations accordingly
