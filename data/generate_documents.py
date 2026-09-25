"""Programmatically generate 10 comprehensive, consistent policy PDFs for Roboserv 4i Private Limited"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.pdfgen import canvas

DOCUMENTS_DIR = Path("data/documents")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page numbers and running header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E293B"))  # Slate 800
        # Running header
        self.drawString(54, 750, "Roboserv 4i Private Limited — Official Corporate Policy")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(558, 750, "Internal & Confidential")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Running footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Enterprise Policy Assistant Knowledge Base — Roboserv 4i Portal")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=15
    ))
    styles.add(ParagraphStyle(
        'MetaBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    ))
    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'PolicyBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'BulletPoint',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E40AF")
    ))
    return styles


def build_pdf(filename, pages_content, metadata):
    filepath = DOCUMENTS_DIR / filename
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=55
    )
    styles = get_custom_styles()
    story = []

    for page_idx, page in enumerate(pages_content):
        if page_idx == 0:
            # First page title & metadata box
            story.append(Paragraph(metadata["title"], styles['DocTitle']))
            story.append(Paragraph(f"Document ID: {metadata['code']} | Version {metadata['version']} | Effective Date: {metadata['effective_date']}", styles['DocSubtitle']))
            
            meta_data = [
                [
                    Paragraph(f"<b>Issuing Department:</b> {metadata['department']}", styles['MetaBox']),
                    Paragraph(f"<b>Document Owner:</b> {metadata['owner']}", styles['MetaBox'])
                ],
                [
                    Paragraph(f"<b>Applicability:</b> {metadata['applicability']}", styles['MetaBox']),
                    Paragraph(f"<b>Classification:</b> Confidential / Internal Use Only", styles['MetaBox'])
                ]
            ]
            meta_table = Table(meta_data, colWidths=[250, 250])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 14))

        # Page sections
        for section in page["sections"]:
            if "title" in section and section["title"]:
                story.append(Paragraph(section["title"], styles['SectionHeader']))
            if "subtitle" in section and section["subtitle"]:
                story.append(Paragraph(section["subtitle"], styles['SubSectionHeader']))
            if "paragraphs" in section:
                for p in section["paragraphs"]:
                    story.append(Paragraph(p, styles['PolicyBody']))
            if "bullets" in section:
                for b in section["bullets"]:
                    story.append(Paragraph(f"• {b}", styles['BulletPoint']))
            if "callout" in section:
                callout_data = [[Paragraph(f"<b>IMPORTANT RULE:</b> {section['callout']}", styles['CalloutText'])]]
                callout_tbl = Table(callout_data, colWidths=[500])
                callout_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#93C5FD")),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ]))
                story.append(Spacer(1, 4))
                story.append(callout_tbl)
                story.append(Spacer(1, 6))

        if page_idx < len(pages_content) - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated {filename} ({len(pages_content)} pages)")


def generate_all_documents():
    print("Generating official fictional policies for Roboserv 4i Private Limited..")

    # 1. leave_policy.pdf (6 pages)
    leave_policy_pages = [
        {
            "sections": [
                {
                    "title": "1. Policy Purpose and Objectives",
                    "paragraphs": [
                        "Roboserv 4i Private Limited recognizes the vital importance of personal well-being, work-life integration, and health restoration for all team members. This policy governs the allotment, accrual, approval, and management of employee leaves.",
                        "The primary objective is to maintain operational continuity across customer engagements while ensuring fair, equitable, and transparent rest opportunities for employees."
                    ]
                },
                {
                    "title": "2. Scope and Annual Leave Cycle",
                    "paragraphs": [
                        "This policy applies to all full-time regular employees, probationary staff, and fixed-term retainers across all Roboserv 4i entities in India.",
                        "The annual leave calendar at Roboserv 4i operates strictly from January 1st to December 31st of each calendar year. All statutory entitlements are credited on a pro-rata basis for employees joining mid-year."
                    ],
                    "bullets": [
                        "Full-time confirmed employees receive an annual leave portfolio comprising Casual Leave, Sick Leave, and Paid/Privilege Leave.",
                        "Statutory holidays are governed under the separate Holiday Policy (DOC-HP-2026).",
                        "All leave applications must be initiated via the Roboserv 4i Enterprise Portal or the Enterprise Policy Assistant."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Casual Leave (CL) Regulations",
                    "paragraphs": [
                        "Casual leave is provided to meet unforeseen emergencies, urgent personal obligations, or short family matters.",
                        "According to the Leave Policy, employees are entitled to 12 casual leaves per year. For new joiners, casual leaves are credited pro-rata at the rate of 1 day per completed month of service."
                    ],
                    "bullets": [
                        "Casual leave cannot be availed for more than 3 consecutive working days without prior approval from the Department Head.",
                        "Casual leaves cannot be combined or prefixed/suffixed with Paid Privilege Leave or Maternity Leave.",
                        "Unutilized casual leave expires automatically on December 31st each year and CANNOT be carried forward to the subsequent calendar year.",
                        "Casual leave cannot be encashed under any circumstances."
                    ],
                    "callout": "Employees are entitled to 12 casual leaves per year. Maximum 3 consecutive casual leaves are permitted without prior manager authorization."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Sick Leave (SL) Regulations",
                    "paragraphs": [
                        "Sick leave is granted to enable employees to recuperate from illness, injury, or contagious medical conditions without financial disadvantage.",
                        "Roboserv 4i employees are entitled to 10 days of paid sick leave per calendar year, credited in advance on January 1st."
                    ],
                    "bullets": [
                        "Employees must inform their reporting manager via Slack, email, or Enterprise Assistant before 10:00 AM on the day of absence.",
                        "A valid medical certificate issued by a registered medical practitioner (MBBS or equivalent) is strictly mandatory whenever sick leave exceeds 2 consecutive working days.",
                        "Unutilized sick leave can be accumulated up to a maximum limit of 30 days across an employee's tenure.",
                        "Sick leave cannot be encashed at the time of resignation or retirement."
                    ],
                    "callout": "A registered doctor's medical certificate is mandatory if sick leave exceeds 2 consecutive working days."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "5. Paid Leave (PL) / Privilege Leave Guidelines",
                    "paragraphs": [
                        "Paid Leave (also termed Privilege or Earned Leave) is intended for planned vacations, personal milestones, and extended family time.",
                        "Full-time employees accrue 18 days of paid leave per calendar year, earned on a monthly basis at the rate of 1.5 days per month of active service."
                    ],
                    "bullets": [
                        "Employees must apply for Paid Leave at least 7 calendar days in advance for leaves up to 3 days, and at least 14 calendar days in advance for leaves exceeding 3 days.",
                        "Managerial approval is mandatory before travel or leave commencement.",
                        "Unutilized paid leave can be carried forward to the following year up to an absolute ceiling of 45 days. Any accrued days beyond 45 will lapse on December 31st.",
                        "Accumulated paid leave up to 45 days is eligible for encashment upon separation or retirement based on basic salary."
                    ],
                    "callout": "Paid Leave requires at least 7 days advance application. Maximum 45 days can be accumulated, which is encashable upon separation."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "6. Parental Leave (Maternity & Paternity)",
                    "paragraphs": [
                        "Roboserv 4i is dedicated to supporting new parents during early child bonding and care.",
                        "Female employees who have completed at least 80 days of continuous service prior to the expected delivery date are entitled to 26 weeks (182 calendar days) of fully paid maternity leave for up to two surviving children.",
                        "In case of adoption or surrogacy of an infant below 3 months, 12 weeks of paid maternity leave is granted."
                    ],
                    "bullets": [
                        "Male employees are entitled to 10 working days of fully paid paternity leave.",
                        "Paternity leave must be availed within 6 months from the date of the child's birth or legal adoption.",
                        "Paternity leave may be taken continuously or split into a maximum of two installments.",
                        "Supporting documents (birth certificate or hospital discharge summary) must be uploaded to the portal."
                    ],
                    "callout": "Maternity leave is 26 weeks of paid leave for up to two children. Paternity leave is 10 working days within 6 months of childbirth."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "7. Special Leaves & Application Workflow",
                    "subtitle": "Bereavement Leave & Compensatory Off",
                    "paragraphs": [
                        "Roboserv 4i provides up to 5 consecutive working days of paid bereavement leave in the unfortunate event of the demise of an immediate family member (parents, spouse, children, siblings, or parents-in-law).",
                        "Compensatory Off (Comp-off) is granted when an employee works on a scheduled weekend or declared national holiday with prior written approval from the Department Head. Comp-offs must be utilized within 60 days of accrual, after which they lapse."
                    ],
                    "subtitle": "Working Days Calculation and Safety Verification",
                    "paragraphs": [
                        "When applying for leave, the system calculates working days between start date and end date (inclusive). Saturdays, Sundays, and declared public holidays are strictly excluded from the leave count.",
                        "Confirmation Safety Rule: The Enterprise Policy Assistant will always review leave balances, compute exact working days, verify eligibility, and request explicit user confirmation before recording the leave transaction in the database."
                    ],
                    "callout": "Working days calculation excludes Saturdays, Sundays, and public holidays. Leave balance is deducted only after explicit employee confirmation."
                }
            ]
        }
    ]
    build_pdf("leave_policy.pdf", leave_policy_pages, {
        "title": "Comprehensive Leave Policy",
        "code": "DOC-HR-LP-2026",
        "version": "2.1",
        "effective_date": "January 1, 2026",
        "department": "Human Resources",
        "owner": "Chief People Officer",
        "applicability": "All Roboserv 4i Employees"
    })

    # 2. wfh_policy.pdf (4 pages)
    wfh_pages = [
        {
            "sections": [
                {
                    "title": "1. Hybrid Work Model Overview",
                    "paragraphs": [
                        "Roboserv 4i Private Limited operates under a progressive hybrid working framework designed to combine in-person collaboration with remote flexibility.",
                        "Under the standard policy, regular full-time employees in eligible roles may Work From Home (WFH) for up to 2 days per business week, with the remaining 3 days spent in office at their designated Roboserv 4i development facility."
                    ],
                    "bullets": [
                        "WFH days must be aligned with project sprint schedules and approved by the immediate project manager.",
                        "Certain designated roles requiring high-security physical infrastructure or lab hardware are exempt from remote work.",
                        "Client requirements and contractual obligations supersede general hybrid flexibility."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Core Working Hours & Availability",
                    "paragraphs": [
                        "To foster cohesive communication across cross-functional teams, Roboserv 4i defines core working hours.",
                        "All employees, whether working on-site or remotely, must remain accessible and actively online during core business hours: 10:00 AM to 5:00 PM IST."
                    ],
                    "bullets": [
                        "Employees must update their status on Slack and enterprise collaboration tools.",
                        "Video cameras are encouraged during customer meetings and agile ceremonies.",
                        "Any unannounced absence during core working hours will be treated as undocumented leave."
                    ],
                    "callout": "Core working hours are 10:00 AM to 5:00 PM IST. Employees must remain active on enterprise communication channels."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Home Office Equipment & Broadband Allowance",
                    "paragraphs": [
                        "Roboserv 4i equips every employee with an enterprise-grade laptop configured with endpoint protection and required developer tools.",
                        "Full-time confirmed employees are eligible for a one-time remote workstation setup allowance of up to INR 15,000 for purchasing ergonomic chairs, external monitors, keyboards, or UPS power backups."
                    ],
                    "bullets": [
                        "Employees working in hybrid roles are eligible for monthly broadband internet reimbursement up to INR 1,500.",
                        "A minimum stable broadband speed of 50 Mbps is mandatory for remote connectivity.",
                        "Invoices with GST details must be submitted through the finance portal by the 25th of each month."
                    ],
                    "callout": "One-time WFH ergonomic setup allowance is INR 15,000. Monthly broadband reimbursement is up to INR 1,500."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Remote Security & Compliance",
                    "paragraphs": [
                        "Information security is paramount when accessing corporate repositories, client datasets, and proprietary software from outside the corporate perimeter.",
                        "All remote connections must be routed through the Roboserv 4i GlobalProtect Virtual Private Network (VPN) with multi-factor authentication (MFA)."
                    ],
                    "bullets": [
                        "Operating from public Wi-Fi networks (cafes, airports) is strictly forbidden without active VPN tunnel encryption.",
                        "Screens must automatically lock after 2 minutes of inactivity.",
                        "Company laptops must not be shared with family members, friends, or third parties."
                    ],
                    "callout": "Mandatory usage of Roboserv 4i GlobalProtect VPN. Auto-screen lock is enforced at 2 minutes of idle time."
                }
            ]
        }
    ]
    build_pdf("wfh_policy.pdf", wfh_pages, {
        "title": "Hybrid & Remote Work Policy",
        "code": "DOC-OPS-WFH-2026",
        "version": "3.0",
        "effective_date": "February 1, 2026",
        "department": "Operations & HR",
        "owner": "Head of People & Facilities",
        "applicability": "All Hybrid & Remote Roles"
    })

    # 3. attendance_policy.pdf (4 pages)
    attendance_pages = [
        {
            "sections": [
                {
                    "title": "1. Standard Working Hours",
                    "paragraphs": [
                        "Roboserv 4i Private Limited maintains a 5-day working week, Monday through Friday, comprising 40 regular hours per week.",
                        "Standard office hours are from 9:30 AM to 6:30 PM IST, including an aggregate 1-hour break for lunch and tea."
                    ],
                    "bullets": [
                        "Flexibility in shift timing must be approved by the Department Head.",
                        "Customer-aligned teams supporting UK or US shifts follow designated client operational windows."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Attendance Recording & Grace Period",
                    "paragraphs": [
                        "Attendance is captured digitally via automated smart-card badge swipes at facility turnstiles or biometric/portal login timestamps.",
                        "Roboserv 4i provides a 30-minute grace period for morning logins, permitting arrival up to 10:00 AM IST up to 3 times per calendar month without deduction."
                    ],
                    "bullets": [
                        "Logins recorded after 10:00 AM without prior managerial notice are flagged as tardy.",
                        "Four or more tardy occurrences in a month will result in a half-day deduction from Casual Leave."
                    ],
                    "callout": "Grace period allows login up to 10:00 AM IST, permitted up to 3 times per calendar month."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Half-Day and Minimum Working Hours",
                    "paragraphs": [
                        "To be credited with a full day of attendance, an employee must record at least 8 working hours in a single business day.",
                        "A half-day attendance credit requires a minimum of 4.5 hours of logged active work.",
                        "Logging fewer than 4 hours in a working day is categorized as an absence unless formal leave has been sanctioned in advance."
                    ],
                    "callout": "Minimum 4.5 hours required for half-day credit. Fewer than 4 hours is categorized as absent."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Overtime and Compensatory Off",
                    "paragraphs": [
                        "While Roboserv 4i discourages habitual overtime, project delivery imperatives or emergency production support may occasionally require extra hours.",
                        "Any work on weekends or declared company holidays requires prior written authorization from the Department Head.",
                        "Employees working on holidays receive 1 full day of Compensatory Off (Comp-off), which must be claimed within 60 days."
                    ]
                }
            ]
        }
    ]
    build_pdf("attendance_policy.pdf", attendance_pages, {
        "title": "Attendance & Punctuality Policy",
        "code": "DOC-HR-ATT-2026",
        "version": "1.8",
        "effective_date": "January 1, 2026",
        "department": "Human Resources",
        "owner": "Director of Talent Operations",
        "applicability": "All Roboserv 4i Employees"
    })

    # 4. travel_policy.pdf (4 pages)
    travel_pages = [
        {
            "sections": [
                {
                    "title": "1. Travel Authorization & Booking Lead Times",
                    "paragraphs": [
                        "This policy establishes guidelines for domestic and international travel undertaken on behalf of Roboserv 4i Private Limited",
                        "All business travel must be formally initiated via the Roboserv 4i Travel Desk and approved by the respective Delivery Head or Vice President."
                    ],
                    "bullets": [
                        "Domestic travel requests must be submitted at least 14 days prior to the departure date to optimize airline and hotel booking rates.",
                        "International business travel requires at least 21 days advance booking and approval from the Chief Operating Officer (COO)."
                    ],
                    "callout": "Domestic travel requires 14 days advance booking. International travel requires 21 days advance booking."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Mode of Transportation & Flight Guidelines",
                    "paragraphs": [
                        "Air travel is permitted for domestic journeys where the one-way distance exceeds 500 kilometers or where rail travel duration exceeds 6 hours.",
                        "Standard air travel class across all levels is Economy Class. Business class travel is permitted only for international flights exceeding 8 continuous flight hours, subject to VP approval."
                    ],
                    "bullets": [
                        "Train travel is entitled under 2nd AC or 3rd AC tiers for inter-city travel below 500 kilometers.",
                        "Airport taxi rides should be arranged via authorized corporate ride-hailing profiles (Ola/Uber Business)."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Lodging & Hotel Tariff Limits",
                    "paragraphs": [
                        "Roboserv 4i partners with corporate hotel chains to provide safe, hygienic, and convenient lodging.",
                        "The nightly room tariff caps (exclusive of statutory taxes) are defined by city tiers:"
                    ],
                    "bullets": [
                        "Tier-1 Metropolitan Cities (Bengaluru, Mumbai, Delhi-NCR, Hyderabad, Chennai, Kolkata): Up to INR 4,500 per night.",
                        "Tier-2 Cities (Pune, Ahmedabad, Chandigarh, Kochi, Jaipur, etc.): Up to INR 3,000 per night.",
                        "Tier-3 and other locations: Up to INR 2,200 per night.",
                        "Complimentary hotel breakfast should be opted for during room reservations."
                    ],
                    "callout": "Hotel tariff limit is INR 4,500/night for Tier-1 cities and INR 3,000/night for Tier-2 cities."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Daily Per Diem & Incidentals",
                    "paragraphs": [
                        "Employees traveling for official purposes receive a daily per diem allowance to cover meals and local incidental transit expenses without needing individual itemized grocery receipts.",
                        "Domestic Tier-1 daily per diem is INR 1,200 per full calendar day. Domestic Tier-2 per diem is INR 900 per day.",
                        "International travel per diem is USD 75 per day (or equivalent local currency in the destination country)."
                    ],
                    "callout": "Daily per diem is INR 1,200/day for Tier-1 and INR 900/day for Tier-2 domestic travel."
                }
            ]
        }
    ]
    build_pdf("travel_policy.pdf", travel_pages, {
        "title": "Corporate Travel & Conveyance Policy",
        "code": "DOC-FIN-TRV-2026",
        "version": "2.4",
        "effective_date": "March 1, 2026",
        "department": "Finance & Administration",
        "owner": "Chief Financial Officer",
        "applicability": "Employees Traveling on Business"
    })

    # 5. reimbursement_policy.pdf (4 pages)
    reimbursement_pages = [
        {
            "sections": [
                {
                    "title": "1. Reimbursement Principles & Submission Timelines",
                    "paragraphs": [
                        "Roboserv 4i reimburses legitimate, necessary, and reasonable business expenses incurred in the performance of corporate duties.",
                        "All expense claims must be submitted via the Roboserv 4i Finance Portal within 30 days of the expense incurring.",
                        "Claims submitted after 45 days will be deemed void unless exceptional dispensation is granted by the CFO."
                    ],
                    "bullets": [
                        "Original digital invoices or clear photo receipts bearing the vendor's GSTIN are mandatory.",
                        "Personal expenses (alcohol, family dining, entertainment) are strictly non-reimbursable."
                    ],
                    "callout": "Reimbursement claims must be submitted within 30 days with valid GST invoices."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Broadband & Mobile Phone Reimbursement",
                    "paragraphs": [
                        "To facilitate uninterrupted connectivity, Roboserv 4i provides monthly telecommunications reimbursement.",
                        "Broadband Reimbursement: Full-time employees working in hybrid or remote modes are entitled to claim broadband internet expenses up to INR 1,500 per month.",
                        "Mobile Phone Plan: Designated project leads, managers, on-call support engineers, and client engagement managers may claim postpaid mobile expenses up to INR 800 per month."
                    ],
                    "callout": "Monthly broadband reimbursement is up to INR 1,500. Eligible mobile bill reimbursement is up to INR 800/month."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Professional Certification & Learning Allowance",
                    "paragraphs": [
                        "Continuous learning and technical mastery are core cultural pillars at Roboserv 4i.",
                        "Each confirmed full-time employee is allotted an annual professional certification budget of up to INR 50,000 per financial year.",
                        "Pre-approved technical credentials include certifications in Google Cloud Platform (GCP), AWS, Azure, LangChain, Machine Learning, and Project Management (PMP)."
                    ],
                    "bullets": [
                        "Prior written approval from the Practice Head is required prior to exam registration.",
                        "Reimbursement is processed upon uploading the official passing certificate and payment receipt."
                    ],
                    "callout": "Annual learning and certification reimbursement allowance is up to INR 50,000 per financial year."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Health & Wellness Reimbursement",
                    "paragraphs": [
                        "Roboserv 4i champions holistic health and wellness for employees.",
                        "Employees are eligible for an annual health & wellness reimbursement of up to INR 12,000 per calendar year.",
                        "Eligible expenses include memberships for gyms, yoga studios, swimming pools, sports clubs, or preventive annual health checkups for the employee."
                    ],
                    "callout": "Annual health & fitness reimbursement is up to INR 12,000."
                }
            ]
        }
    ]
    build_pdf("reimbursement_policy.pdf", reimbursement_pages, {
        "title": "Employee Expense Reimbursement Policy",
        "code": "DOC-FIN-RMB-2026",
        "version": "2.0",
        "effective_date": "January 15, 2026",
        "department": "Finance & Accounts",
        "owner": "Head of Corporate Finance",
        "applicability": "All Regular Employees"
    })

    # 6. employee_benefits.pdf (5 pages)
    benefits_pages = [
        {
            "sections": [
                {
                    "title": "1. Group Medical Insurance (Mediclaim)",
                    "paragraphs": [
                        "Roboserv 4i provides comprehensive Group Health Insurance coverage to safeguard employees and their families against medical exigencies.",
                        "The company provides a base floater coverage of INR 500,000 per annum covering the employee, legal spouse, and up to 2 dependent children.",
                        "Coverage includes cashless hospitalization across 8,000+ accredited network hospitals nationwide, pre-hospitalization expenses up to 30 days, and post-hospitalization expenses up to 60 days."
                    ],
                    "bullets": [
                        "Maternity hospitalization cover is included up to INR 75,000 for normal delivery and INR 100,000 for C-section.",
                        "Optional voluntary top-up coverage up to INR 1,000,000 is available at subsidized corporate group premiums."
                    ],
                    "callout": "Base Group Mediclaim insurance coverage is INR 500,000 for employee, spouse, and up to 2 children."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Term Life Insurance & Personal Accident Cover",
                    "paragraphs": [
                        "To provide financial security to employees' loved ones, Roboserv 4i sponsors 100% of the premium for Group Term Life Insurance.",
                        "The term life insurance policy provides a lump-sum death benefit equal to 3 times (3x) the employee's annual Cost-to-Company (CTC).",
                        "In addition, Group Personal Accident insurance provides financial compensation up to INR 2,500,000 in the event of permanent or partial disability resulting from an accident."
                    ],
                    "callout": "Life insurance coverage equals 3x annual CTC. Personal accident coverage is up to INR 2,500,000."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Retirement & Long-Term Financial Benefits",
                    "paragraphs": [
                        "Roboserv 4i complies fully with all statutory retirement security mandates in India.",
                        "Provident Fund (PF): 12% matching contribution under the Employees' Provident Fund Organization (EPFO) regulations.",
                        "Gratuity: Payable under the Payment of Gratuity Act, 1972, upon completion of at least 5 continuous years of service, calculated as 15 days of last drawn basic salary for each completed year of service."
                    ],
                    "bullets": [
                        "Voluntary Provident Fund (VPF) options are available for employees wishing to increase tax-advantaged savings.",
                        "National Pension Scheme (NPS) corporate tier integration is supported under Section 80CCD(2)."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Employee Assistance Program (EAP) & Mental Health",
                    "paragraphs": [
                        "Roboserv 4i has partnered with leading mental healthcare providers to offer a 24x7 confidential Employee Assistance Program (EAP).",
                        "Employees and their immediate family members can access up to 6 free one-on-one sessions per year with licensed clinical psychologists, counsellors, and financial wellbeing consultants."
                    ],
                    "bullets": [
                        "All discussions are strictly confidential between the employee and the provider; no records are shared with Roboserv 4i HR or management.",
                        "Assistance spans work stress, grief, anxiety, relationship counseling, and parenting guidance."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "5. Annual Performance Bonus & Rewards Cycle",
                    "paragraphs": [
                        "Roboserv 4i recognizes and rewards high performance, innovation, and leadership.",
                        "Annual performance appraisals occur during the fourth quarter (February-March), with revised compensation and annual bonus payouts disbursed in the April payroll.",
                        "Bonus pools are determined based on company financial targets (60% weightage) and individual goal achievement (40% weightage)."
                    ],
                    "bullets": [
                        "Spot Awards: Cash recognition of INR 10,000 to INR 25,000 for exceptional project delivery.",
                        "Long Service Awards: Commendations and gift milestones at 3, 5, and 10 years of service."
                    ]
                }
            ]
        }
    ]
    build_pdf("employee_benefits.pdf", benefits_pages, {
        "title": "Corporate Employee Benefits Handbook",
        "code": "DOC-HR-BEN-2026",
        "version": "3.2",
        "effective_date": "January 1, 2026",
        "department": "Total Rewards & HR",
        "owner": "Head of Rewards & Welfare",
        "applicability": "All Full-Time Employees"
    })

    # 7. code_of_conduct.pdf (5 pages)
    code_pages = [
        {
            "sections": [
                {
                    "title": "1. Corporate Values & Workplace Principles",
                    "paragraphs": [
                        "At Roboserv 4i Private Limited, our mission is built upon five pillars: Integrity, Innovation, Respect, Transparency, and Customer Success.",
                        "We are committed to providing an inclusive, safe, and professional work environment free from discrimination, harassment, and bias based on caste, religion, gender, sexual orientation, disability, or marital status."
                    ],
                    "bullets": [
                        "Treat all colleagues, clients, and partners with dignity and professional courtesy.",
                        "Maintain highest standards of academic and technological integrity in research and software development."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Prevention of Sexual Harassment (POSH)",
                    "paragraphs": [
                        "Roboserv 4i enforces zero tolerance for sexual harassment under the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013.",
                        "An Internal Complaints Committee (ICC) headed by an external female presiding officer is constituted to investigate grievances with absolute confidentiality.",
                        "Inquiries are conducted and completed within a maximum timeframe of 90 days from the filing of the complaint."
                    ],
                    "callout": "Roboserv 4i maintains zero tolerance for sexual harassment. POSH inquiries are strictly concluded within 90 days."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Conflict of Interest & Moonlighting Policy",
                    "paragraphs": [
                        "Roboserv 4i employees must devote their full business time, attention, and technical skills to the business of the company.",
                        "Moonlighting (dual employment, commercial freelancing, running external commercial software ventures, or consulting for third-party commercial entities) is strictly prohibited without prior written approval from the Chief People Officer.",
                        "Passive personal investments in publicly traded equity or mutual funds are permitted provided they do not conflict with client confidentiality."
                    ],
                    "callout": "Moonlighting and dual employment are strictly forbidden without prior written consent from HR leadership."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Anti-Bribery, Gifts & Corporate Hospitality",
                    "paragraphs": [
                        "Roboserv 4i conducts business ethically and in full compliance with all domestic and international anti-corruption laws.",
                        "Employees must never accept or solicit personal gifts, lavish hospitality, gift cards, or cash from vendors, clients, or partners.",
                        "Modest customary promotional items (pens, notepads, diaries, calendars) with an aggregate market value not exceeding INR 2,000 are permissible during festive seasons."
                    ],
                    "callout": "Acceptance of gifts exceeding INR 2,000 in value is strictly prohibited."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "5. Whistleblower Protection Policy",
                    "paragraphs": [
                        "Roboserv 4i provides a protected, confidential channel for employees to report unlawful conduct, fraud, safety violations, or unethical behavior.",
                        "Reports may be submitted via email to ethics@roboserv4i.com or to the Chairman of the Audit Committee.",
                        "Roboserv 4i strictly forbids any form of retaliation against an employee who reports a suspected violation in good faith."
                    ],
                    "callout": "Confidential whistleblower channel: ethics@roboserv4i.com. Retaliation against whistleblowers is grounds for immediate termination."
                }
            ]
        }
    ]
    build_pdf("code_of_conduct.pdf", code_pages, {
        "title": "Code of Business Conduct & Ethics",
        "code": "DOC-LEGAL-COC-2026",
        "version": "4.0",
        "effective_date": "January 1, 2026",
        "department": "Legal & Compliance",
        "owner": "General Counsel & Chief Ethics Officer",
        "applicability": "All Employees, Officers & Contractors"
    })

    # 8. information_security_policy.pdf (4 pages)
    infosec_pages = [
        {
            "sections": [
                {
                    "title": "1. Password & Access Control Standards",
                    "paragraphs": [
                        "Information security is the collective responsibility of every employee at Roboserv 4i Private Limited.",
                        "All enterprise passwords must be at least 12 characters in length, containing uppercase letters, lowercase letters, numbers, and special symbols.",
                        "Passwords must be updated every 90 days. Reusing the previous 5 passwords is prohibited.",
                        "Multi-Factor Authentication (MFA) via enterprise authenticators (Duo or Google Authenticator) is mandatory across all cloud and on-premise systems."
                    ],
                    "callout": "Passwords must have minimum 12 characters, rotated every 90 days. MFA is mandatory."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Data Classification & Protection Tiers",
                    "paragraphs": [
                        "All electronic documents, source code repositories, and datasets are classified into four tiers:",
                        "1. Public: Approved press releases and marketing collateral.",
                        "2. Internal: General company communications, org charts, internal guidelines.",
                        "3. Confidential: Intellectual property, proprietary source code, financial reports, HR compensation records.",
                        "4. Highly Restricted: Customer PII (Personally Identifiable Information), API keys, cryptographic credentials, production database backups."
                    ],
                    "bullets": [
                        "Highly Restricted data must be encrypted with AES-256 at rest and TLS 1.3 in transit.",
                        "Production data must NEVER be downloaded to local developer laptops."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Clean Desk & Removable Storage Policy",
                    "paragraphs": [
                        "To prevent physical data exfiltration and visual snooping, Roboserv 4i enforces a strict Clean Desk and Clean Screen rule.",
                        "Employees must lock their screens (Win+L / Cmd+Ctrl+Q) whenever leaving their workstation. Automatic lock activates after 2 minutes of idle time.",
                        "External USB flash drives, memory sticks, and portable external hard disks are blocked by endpoint device control policies. Transferring data via personal cloud storage (Google Drive, Dropbox) is blocked."
                    ],
                    "callout": "Clean screen auto-lock at 2 minutes. Removable USB drives and personal cloud storage are disabled."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Security Incident Reporting & Phishing",
                    "paragraphs": [
                        "Early detection and reporting are critical to mitigating cyber threats and safeguarding client data.",
                        "Any suspected phishing email, anomalous system behavior, lost badge, or stolen laptop must be reported immediately to security@roboserv4i.com within 60 minutes of discovery.",
                        "The InfoSec Incident Response Team operates 24x7 to isolate endpoints and prevent lateral threat movement."
                    ],
                    "callout": "All security incidents and lost hardware must be reported to security@roboserv4i.com within 60 minutes."
                }
            ]
        }
    ]
    build_pdf("information_security_policy.pdf", infosec_pages, {
        "title": "Information Security & Data Protection Policy",
        "code": "DOC-SEC-ISP-2026",
        "version": "2.2",
        "effective_date": "January 1, 2026",
        "department": "Information Security (InfoSec)",
        "owner": "Chief Information Security Officer (CISO)",
        "applicability": "All Staff with System Access"
    })

    # 9. holiday_policy.pdf (3 pages)
    holiday_pages = [
        {
            "sections": [
                {
                    "title": "1. Corporate Holiday Structure",
                    "paragraphs": [
                        "Roboserv 4i Private Limited publishes an annual official holiday schedule for each calendar year.",
                        "The holiday entitlement consists of 10 Mandatory Public Holidays and 2 Optional / Restricted Holidays (RH) per year, totaling 12 official paid holidays."
                    ],
                    "bullets": [
                        "Mandatory holidays are observed across all regional development centers.",
                        "Optional holidays allow employees to celebrate cultural, religious, or personal festivals of significance."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Annual Mandatory Holidays (10 Days)",
                    "paragraphs": [
                        "Roboserv 4i observes the following 10 mandatory public holidays in calendar year 2026:"
                    ],
                    "bullets": [
                        "1. New Year's Day — January 1, 2026",
                        "2. Republic Day — January 26, 2026",
                        "3. May Day / International Labour Day — May 1, 2026",
                        "4. Independence Day — August 15, 2026",
                        "5. Gandhi Jayanti — October 2, 2026",
                        "6. Dussehra / Vijayadashami — October 20, 2026",
                        "7. Diwali / Deepavali — November 8, 2026",
                        "8. Kannada Rajyotsava / State Day — November 1, 2026",
                        "9. Eid-ul-Fitr — April 10, 2026 (subject to moon sighting)",
                        "10. Christmas Day — December 25, 2026"
                    ],
                    "callout": "Roboserv 4i observes 10 mandatory paid public holidays and 2 optional restricted holidays per year."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Optional / Restricted Holidays (RH)",
                    "paragraphs": [
                        "Employees are entitled to select 2 Optional Holidays per year from the designated RH roster:",
                        "Options include Holi, Good Friday, Makar Sankranti/Pongal, Onam, Guru Nanak Jayanti, and Muharram.",
                        "Optional holiday requests must be submitted at least 5 business days in advance through the Enterprise Portal and approved by the project lead to ensure team coverage."
                    ],
                    "callout": "Optional holidays require at least 5 business days advance application."
                }
            ]
        }
    ]
    build_pdf("holiday_policy.pdf", holiday_pages, {
        "title": "Corporate Holiday & Calendar Policy",
        "code": "DOC-HR-HOL-2026",
        "version": "2.0",
        "effective_date": "January 1, 2026",
        "department": "Human Resources",
        "owner": "Talent Operations Lead",
        "applicability": "All Roboserv 4i Employees"
    })

    # 10. hr_handbook.pdf (5 pages)
    handbook_pages = [
        {
            "sections": [
                {
                    "title": "1. Welcome & About Roboserv 4i Private Limited",
                    "paragraphs": [
                        "Welcome to Roboserv 4i Private Limited! Founded in 2018, Roboserv 4i is an industry-leading software and artificial intelligence enterprise empowering global clients with generative AI, cloud transformation, and intelligent automation solutions.",
                        "With delivery headquarters in Bengaluru and regional centers in Pune and Hyderabad, Roboserv 4i is home to over 1,500 dedicated technologists, data scientists, and business consultants."
                    ],
                    "bullets": [
                        "This handbook serves as the overarching guide to employment terms, company culture, and career progression.",
                        "Detailed policies on leaves, travel, and benefits supplement this handbook."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "2. Probation & Confirmation Process",
                    "paragraphs": [
                        "All new lateral and campus recruits undergo a standard probation period of 6 months from their joining date.",
                        "At 5.5 months, the reporting manager completes a formal performance review. Upon meeting key deliverables, HR issues a formal Letter of Confirmation."
                    ],
                    "bullets": [
                        "If milestones require further stabilization, probation may be extended once for up to 3 additional months.",
                        "Notice period during probation is 30 days for either party."
                    ],
                    "callout": "Probation period is 6 months with formal evaluation at 5.5 months. Notice period during probation is 30 days."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "3. Notice Period & Separation Protocol",
                    "paragraphs": [
                        "For confirmed full-time employees, the contractual notice period is 60 calendar days upon submission of formal resignation on the HRMS portal.",
                        "Notice buyout or early release is subject to project handover requirements and approval from the Delivery Head and Head of HR.",
                        "Full and Final (F&F) settlement, along with service certificates and encashment of accumulated paid leave (up to 45 days), is processed within 30 working days of the last working day."
                    ],
                    "callout": "Notice period for confirmed employees is 60 days. Full and Final settlement is executed within 30 working days."
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "4. Performance Management & OKR System",
                    "paragraphs": [
                        "Roboserv 4i follows an agile Objectives and Key Results (OKR) framework aligned quarterly.",
                        "Performance ratings are evaluated annually on a 5-point scale: 1 (Unsatisfactory), 2 (Needs Improvement), 3 (Meets Expectations), 4 (Exceeds Expectations), 5 (Outstanding).",
                        "Ratings directly determine annual merit increments, promotion eligibility, and performance bonus allocation."
                    ]
                }
            ]
        },
        {
            "sections": [
                {
                    "title": "5. Employee Grievance Redressal Matrix",
                    "paragraphs": [
                        "Roboserv 4i promotes an open-door policy where constructive concerns are addressed swiftly and fairly.",
                        "Employees may escalate unresolved grievances through our structured 3-tier escalation matrix:",
                        "• Tier 1: Immediate Project Manager or assigned HR Business Partner (HRBP). Response within 3 working days.",
                        "• Tier 2: Department Head or Head of Human Resources. Response within 5 working days.",
                        "• Tier 3: Grievance Redressal Committee comprising Executive Leadership. Final decision within 7 working days."
                    ],
                    "callout": "Three-tier grievance escalation matrix guarantees swift resolution within 7 working days."
                }
            ]
        }
    ]
    build_pdf("hr_handbook.pdf", handbook_pages, {
        "title": "Employee Handbook & Organizational Guidelines",
        "code": "DOC-HR-HDB-2026",
        "version": "5.0",
        "effective_date": "January 1, 2026",
        "department": "Human Resources",
        "owner": "Chief People Officer",
        "applicability": "All Roboserv 4i Personnel"
    })

    print("All 10 policy PDF documents generated successfully in data/documents/")


if __name__ == "__main__":
    generate_all_documents()
