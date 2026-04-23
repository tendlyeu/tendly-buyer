# Tendly Buyer AI Tools — User Stories & Stakeholder Questionnaire

> **Purpose:** This document defines user stories and validation questions for extending the Tendly Agent Chat platform with buyer-side AI tools. Buyers (procurement officers, contracting authorities) will use these tools to draft RFPs, benchmark prices, and prepare procurement documents — all through the chat interface with canvas artifact display.
>
> **How to use:** Review each section, rate user stories using the MoSCoW priority scale, and answer the questionnaire questions to validate requirements.

---

## 1. User Personas

| ID | Persona | Description |
|----|---------|-------------|
| B1 | Procurement Officer | Day-to-day buyer who drafts tenders, manages procurement processes, and evaluates bids. Primary user of RFP drafting and price benchmarking tools. |
| B2 | Procurement Manager | Senior buyer who oversees procurement strategy, approves RFPs, and ensures compliance with procurement regulations (EU directives, national law). |
| B3 | Budget Owner / Department Head | Internal stakeholder who defines requirements, sets budgets, and approves procurement plans. Needs market intelligence for budget planning. |
| B4 | Legal / Compliance Officer | Reviews procurement documents for legal compliance, checks evaluation criteria fairness, and ensures adherence to public procurement regulations. |
| B5 | Finance Controller | Validates cost estimates, checks budget allocations, monitors contract spending, and ensures financial compliance. |
| B6 | Technical Specialist | Subject-matter expert who defines technical requirements, specifications, and evaluation criteria for specialized procurements (IT, construction, medical). |

### Questionnaire: Personas

- **Q1.1** Which of these personas exist in your organization? Are there additional roles involved in procurement?
- **Q1.2** Who typically initiates a new procurement process — the budget owner (B3) or the procurement officer (B1)?
- **Q1.3** How many people are typically involved in drafting a single RFP?
- **Q1.4** Do you currently use any AI or digital tools for procurement drafting? If so, which ones?

---

## 2. RFP Drafting with AI

| ID | User Story | Persona |
|----|-----------|---------|
| US-01 | As a Procurement Officer, I want to describe my procurement need in natural language so that the AI generates a structured RFP draft based on best practices and regulatory requirements. | B1 |
| US-02 | As a Procurement Officer, I want the AI to suggest appropriate evaluation criteria and weights based on the type of procurement (services, supplies, works) so that I create fair and effective criteria. | B1 |
| US-03 | As a Procurement Manager, I want to select from RFP templates (open procedure, restricted procedure, negotiated procedure) so that the generated RFP follows the correct procurement process. | B2 |
| US-04 | As a Procurement Officer, I want the AI to generate appropriate CPV codes from my requirement description so that the tender is correctly classified and reaches the right suppliers. | B1 |
| US-05 | As a Procurement Officer, I want the AI to draft qualification requirements (experience, financial standing, technical capability) based on the estimated contract value and type so that requirements are proportionate and non-discriminatory. | B1 |
| US-06 | As a Legal Officer, I want the AI to flag potential compliance issues in the draft RFP (discriminatory requirements, missing mandatory clauses, incorrect thresholds) so that I can fix them before publication. | B4 |
| US-07 | As a Procurement Officer, I want to iterate on the RFP in chat — asking the AI to modify sections, add clauses, or rephrase requirements — so that I refine the document conversationally. | B1 |
| US-08 | As a Budget Owner, I want to provide high-level needs ("we need office renovation for 200 people") and have the AI expand them into detailed technical specifications so that I don't need procurement expertise to start the process. | B3 |
| US-09 | As a Procurement Officer, I want to export the finalized RFP as a downloadable document (DOCX/PDF) from the canvas panel so that I can upload it to the procurement portal. | B1 |
| US-10 | As a Procurement Manager, I want the AI to generate a procurement timeline (notice period, submission deadline, evaluation period, contract signing) based on the procedure type and EU thresholds so that I set realistic deadlines. | B2 |

### Questionnaire: RFP Drafting

- **Q2.1** What is your current process for drafting an RFP? How long does it typically take from requirements to publication?
- **Q2.2** Which sections of an RFP are most time-consuming to write? (e.g., technical specifications, evaluation criteria, qualification requirements)
- **Q2.3** Do you use standardized templates? If so, are they organization-specific or national templates?
- **Q2.4** How often do published tenders need to be corrected due to errors or omissions in the RFP?
- **Q2.5** Would you trust an AI-generated first draft that you then review and edit, or do you prefer AI as an assistant that suggests options?
- **Q2.6** What procurement procedures do you use most frequently? (Open, restricted, negotiated, competitive dialogue, innovation partnership)
- **Q2.7** What languages should the RFP drafting support? (Estonian, English, both?)

---

## 3. Market Price Intelligence — Real Estate

