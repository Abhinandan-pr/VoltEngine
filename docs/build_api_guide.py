from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "VoltEngine_API_Guide.pdf"
NAVY = colors.HexColor("#183B63")
BLUE = colors.HexColor("#2878B5")
PALE = colors.HexColor("#EEF5FB")
INK = colors.HexColor("#243447")
MUTED = colors.HexColor("#61758A")
GREEN = colors.HexColor("#18805B")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=25, leading=30, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Subtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=12, leading=18, textColor=MUTED, spaceAfter=16,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=16, leading=20, textColor=NAVY, spaceBefore=8, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Subsection", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11, leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.5, leading=14, textColor=INK, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8, leading=11, textColor=MUTED, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="CodeCustom", fontName="Courier", fontSize=7.1, leading=9.2,
    textColor=INK, backColor=PALE,
    borderPadding=8, leftIndent=4, rightIndent=4, spaceBefore=4, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="TableHead", fontName="Helvetica-Bold", fontSize=8.5,
    leading=11, textColor=colors.white,
))
styles.add(ParagraphStyle(
    name="TableCell", fontName="Helvetica", fontSize=8.3,
    leading=11, textColor=INK,
))
styles.add(ParagraphStyle(
    name="Callout", fontName="Helvetica-Bold", fontSize=9,
    leading=13, textColor=NAVY,
))


def P(text, style="BodyCustom"):
    return Paragraph(text, styles[style])


def code(text):
    return Preformatted(text.strip("\n"), styles["CodeCustom"])


