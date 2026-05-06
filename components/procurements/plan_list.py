"""Procurement plan list and form components."""

from fasthtml.common import *
from core.utils import _raw, _get_file_type_info, _format_file_size
from config.i18n import t
from components.dashboard.overview import procurement_card
from components.procurements.ai_review_panel import ai_review_section


PROCUREMENT_CATEGORIES = [
    ("it", "IT & Technology"),
    ("kinnisvara", "Real Estate / Kinnisvara"),
    ("personal", "Personnel / Personal"),
    ("toitlustus", "Catering / Toitlustus"),
    ("ehitus", "Construction / Ehitus"),
    ("transport", "Transport"),
    ("meditsiiniline", "Medical / Meditsiiniline"),
    ("haridus", "Education / Haridus"),
    ("muu", "Other / Muu"),
]

WORKFLOW_STEPS = [
    (1, "domain_review", "Vajaduse ülevaade", "domain_lead"),
    (2, "market_research", "Turu-uuring", "domain_lead"),
    (3, "plan_review", "Hankeplaani ülevaade", "procurement_manager"),
    (4, "board_approval", "Eelarve kinnitamine", "board"),
    (5, "document_preparation", "Dokumentide koostamine", "domain_specialist"),
]

DOCUMENT_TYPES = [
    ("contract_template", "Contract Template / Lepingumall"),
    ("technical_description", "Technical Description / Tehniline kirjeldus"),
    ("good_practice", "Good Practice / Hea tava"),
    ("org_chart", "Org Chart / Struktuuriskeem"),
    ("cv", "CV / Team Roles"),
    ("iso_certificate", "ISO Certificate"),
    ("product_list", "Product List / Tootenimekiri (XLS)"),
    ("software_list", "Software List / Tarkvara nimekiri"),
    ("rit_inventory", "IT Inventory / RIT"),
    ("rfp_draft", "RFP Draft"),
    ("other", "Other / Muu"),
]