| ID | User Story | Persona |
|----|-----------|---------|
| US-11 | As a Budget Owner, I want to search historical tender data for office rental prices per square meter by city and region so that I set a realistic budget for our space requirements. | B3 |
| US-12 | As a Procurement Officer, I want the AI to show me comparable real estate tenders (office space, facility management, cleaning) in my region so that I understand current market rates. | B1 |
| US-13 | As a Finance Controller, I want to see price trends over time for real estate services (rental, maintenance, renovation) so that I can forecast costs for multi-year budget planning. | B5 |
| US-14 | As a Procurement Officer, I want the AI to suggest an estimated value range for my real estate procurement based on location, area, duration, and service level so that I set a proportionate contract value. | B1 |
| US-15 | As a Budget Owner, I want to compare public vs. private sector rental rates in a specific location so that I understand whether the procurement route offers value for money. | B3 |

### Questionnaire: Real Estate Pricing

- **Q3.1** What types of real estate procurements do you handle most often? (Office rental, facility management, cleaning, renovation, construction)
- **Q3.2** What data points are most important for real estate price benchmarking? (Price per m², total contract value, duration, location, service level)
- **Q3.3** Do you currently use any benchmarking data for setting estimated values in real estate tenders? If so, what sources?
- **Q3.4** How confident are you in the estimated values you currently set for real estate tenders? (Very confident / Somewhat / Not confident)
- **Q3.5** Would historical tender data (won contracts, actual costs) be more useful than market surveys?

---

## 4. Market Price Intelligence — Staff & Personnel

| ID | User Story | Persona |
|----|-----------|---------|
| US-16 | As a Budget Owner, I want to search for typical hourly rates and daily rates for different professional roles (developers, project managers, consultants, security guards) in public sector tenders so that I budget correctly. | B3 |
| US-17 | As a Procurement Officer, I want the AI to show me comparable staff procurement tenders (temporary agency workers, consulting, outsourced services) with their contract values and team compositions so that I benchmark my requirements. | B1 |
| US-18 | As a Technical Specialist, I want to search for typical qualification requirements for IT staff tenders (experience years, certifications, security clearances) so that I set requirements that are achievable but maintain quality. | B6 |
| US-19 | As a Finance Controller, I want to compare staffing costs across countries (Estonia, Latvia, Lithuania, Poland) for the same role types so that I understand regional cost differences for cross-border procurements. | B5 |
| US-20 | As a Procurement Officer, I want the AI to suggest a price scoring formula (lowest price, best price-quality ratio, cost-effectiveness) based on the type of staff procurement so that the evaluation method is appropriate. | B1 |

### Questionnaire: Staff & Personnel Pricing

- **Q4.1** What types of staff/personnel procurements do you handle? (IT consultants, temporary workers, cleaning staff, security, professional services)
- **Q4.2** Do you use hourly rates, daily rates, or total contract value for staff procurements?
- **Q4.3** What is the most challenging aspect of pricing staff tenders? (Setting rates, defining roles, estimating volume, evaluating quality)
- **Q4.4** Do you need to comply with minimum wage regulations or collective agreements when setting rate expectations?
- **Q4.5** Would benchmarking data from won contracts in other public sector organizations be useful?

---

## 5. Market Price Intelligence — Equipment

| ID | User Story | Persona |
|----|-----------|---------|
| US-21 | As a Budget Owner, I want to search for typical costs of IT equipment (servers, workstations, networking, software licenses) in public sector tenders so that I create accurate budgets. | B3 |
| US-22 | As a Procurement Officer, I want the AI to show comparable equipment tenders (medical equipment, vehicles, laboratory instruments, office furniture) with specifications and prices so that I benchmark our requirements. | B1 |
| US-23 | As a Technical Specialist, I want to search for technical specifications used in similar equipment tenders so that I draft specifications that are competitive but not restrictive to a single vendor. | B6 |
| US-24 | As a Finance Controller, I want to compare purchase vs. lease costs for equipment categories so that I recommend the most cost-effective procurement approach. | B5 |
| US-25 | As a Procurement Officer, I want the AI to detect if my equipment specifications are too restrictive (point to a single brand/vendor) and suggest alternatives so that I comply with non-discrimination principles. | B1 |

### Questionnaire: Equipment Pricing

- **Q5.1** What equipment categories do you procure most often? (IT hardware, software, medical, vehicles, office furniture, lab equipment)
- **Q5.2** Do you typically purchase outright or use leasing/rental agreements?
- **Q5.3** How do you currently estimate equipment costs? (Vendor quotes, market research, historical data, catalogues)
- **Q5.4** Have you ever had a tender challenged for overly restrictive specifications? How was it resolved?
- **Q5.5** Would an AI tool that checks specifications for brand-specificity be valuable?

---

## 6. Price Benchmarking & Analytics