def callout(text, background=PALE, border=BLUE):
    table = Table([[P(text, "Callout")]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def draw_chrome(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 8 * mm, width, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(18 * mm, height - 5.4 * mm, "VOLTENGINE  /  BILLING API GUIDE")
    canvas.setStrokeColor(colors.HexColor("#D6E0EA"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "Beginner guide | Keep API keys private")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=19 * mm,
        title="VoltEngine Billing API Guide",
        author="VoltEngine",
        subject="Allowlisted API setup and billing endpoints",
    )
    story = []

    story.extend([
        Spacer(1, 9 * mm),
        P("VoltEngine Billing API", "CoverTitle"),
        P("A plain-language guide to allowlisting clients and sending billing requests.", "Subtitle"),
        HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=12),
        P("What this API does", "Section"),
        P("VoltEngine accepts account, meter, and tariff data, runs the billing calculation, and returns the charge breakdown, updated balances, and ledger lines. It provides daily billing, monthly invoice summaries, and wallet recharge endpoints.", "BodyCustom"),
        P("How a request works", "Section"),
    ])
    flow = [[
        P("1. Your app<br/>sends JSON", "Callout"),
        P("2. Key and IP<br/>are checked", "Callout"),
        P("3. Billing<br/>is calculated", "Callout"),
        P("4. Result and ledger<br/>are returned", "Callout"),
    ]]
    flow_table = Table(flow, colWidths=[43.5 * mm] * 4, rowHeights=[22 * mm])
    flow_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#C7D8E8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.extend([flow_table, Spacer(1, 8), callout("This service is stateless. Your system must save the returned wallet balance, arrear balance, and ledger entries. VoltEngine does not store account records."), P("Access: two allowlists are required", "Section")])
    story.append(P("Each billing request must pass both checks. A correct API key alone is not enough, and an approved IP alone is not enough. If either allowlist is missing, billing endpoints return HTTP 503 and remain unavailable.", "BodyCustom"))
    story.extend([
        P("1. API key: the request sends an approved value in the <b>X-API-Key</b> header.", "BodyCustom"),
        P("2. Client IP: the request must come from an approved IP address or CIDR range.", "BodyCustom"),
        P("Configure comma-separated values in the server environment:", "BodyCustom"),
        code('VOLTENGINE_API_KEYS="client-key-one,client-key-two"\nVOLTENGINE_ALLOWED_IPS="203.0.113.10,198.51.100.0/24"'),
        P("Replace the example addresses with real client IPs. Generate strong random API keys, share them only with approved clients, and never commit keys to source control. CIDR is a network range such as 198.51.100.0/24.", "Small"),
        PageBreak(),
    ])

    story.extend([P("Run and explore the API", "Section"), P("Install the API extra and start the server from the repository folder. For local development, use 127.0.0.1. For a deployed service, bind to 0.0.0.0 and set the port required by the host.", "BodyCustom"), code('python -m pip install -e ".[api]"\npython -m uvicorn http_api:app --host 127.0.0.1 --port 8000'), P("Open /docs on the running server to see interactive request forms. The health check at /health is public. All /v1/billing/* routes require both allowlists.", "BodyCustom"), callout("Behind a reverse proxy? The IP check sees the address the ASGI server trusts. Configure forwarded-address handling only for your trusted proxy; do not trust client-supplied X-Forwarded-For headers."), P("Endpoints", "Section")])
    endpoint_rows = [
        [P("Method and path", "TableHead"), P("Purpose", "TableHead"), P("Required input", "TableHead")],
        [P("GET /health", "TableCell"), P("Confirm the service is running.", "TableCell"), P("None. Public endpoint.", "TableCell")],
        [P("POST /v1/billing/daily", "TableCell"), P("Calculate one daily prepaid bill.", "TableCell"), P("Consumer, meter, tariff, period days, billing date.", "TableCell")],
        [P("POST /v1/billing/monthly", "TableCell"), P("Summarize supplied ledger entries for a month.", "TableCell"), P("Consumer ID, balances, month, ledger lines.", "TableCell")],
        [P("POST /v1/billing/recharge", "TableCell"), P("Add funds to a wallet and optionally revise installment.", "TableCell"), P("Consumer ID, current balances, amount.", "TableCell")],
    ]
    endpoint_table = Table(endpoint_rows, colWidths=[47 * mm, 55 * mm, 72 * mm], repeatRows=1)
    endpoint_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D5E0EA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([endpoint_table, Spacer(1, 8), P("Daily billing input", "Subsection"), P("The consumer object carries the current wallet, arrear, sanctioned load, and optional installment. The meter object has daily units and maximum demand. The tariff object contains rate slabs and charge settings. The last slab must have <b>upto: null</b> so all usage can be priced.", "BodyCustom"), P("Daily response", "Subsection"), P("The response has a result object with totalDeduction, charge breakup, and updated state balances, plus a ledger array describing the entries posted by this calculation. Save these returned balances before the next billing request.", "BodyCustom"), PageBreak()])

    daily_json = '''{
  "consumer": {
    "consumer_id": "C-1001",
    "wallet_balance": 500.0,
    "arrear_balance": 120.0,
    "load_kw": 3.0,
    "installment": {"total": 120.0, "daily": 2.0, "tenureDays": 60}
  },
  "meter": {"daily_units": 8.5, "max_demand_kw": 2.4},
  "tariff": {
    "slabs": [
      {"upto": 50, "rate": 3.1},
      {"upto": 100, "rate": 3.6},
      {"upto": null, "rate": 4.1}
    ],
    "fixed_charge": 120,
    "duty_rate": 0.05,
    "dps_monthly_rate": 0.015,
    "demand_rate": 250,
    "excess_demand_multiplier": 1.5
  },
  "period_days": 30,
  "billing_date": "2026-11-06"
}'''
    story.extend([
        P("Daily billing: complete example", "Section"),
        P("Send this JSON to <b>POST /v1/billing/daily</b>. Include the approved key as a header. Values below are illustrative; use the actual account and tariff data for your utility.", "BodyCustom"),
        code(daily_json),
        P("Example response shape", "Subsection"),
        code('''{
  "result": {
    "totalDeduction": 33.73,
    "breakup": {"energy": 26.35, "fixed": 4.0, "duty": 1.32,
                "dps": 0.06, "installment": 2.0},
    "state": {"walletBalance": 466.27, "arrearBalance": 118.06}
  },
  "ledger": [
    {"date": "2026-11-06", "type": "ENERGY", "amount": 26.35, "balance": 466.27}
  ]
}'''),
        P("These sample amounts correspond to the example input on the previous page. Your result changes with the consumer, tariff, and meter values you send.", "Small"),
        PageBreak(),
    ])

    story.extend([
        P("Monthly summary and recharge", "Section"),
        P("Monthly invoice request", "Subsection"),
        P("Send <b>POST /v1/billing/monthly</b> with the month in YYYY-MM format and the ledger lines to summarize. Accepted line types include ENERGY, FIXED, DUTY, DPS, INSTALLMENT_RECOVERY, and EXCESS_DEMAND_PENALTY. The service normalizes letter case.", "BodyCustom"),
        code('''{
  "consumer_id": "C-1001",
  "wallet_balance": 466.27,
  "arrear_balance": 118.06,
  "month": "2026-11",
  "ledger_entries": [
    {"type": "ENERGY", "amount": 26.35},
    {"type": "FIXED", "amount": 4.0},
    {"type": "DUTY", "amount": 0.79}
  ]
}'''),
        P("Recharge request", "Subsection"),
        P("Send <b>POST /v1/billing/recharge</b> with current account state and a positive amount. The response contains the new wallet balance and installment. Save the returned state in your account system.", "BodyCustom"),
        code('''{
  "consumer_id": "C-1001",
  "wallet_balance": 466.27,
  "arrear_balance": 118.06,
  "load_kw": 3.0,
  "installment": {"total": 120.0, "daily": 2.0, "tenureDays": 60},
  "amount": 500.0,
  "revise_installment": true
}'''),
        P("Common errors", "Section"),
    ])
    errors = [
        [P("HTTP status", "TableHead"), P("Meaning and action", "TableHead")],
        [P("401", "TableCell"), P("Missing or incorrect API key. Send a valid X-API-Key header.", "TableCell")],
        [P("403", "TableCell"), P("Client address is not allowlisted. Add the caller IP or its CIDR range to VOLTENGINE_ALLOWED_IPS.", "TableCell")],
        [P("422", "TableCell"), P("Input is invalid. Check required fields, non-negative values, dates, and final open-ended tariff slab.", "TableCell")],
        [P("503", "TableCell"), P("One or both allowlists are missing or malformed. Configure both server environment variables.", "TableCell")],
    ]
    err_table = Table(errors, colWidths=[30 * mm, 144 * mm], repeatRows=1)
    err_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D5E0EA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        err_table, Spacer(1, 9),
        callout("Important: VoltEngine does not save balances or prevent your application from recording the same returned result twice. Persist every successful response once, maintain an audit trail, and send the latest balances on the next request.", background=colors.HexColor("#FFF5E8"), border=colors.HexColor("#D88726")),
        Spacer(1, 6),
        P("For developers: GET /docs provides interactive OpenAPI documentation while the service is running. Keep production keys private and manage the allowlists through deployment settings.", "Small"),
    ])
    doc.build(story, onFirstPage=draw_chrome, onLaterPages=draw_chrome)
    print(OUTPUT)


if __name__ == "__main__":
    build()