# Inline JS for dynamic form rows (evaluation criteria + requirements).
# All content is built from DOM API calls and data-attribute values only.
_DYNAMIC_FORM_JS = Script("""
(function(){
    var criteriaIdx = 0;
    var reqIdx = 0;

    function makeEl(tag, attrs, children) {
        var el = document.createElement(tag);
        if (attrs) Object.keys(attrs).forEach(function(k){ el.setAttribute(k, attrs[k]); });
        if (children) children.forEach(function(c){
            if (typeof c === 'string') el.appendChild(document.createTextNode(c));
            else if (c) el.appendChild(c);
        });
        return el;
    }

    window.addCriterionRow = function() {
        criteriaIdx++;
        var container = document.getElementById('criteria-rows');
        var phName = container.getAttribute('data-ph-name') || 'Criterion name';
        var phDesc = container.getAttribute('data-ph-desc') || 'Description';
        var idx = criteriaIdx;

        var nameInput = makeEl('input', {type:'text', name:'criterion_name_'+idx, placeholder:phName, class:'form-input', style:'flex:2;'});
        var weightInput = makeEl('input', {type:'number', name:'criterion_weight_'+idx, placeholder:'%', min:'0', max:'100', class:'form-input', style:'flex:0 0 80px;'});
        var descInput = makeEl('input', {type:'text', name:'criterion_desc_'+idx, placeholder:phDesc, class:'form-input', style:'flex:2;'});

        var fields = makeEl('div', {class:'dynamic-row-fields'}, [nameInput, weightInput, descInput]);
        var removeBtn = makeEl('button', {type:'button', class:'btn-remove-row', title:'Remove'}, [document.createTextNode('\\u00d7')]);
        removeBtn.addEventListener('click', function(){ row.remove(); serializeCriteria(); });

        var row = makeEl('div', {class:'dynamic-row', id:'criterion-'+idx}, [fields, removeBtn]);
        container.appendChild(row);
        serializeCriteria();
    };

    window.addRequirementRow = function() {
        reqIdx++;
        var container = document.getElementById('requirements-rows');
        var phText = container.getAttribute('data-ph-text') || 'Requirement';
        var lblMandatory = container.getAttribute('data-lbl-mandatory') || 'Mandatory';
        var lblPreferred = container.getAttribute('data-lbl-preferred') || 'Preferred';
        var idx = reqIdx;

        var textInput = makeEl('input', {type:'text', name:'req_text_'+idx, placeholder:phText, class:'form-input', style:'flex:3;'});

        var typeSelect = makeEl('select', {name:'req_type_'+idx, class:'form-select', style:'flex:0 0 130px;'}, [
            makeEl('option', {value:'qualification'}, ['Qualification']),
            makeEl('option', {value:'compliance'}, ['Compliance']),
            makeEl('option', {value:'service_level'}, ['Service level']),
            makeEl('option', {value:'experience'}, ['Experience'])
        ]);

        var prioSelect = makeEl('select', {name:'req_priority_'+idx, class:'form-select', style:'flex:0 0 110px;'}, [
            makeEl('option', {value:'must'}, [lblMandatory || 'Must']),
            makeEl('option', {value:'should'}, [lblPreferred || 'Should'])
        ]);

        var fields = makeEl('div', {class:'dynamic-row-fields'}, [textInput, typeSelect, prioSelect]);
        var removeBtn = makeEl('button', {type:'button', class:'btn-remove-row', title:'Remove'}, [document.createTextNode('\\u00d7')]);
        removeBtn.addEventListener('click', function(){ row.remove(); serializeRequirements(); });

        var row = makeEl('div', {class:'dynamic-row', id:'requirement-'+idx}, [fields, removeBtn]);
        container.appendChild(row);
        serializeRequirements();
    };

    function serializeCriteria() {
        var rows = document.querySelectorAll('#criteria-rows .dynamic-row');
        var criteria = [];
        rows.forEach(function(row) {
            var inputs = row.querySelectorAll('input');
            var name = inputs[0] ? inputs[0].value.trim() : '';
            var weight = inputs[1] ? parseFloat(inputs[1].value) || 0 : 0;
            var desc = inputs[2] ? inputs[2].value.trim() : '';
            if (name) {
                // Field names MUST match what the renderer reads in
                // _criteria_and_requirements_section (plan_list.py).
                criteria.push({name: name, weight: weight, description: desc});
            }
        });
        var hidden = document.getElementById('evaluation_criteria_json');
        if (hidden) hidden.value = JSON.stringify(criteria);
    }

    function serializeRequirements() {
        var rows = document.querySelectorAll('#requirements-rows .dynamic-row');
        var reqs = [];
        rows.forEach(function(row) {
            var input = row.querySelector('input');
            var selects = row.querySelectorAll('select');
            var text = input ? input.value.trim() : '';
            var rtype = selects[0] ? selects[0].value : 'qualification';
            var priority = selects[1] ? selects[1].value : 'must';
            if (text) {
                // Field names MUST match the renderer
                reqs.push({text: text, type: rtype, priority: priority});
            }
        });
        var hidden = document.getElementById('requirements_json');
        if (hidden) hidden.value = JSON.stringify(reqs);
    }

    // Pre-populate visible rows from the hidden JSON inputs (used by the
    // edit form, which loads with existing criteria/requirements).
    function hydrateFromHidden() {
        try {
            var critHidden = document.getElementById('evaluation_criteria_json');
            if (critHidden && critHidden.value && critHidden.value !== '[]') {
                var crit = JSON.parse(critHidden.value);
                crit.forEach(function(c) {
                    window.addCriterionRow();
                    var rows = document.querySelectorAll('#criteria-rows .dynamic-row');
                    var row = rows[rows.length - 1];
                    var inputs = row.querySelectorAll('input');
                    if (inputs[0]) inputs[0].value = c.name || c.criterion_name || '';
                    if (inputs[1]) inputs[1].value = c.weight || c.weight_percentage || '';
                    if (inputs[2]) inputs[2].value = c.description || '';
                });
                serializeCriteria();
            }
            var reqHidden = document.getElementById('requirements_json');
            if (reqHidden && reqHidden.value && reqHidden.value !== '[]') {
                var reqs = JSON.parse(reqHidden.value);
                reqs.forEach(function(r) {
                    window.addRequirementRow();
                    var rows = document.querySelectorAll('#requirements-rows .dynamic-row');
                    var row = rows[rows.length - 1];
                    var input = row.querySelector('input');
                    var selects = row.querySelectorAll('select');
                    if (input) input.value = r.text || r.requirement_text || '';
                    if (selects[0]) selects[0].value = r.type || r.requirement_type || 'qualification';
                    if (selects[1]) selects[1].value = r.priority || 'must';
                });
                serializeRequirements();
            }
        } catch (e) { console.error('hydrateFromHidden failed', e); }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hydrateFromHidden);
    } else {
        hydrateFromHidden();
    }

    // Re-serialize on form submit
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('procurement-form')) {
            serializeCriteria();
            serializeRequirements();
        }
    });

    // Also serialize on input changes
    document.addEventListener('input', function(e) {
        if (e.target.closest('#criteria-rows')) serializeCriteria();
        if (e.target.closest('#requirements-rows')) serializeRequirements();
    });
    document.addEventListener('change', function(e) {
        if (e.target.closest('#requirements-rows')) serializeRequirements();
    });
})();
""")