| ID | User Story | Persona |
|----|-----------|---------|
| US-26 | As a Procurement Officer, I want the AI to generate a price benchmarking report for my planned procurement — comparing similar historical contracts by CPV code, country, and value range — so that I justify my estimated value. | B1 |
| US-27 | As a Procurement Manager, I want to see a market analysis canvas artifact showing price distributions, winner patterns, and competition levels for my procurement category so that I make data-driven decisions. | B2 |
| US-28 | As a Finance Controller, I want to export benchmarking data as a report (PDF) that I can attach to the procurement file to justify the estimated contract value. | B5 |
| US-29 | As a Budget Owner, I want the AI to alert me when my estimated budget is significantly above or below the market rate for similar procurements so that I adjust before publication. | B3 |
| US-30 | As a Procurement Officer, I want to ask the AI "what is a fair price for X?" and get an answer backed by actual tender data with sources so that I have evidence-based pricing. | B1 |

### Questionnaire: Price Benchmarking

- **Q6.1** How do you currently justify the estimated contract value in your procurements? (Market research, vendor quotes, historical data, expert opinion)
- **Q6.2** Have you ever had a procurement where the estimated value was significantly wrong? What was the impact?
- **Q6.3** Would you find value in automated benchmarking against similar contracts in other countries?
- **Q6.4** How important is it that price benchmarking data includes source references (links to actual tenders)?
- **Q6.5** Do you need benchmarking data in real-time, or would a monthly-updated dataset be sufficient?

---

## 7. Compliance & Quality Assurance

| ID | User Story | Persona |
|----|-----------|---------|
| US-31 | As a Legal Officer, I want the AI to validate that my RFP complies with EU procurement directives (2014/24/EU, 2014/25/EU) and national procurement law so that I reduce legal risk. | B4 |
| US-32 | As a Procurement Officer, I want the AI to check that evaluation criteria are proportionate to the contract value (no over-qualification) so that I maximize competition and don't receive complaints. | B1 |
| US-33 | As a Procurement Manager, I want the AI to estimate the expected number of bidders based on historical data for similar tenders in my region so that I set realistic expectations. | B2 |
| US-34 | As a Legal Officer, I want the AI to generate a compliance checklist for my procurement procedure (mandatory notices, standstill period, documentation requirements) so that I don't miss any steps. | B4 |
| US-35 | As a Procurement Officer, I want the AI to review my evaluation criteria and flag if the price weight is too high or too low compared to similar tenders so that I follow market norms. | B1 |

### Questionnaire: Compliance

- **Q7.1** Which procurement regulations do you need to comply with? (EU directives, national public procurement law, internal policies)
- **Q7.2** What are the most common compliance errors in your organization's procurements?
- **Q7.3** How often are your procurements challenged by bidders? What are the typical grounds?
- **Q7.4** Would you use an AI compliance checker before publishing a tender?
- **Q7.5** Do you need support for both above-threshold (EU) and below-threshold (national) procedures?

---

## 8. AI Chat Integration for Buyers

| ID | User Story | Persona |
|----|-----------|---------|
| US-36 | As a Procurement Officer, I want to start a chat with "I need to procure [X]" and have the AI guide me through the entire process — from requirements to RFP draft — step by step. | B1 |
| US-37 | As a Budget Owner, I want to ask "How much should we budget for [type of procurement]?" and get an AI answer backed by historical tender data in the canvas panel. | B3 |
| US-38 | As a Procurement Officer, I want to upload an existing tender document and ask the AI to review it for completeness and compliance issues displayed as a canvas artifact. | B1 |
| US-39 | As a Procurement Manager, I want conversation history preserved so that I can return to previous procurement planning sessions and continue where I left off. | B2 |
| US-40 | As a Technical Specialist, I want to ask the AI to generate technical specifications for a specific product or service category using examples from similar successful tenders. | B6 |

### Questionnaire: Chat Integration

- **Q8.1** Would you prefer a step-by-step guided workflow or a freeform chat where you can ask anything?
- **Q8.2** How important is it that the AI cites sources (specific tenders, regulations) in its answers?
- **Q8.3** Would you use this tool on mobile devices or primarily on desktop?
- **Q8.4** Should the AI remember context from previous procurement planning sessions?
- **Q8.5** Would you want to share a chat session with colleagues for collaborative procurement planning?

---

## Priority Rating Guide

Use the MoSCoW method to rate each user story:

| Rating | Meaning |
|--------|---------|
| **Must** | Critical for launch — the system is not usable without this feature |
| **Should** | Important — should be included if at all possible |
| **Could** | Desirable — include if time and budget allow |
| **Won't** | Not needed now — may be considered for future releases |

---

## How to Submit Feedback

1. Review each user story and assign a priority rating (Must / Should / Could / Won't)
2. Answer the questionnaire questions with your real-world experience
3. Add notes or comments for any user story that needs clarification
4. Flag any missing user stories or features not covered
5. Return the completed document to the Tendly product team

---

*Tendly Buyer AI Tools — User Stories & Stakeholder Questionnaire v1.0*