def procurement_list_page(plans=None, language="en"):
    plans = plans or []

    filter_bar = Div(
        Div(
            H1(t("procurements.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            A(
                f"+ {t('procurements.new', language)}",
                href="/procurements/new",
                cls="btn-primary",
            ),
            style="display:flex;align-items:center;justify-content:space-between;",
        ),
        cls="page-header",
    )

    if plans:
        plan_cards = [procurement_card(p) for p in plans]
        content = Div(*plan_cards, cls="plans-list")
    else:
        content = Div(
            _raw('<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'),
            P(t("procurements.empty", language), style="color:#6b7280;font-size:14px;margin:12px 0 4px;"),
            A(
                f"+ {t('procurements.create_first', language)}",
                href="/procurements/new",
                style="color:#2563eb;font-size:14px;font-weight:500;text-decoration:none;",
            ),
            style="text-align:center;padding:48px 0;",
        )

    return Div(filter_bar, content, cls="page-content")


def procurement_new_page(language="en", plan=None):
    """New / edit procurement plan form. When `plan` is given, fields are
    pre-populated and the form posts to the edit endpoint."""
    is_edit = bool(plan)
    plan = plan or {}
    meta = plan.get("metadata_json") or {}
    if isinstance(meta, str):
        try:
            import json as _json
            meta = _json.loads(meta)
        except Exception:
            meta = {}

    category_options = []
    cur_cat = (plan.get("category") or "").lower()
    for val, label in PROCUREMENT_CATEGORIES:
        opt_kwargs = {"value": val}
        if cur_cat and val.lower() == cur_cat:
            opt_kwargs["selected"] = True
        category_options.append(Option(label, **opt_kwargs))

    cur_method = plan.get("procurement_method") or "open"
    def _method_opt(label, val):
        kwargs = {"value": val}
        if val == cur_method:
            kwargs["selected"] = True
        return Option(label, **kwargs)

    initial_value = ""
    if plan.get("estimated_value"):
        try: initial_value = f"{float(plan['estimated_value']):.2f}"
        except Exception: initial_value = ""

    initial_deadline = meta.get("submission_deadline") or ""
    # If it's an ISO date with time, take just the YYYY-MM-DD part
    if initial_deadline and "T" in str(initial_deadline):
        initial_deadline = str(initial_deadline).split("T")[0]
    elif initial_deadline:
        initial_deadline = str(initial_deadline)[:10]

    initial_criteria_json = "[]"
    if meta.get("evaluation_criteria"):
        import json as _json
        initial_criteria_json = _json.dumps(meta["evaluation_criteria"])
    initial_requirements_json = "[]"
    if meta.get("requirements"):
        import json as _json
        initial_requirements_json = _json.dumps(meta["requirements"])

    page_title = (
        (t("procurements.edit_title", language) or "Edit Plan") if is_edit
        else t("procurements.new_title", language)
    )
    submit_label = (
        (t("procurements.save", language) or "Save changes") if is_edit
        else t("procurements.create", language)
    )
    form_action = f"/procurements/{plan['id']}/edit" if is_edit else "/procurements"
    cancel_target = f"/procurements/{plan['id']}" if is_edit else "/procurements"

    return Div(
        Div(
            H1(page_title, style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            cls="page-header",
        ),
        Form(
            # Title
            Div(
                Label(t("procurements.field_title", language), fr="title", cls="form-label"),
                Input(name="title", id="title", type="text",
                      value=plan.get("title", ""),
                      placeholder=t("procurements.title_placeholder", language),
                      cls="form-input", required=True),
                cls="form-group",
            ),
            # Description
            Div(
                Label(t("procurements.field_description", language), fr="description", cls="form-label"),
                Textarea(plan.get("description", ""),
                         name="description", id="description",
                         placeholder=t("procurements.description_placeholder", language),
                         cls="form-textarea", rows="4"),
                cls="form-group",
            ),
            # Category + Estimated Value row
            Div(
                Div(
                    Label(t("procurements.field_category", language), fr="category", cls="form-label"),
                    Select(*category_options, name="category", id="category", cls="form-select"),
                    cls="form-group",
                ),
                Div(
                    Label(t("procurements.field_estimated_value", language), fr="estimated_value", cls="form-label"),
                    Input(name="estimated_value", id="estimated_value", type="number", step="0.01",
                          value=initial_value, placeholder="0.00", cls="form-input"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            # CPV Code + Fiscal Year row
            Div(
                Div(
                    Label(t("procurements.field_cpv_code", language), fr="cpv_code", cls="form-label"),
                    Input(name="cpv_code", id="cpv_code", type="text",
                          value=plan.get("cpv_code", ""),
                          placeholder="e.g. 72000000", cls="form-input"),
                    cls="form-group",
                ),
                Div(
                    Label(t("procurements.field_fiscal_year", language), fr="fiscal_year", cls="form-label"),
                    Input(name="fiscal_year", id="fiscal_year", type="number",
                          value=str(plan.get("fiscal_year") or 2026),
                          cls="form-input"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            # Procurement Method + Submission Deadline row
            Div(
                Div(
                    Label(t("procurements.field_method", language), fr="procurement_method", cls="form-label"),
                    Select(
                        _method_opt("Open procedure / Avatud hange", "open"),
                        _method_opt("Restricted procedure / Piiratud hange", "restricted"),
                        _method_opt("Negotiated procedure / Väljakuulutamisega läbirääkimistega hange", "negotiated"),
                        _method_opt("Framework agreement / Raamleping", "framework"),
                        _method_opt("Simplified / Lihthange", "simplified"),
                        name="procurement_method", id="procurement_method", cls="form-select",
                    ),
                    cls="form-group",
                ),
                Div(
                    Label(t("procurements.deadline_label", language), fr="submission_deadline", cls="form-label"),
                    Input(name="submission_deadline", id="submission_deadline", type="date",
                          value=initial_deadline, cls="form-input"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            # --- Evaluation Criteria section ---
            Div(
                Div(
                    H3(t("procurements.criteria_title", language), style="font-size:15px;font-weight:600;color:#111827;margin:0;"),
                    Button(
                        _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'),
                        " ", t("procurements.add_criterion", language),
                        type="button",
                        cls="btn-add-row",
                        onclick="addCriterionRow()",
                    ),
                    style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;",
                ),
                # Column headers
                Div(
                    Span(t("procurements.criterion_name", language), style="flex:2;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;"),
                    Span(t("procurements.criterion_weight", language), style="flex:0 0 80px;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;"),
                    Span(t("procurements.field_description", language), style="flex:2;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;"),
                    Span("", style="width:32px;"),
                    style="display:flex;gap:8px;padding:0 0 6px;",
                    cls="dynamic-row-header",
                ),
                Div(
                    id="criteria-rows",
                    **{
                        "data-ph-name": t("procurements.criterion_name", language),
                        "data-ph-desc": t("procurements.description_placeholder", language),
                    },
                ),
                Input(type="hidden", name="evaluation_criteria_json",
                      id="evaluation_criteria_json", value=initial_criteria_json),
                cls="form-section",
            ),
            # --- Requirements section ---
            Div(
                Div(
                    H3(t("procurements.requirements_title", language), style="font-size:15px;font-weight:600;color:#111827;margin:0;"),
                    Button(
                        _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'),
                        " ", t("procurements.add_requirement", language),
                        type="button",
                        cls="btn-add-row",
                        onclick="addRequirementRow()",
                    ),
                    style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;",
                ),
                Div(
                    Span(t("procurements.requirements_title", language), style="flex:3;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;"),
                    Span(t("procurements.requirement_type", language), style="flex:0 0 130px;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;"),
                    Span("Priority", style="flex:0 0 110px;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;"),
                    Span("", style="width:32px;"),
                    style="display:flex;gap:8px;padding:0 0 6px;",
                    cls="dynamic-row-header",
                ),
                Div(
                    id="requirements-rows",
                    **{
                        "data-ph-text": t("procurements.requirements_title", language),
                        "data-lbl-mandatory": t("procurements.mandatory", language),
                        "data-lbl-preferred": t("procurements.preferred", language),
                    },
                ),
                Input(type="hidden", name="requirements_json",
                      id="requirements_json", value=initial_requirements_json),
                cls="form-section",
            ),
            # Form actions
            Div(
                Button(t("procurements.cancel", language), type="button", cls="btn-secondary",
                       onclick=f"window.location='{cancel_target}'"),
                Button(submit_label, type="submit", cls="btn-primary"),
                cls="form-actions",
            ),
            action=form_action,
            method="post",
            cls="procurement-form",
        ),
        _DYNAMIC_FORM_JS,
        cls="page-content",
    )


def _document_card(doc, plan_id, language="en"):
    """Render a single document card with file type icon, info, and actions."""
    file_name = doc.get("file_name", "")
    ext_label, svg_icon, css_class = _get_file_type_info(file_name)
    file_size_str = _format_file_size(doc.get("file_size", 0))
    doc_type_label = doc.get("document_type", "other").replace("_", " ").title()
    doc_id = doc.get("id", "")

    # Icon color based on file type
    icon_colors = {
        "detail-doc-icon-pdf": "#ef4444",
        "detail-doc-icon-doc": "#2563eb",
        "detail-doc-icon-xls": "#16a34a",
        "detail-doc-icon-zip": "#f59e0b",
        "detail-doc-icon-img": "#8b5cf6",
        "detail-doc-icon-default": "#6b7280",
    }
    icon_color = icon_colors.get(css_class, "#6b7280")

    info_parts = []
    if doc_type_label:
        info_parts.append(Span(doc_type_label, style="font-size:12px;color:#6b7280;"))
    if file_size_str:
        info_parts.append(Span(file_size_str, style="font-size:12px;color:#9ca3af;"))

    actions = []
    if file_name and doc_id:
        actions.append(
            A(
                _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'),
                href=f"/api/procurements/{plan_id}/documents/{doc_id}/download",
                style="display:inline-flex;align-items:center;padding:4px;color:#6b7280;",
                title="Download",
            )
        )
    if doc_id:
        actions.append(
            Button(
                _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>'),
                type="button",
                style="display:inline-flex;align-items:center;padding:4px;color:#9ca3af;background:none;border:none;cursor:pointer;",
                title="Delete",
                hx_delete=f"/api/procurements/{plan_id}/documents/{doc_id}",
                hx_confirm="Delete this document?",
                hx_target="closest .doc-card",
                hx_swap="outerHTML",
            )
        )

    return Div(
        Div(
            Div(
                _raw(svg_icon.replace('stroke="currentColor"', f'stroke="{icon_color}"')),
                style="width:32px;height:32px;flex-shrink:0;",
            ),
            Div(
                Div(doc.get("title", file_name or "Untitled"), style="font-size:14px;font-weight:600;color:#111827;line-height:1.3;"),
                Div(
                    *info_parts,
                    style="display:flex;align-items:center;gap:8px;margin-top:2px;",
                ) if info_parts else "",
            ),
            style="display:flex;align-items:center;gap:12px;flex:1;min-width:0;",
        ),
        Div(
            *actions,
            style="display:flex;align-items:center;gap:4px;flex-shrink:0;",
        ) if actions else "",
        style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:white;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:8px;",
        cls="doc-card",
    )


def _documents_section(plan_id, documents=None, language="en"):
    """Render the documents section for the procurement detail page."""
    documents = documents or []
    type_options = [Option(label, value=val) for val, label in DOCUMENT_TYPES]

    upload_form = Form(
        Div(
            Div(
                Label(t("procurements.document_title_label", language), cls="form-label"),
                Input(name="title", type="text", placeholder=t("procurements.document_title_label", language), cls="form-input", required=True),
                cls="form-group",
            ),
            Div(
                Label(t("procurements.requirement_type", language), cls="form-label"),
                Select(*type_options, name="document_type", cls="form-select"),
                cls="form-group",
            ),
            cls="form-row",
        ),
        Div(
            Label("File", cls="form-label"),
            Input(
                name="document", type="file",
                accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.csv",
                cls="form-input",
                required=True,
                style="padding:7px 12px;",
            ),
            P("PDF, DOCX, XLSX, TXT, CSV (max 10 MB)", style="font-size:11px;color:#9ca3af;margin-top:4px;"),
            cls="form-group",
        ),
        Div(
            Button(
                _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'),
                " ", t("procurements.upload_document", language),
                type="submit",
                cls="btn-primary",
                style="font-size:13px;padding:8px 16px;",
            ),
            cls="form-actions", style="justify-content:flex-start;border-top:none;margin-top:8px;padding-top:0;",
        ),
        action=f"/api/procurements/{plan_id}/documents",
        method="post",
        enctype="multipart/form-data",
    )

    if documents:
        doc_list = Div(*[_document_card(d, plan_id, language) for d in documents])
    else:
        doc_list = Div(
            _raw('<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>'),
            P(t("procurements.no_documents", language), style="color:#6b7280;font-size:13px;margin:8px 0 0;"),
            style="text-align:center;padding:24px 0;",
        )

    return Div(
        H2(t("procurements.documents_title", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 14px;"),
        upload_form,
        Div(style="margin-top:16px;"),
        doc_list,
        cls="dashboard-section",
    )


def procurement_step_page(plan, step_number, step_data, language="en"):
    """Detail page for a single workflow step.

    Shows the step name + role + status + a guidance paragraph, and a
    "Mark step complete" action button when the step is the active one."""
    step_meta = next((s for s in WORKFLOW_STEPS if s[0] == step_number), None)
    if not step_meta:
        return Div(P(t("procurements.step_not_found", language) or "Step not found",
                     style="padding:24px;color:#6b7280;"))
    _num, step_id, step_name_et, role = step_meta
    loc_step_name = t(f"procurements.step_name_{step_id}", language) or step_name_et
    loc_role = t(f"procurements.role_{role}", language) or role.replace("_", " ").title()

    # Localised English explanation of what the step is for. The Estonian
    # name lives in WORKFLOW_STEPS; we add a short rationale here so the
    # buyer knows what to actually DO at this step.
    GUIDANCE = {
        1: ("Need review",
            "Confirm the procurement need is real, scoped, and aligned "
            "with budget priorities. The Domain Lead writes a short "
            "needs-statement and outlines the problem to be solved."),
        2: ("Market research",
            "Survey the market: who supplies this, at what price range, "
            "what specs are typical? Use the AI chat to benchmark "
            "against similar past tenders and price-benchmark."),
        3: ("Plan review",
            "The Procurement Manager reviews the draft plan: procedure "
            "type (open / restricted / simple), evaluation criteria, "
            "qualification requirements, and timeline."),
        4: ("Budget approval",
            "The Board signs off on the estimated value and confirms "
            "the funding source. After approval the plan is locked for "
            "publication."),
        5: ("Document preparation",
            "The Domain Specialist drafts the contract notice, "
            "technical specification, draft contract, and ESPD form. "
            "Documents are uploaded below and reviewed with AI."),
    }
    title_en, blurb = GUIDANCE.get(step_number, ("Step", ""))

    status = (step_data or {}).get("status", "pending")
    completed_by = (step_data or {}).get("completed_by", "")
    completed_at = (step_data or {}).get("completed_at", "")

    status_color = {
        "completed": ("#10b981", "#ecfdf5", "#065f46"),
        "in_progress": ("#2563eb", "#eff6ff", "#1e40af"),
        "pending": ("#9ca3af", "#f3f4f6", "#374151"),
    }.get(status, ("#9ca3af", "#f3f4f6", "#374151"))
    dot, bg, txt = status_color

    is_current = (status == "in_progress") or (plan.get("current_step") == step_number and status != "completed")

    action_btn = ""
    if is_current:
        action_btn = Form(
            Button(
                t("procurements.complete_step", language) or "Mark step complete",
                type="submit",
                cls="btn-primary",
                style="font-size:13px;padding:8px 18px;",
            ),
            action=f"/procurements/{plan['id']}/steps/{step_number}/complete",
            method="post",
        )

    return Div(
        Div(
            A("← " + (t("procurements.back_to_plan", language) or "Back to plan"),
              href=f"/procurements/{plan['id']}",
              style="font-size:13px;color:#6b7280;text-decoration:none;"),
            style="margin-bottom:8px;",
        ),
        Div(
            Span(f"{t('procurements.step', language) or 'Step'} {step_number} / 5",
                 style="font-size:12px;color:#9ca3af;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;"),
            H1(loc_step_name, style="font-size:24px;font-weight:700;color:#111827;margin:4px 0 0;"),
            P(title_en, style="font-size:14px;color:#6b7280;margin:2px 0 0;"),
            cls="page-header",
        ),
        # Status + role chips
        Div(
            Div(
                Span(t("procurements.status", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(
                    Span(status.replace("_", " ").title(),
                         style=f"font-size:13px;font-weight:600;color:{txt};background:{bg};padding:4px 10px;border-radius:6px;display:inline-block;"),
                    style="margin-top:4px;",
                ),
                cls="info-card",
            ),
            Div(
                Span(t("procurements.assigned_role", language) or "Assigned role",
                     style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(loc_role,
                    style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            (Div(
                Span(t("procurements.completed_by", language) or "Completed by",
                     style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(completed_by or "—",
                    style="font-size:13px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ) if status == "completed" else Div()),
            cls="info-grid",
        ),
        # Guidance + action
        Div(
            H3(t("procurements.what_to_do", language) or "What to do at this step",
               style="font-size:15px;font-weight:600;color:#111827;margin:0 0 8px;"),
            P(blurb, style="font-size:14px;color:#374151;line-height:1.6;"),
            Div(action_btn, style="margin-top:14px;") if action_btn else Div(),
            cls="dashboard-section",
        ),
        cls="page-content",
    )


def procurement_detail_page(plan, steps=None, documents=None, language="en"):
    steps = steps or []
    documents = documents or []
    status = plan.get("status", "draft")
    current_step = plan.get("current_step", 1)

    step_indicators = []
    for i, (num, step_id, step_name_et, role) in enumerate(WORKFLOW_STEPS):
        if num < current_step:
            step_status = "completed"
        elif num == current_step:
            step_status = "in_progress"
        else:
            step_status = "pending"

        step_colors = {
            "completed": ("#10b981", "#ecfdf5", "#065f46"),
            "in_progress": ("#2563eb", "#eff6ff", "#1e40af"),
            "pending": ("#d1d5db", "#f9fafb", "#9ca3af"),
        }
        dot_color, bg_color, text_color = step_colors[step_status]

        # Localised step name + role using translation keys
        # (procurements.step_name_<step_id>, procurements.role_<role>)
        loc_name = t(f"procurements.step_name_{step_id}", language) or step_name_et
        loc_role = t(f"procurements.role_{role}", language) or role.replace("_", " ").title()

        # Active step gets an inline "Mark complete" CTA so the buyer can
        # advance the workflow without going to the step detail page first.
        right_action = ""
        if step_status == "in_progress":
            right_action = Form(
                Button(
                    t("procurements.mark_complete_short", language) or "Mark complete",
                    type="submit",
                    cls="btn-primary",
                    style="font-size:12px;padding:6px 12px;white-space:nowrap;",
                ),
                action=f"/procurements/{plan['id']}/steps/{num}/complete",
                method="post",
                style="margin-left:auto;flex-shrink:0;",
                onclick="event.stopPropagation();",
            )

        step_indicators.append(
            Div(
                Div(
                    Span(
                        _raw('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>') if step_status == "completed" else str(num),
                        style=f"display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:{dot_color};color:white;font-size:12px;font-weight:600;",
                    ),
                    style="flex-shrink:0;",
                ),
                Div(
                    Div(loc_name, style=f"font-size:13px;font-weight:600;color:{text_color};"),
                    Div(loc_role, style="font-size:11px;color:#9ca3af;"),
                    style="min-width:0;flex:1;",
                ),
                right_action,
                style=f"display:flex;align-items:center;gap:10px;padding:10px 14px;background:{bg_color};border-radius:10px;border:1px solid {dot_color}20;cursor:pointer;margin-bottom:6px;",
                onclick=f"window.location='/procurements/{plan['id']}/steps/{num}'",
            )
        )

    value_display = f"€{plan['estimated_value']:,.0f}" if plan.get("estimated_value") else "—"

    # Build info cards - include deadline if present
    info_cards = [
        Div(
            Div(t("procurements.field_category", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
            Div(plan.get("category", "—").replace("_", " ").title(), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
            cls="info-card",
        ),
        Div(
            Div(t("procurements.field_estimated_value", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
            Div(value_display, style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
            cls="info-card",
        ),
        Div(
            Div(t("procurements.status", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
            Div(status.capitalize(), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
            cls="info-card",
        ),
        Div(
            Div(t("procurements.field_method", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
            Div(plan.get("procurement_method", "—").replace("_", " ").title(), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
            cls="info-card",
        ),
    ]

    # Show deadline if available (from metadata_json or plan itself)
    metadata = plan.get("metadata_json") or {}
    deadline = metadata.get("submission_deadline") or plan.get("submission_deadline")
    if deadline:
        info_cards.append(
            Div(
                Div(t("procurements.deadline_label", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(str(deadline), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
        )

    return Div(
        Div(
            Div(
                A("← " + t("procurements.back", language), href="/procurements", style="font-size:13px;color:#6b7280;text-decoration:none;"),
                style="margin-bottom:8px;",
            ),
            Div(
                H1(plan.get("title", ""), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
                Div(
                    A(t("procurements.edit", language),
                      href=f"/procurements/{plan['id']}/edit",
                      cls="btn-secondary",
                      style="font-size:13px;padding:6px 14px;white-space:nowrap;flex-shrink:0;"),
                    A(
                        _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>'),
                        t("procurements.ask_ai", language),
                        href=f"/chat?plan={plan['id']}",
                        cls="btn-primary",
                        style="font-size:13px;padding:6px 14px;white-space:nowrap;flex-shrink:0;display:inline-flex;align-items:center;",
                    ),
                    style="display:flex;gap:8px;flex-shrink:0;",
                ),
                style="display:flex;align-items:center;justify-content:space-between;",
            ),
            cls="page-header",
        ),
        # Info cards
        Div(*info_cards, cls="info-grid"),
        # Workflow stepper
        Div(
            H2(t("procurements.workflow", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 12px;"),
            Div(*step_indicators, cls="workflow-steps"),
            cls="dashboard-section",
        ),
        # Evaluation criteria + requirements (from metadata_json)
        _criteria_and_requirements_section(metadata, language),
        # Documents section
        _documents_section(plan["id"], documents, language),
        # AI Document Review section
        ai_review_section(plan, language),
        cls="page-content",
    )


def _criteria_and_requirements_section(metadata, language="en"):
    """Render evaluation criteria + requirements if present in metadata_json.

    Returns an empty placeholder when neither is configured so the layout
    stays consistent."""
    criteria = metadata.get("evaluation_criteria") or []
    requirements = metadata.get("requirements") or []
    if not criteria and not requirements:
        return Div()

    blocks = []

    if criteria:
        rows = [
            Div(
                Div(c.get("name", ""), style="font-size:13px;font-weight:500;color:#111827;flex:1;min-width:0;"),
                Div(
                    f"{c.get('weight', '')}%" if c.get("weight") not in (None, "") else "",
                    style="font-size:13px;color:#6b7280;width:60px;text-align:right;font-variant-numeric:tabular-nums;",
                ),
                Div(c.get("description", ""), style="font-size:12px;color:#6b7280;flex:2;min-width:0;"),
                style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #f3f4f6;",
            )
            for c in criteria
        ]
        blocks.append(
            Div(
                H2(t("procurements.evaluation_criteria", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 12px;"),
                *rows,
                cls="dashboard-section",
            )
        )

    if requirements:
        rows = [
            Div(
                Div(r.get("text", ""), style="font-size:13px;color:#111827;flex:1;min-width:0;"),
                Span(
                    r.get("priority", "should").upper(),
                    style=(
                        "font-size:10px;font-weight:700;padding:3px 8px;border-radius:999px;"
                        + ("background:#fee2e2;color:#991b1b;" if r.get("priority") == "must"
                           else "background:#fef3c7;color:#92400e;" if r.get("priority") == "should"
                           else "background:#e5e7eb;color:#374151;")
                    ),
                ),
                Span(
                    (r.get("type") or "").replace("_", " ").title(),
                    style="font-size:11px;color:#6b7280;width:120px;text-align:right;",
                ),
                style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #f3f4f6;",
            )
            for r in requirements
        ]
        blocks.append(
            Div(
                H2(t("procurements.requirements", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 12px;"),
                *rows,
                cls="dashboard-section",
            )
        )

    return Div(*blocks)
