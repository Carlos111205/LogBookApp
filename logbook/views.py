from io import BytesIO
import re
from pathlib import Path
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.shared import Inches, Mm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from .forms import LogEntryForm, ReportForm, SignUpForm, StudentProfileForm
from .models import LogEntry, StudentProfile

CREST_PATH = Path(__file__).resolve().parent.parent / "static" / "images" / "nust_crest.png"
LETTERHEAD = {
    "university": "NATIONAL UNIVERSITY OF SCIENCE AND TECHNOLOGY",
    "department": "COMPUTER SCIENCE DEPARTMENT",
    "address": "P.O. BOX AC 939, ASCOT, BULAWAYO, ZIMBABWE",
    "contact": "Tel: +263 292 282842 ext. 2332  |  Fax: +263 292 286803",
    "email": "Email: compscie@nust.ac.zw  |  Facebook: @NUST ZIM  |  X: @nustzim",
}

def signup(request):
    if request.user.is_authenticated: return redirect("dashboard")
    form=SignUpForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        user=form.save()
        login(request,user,backend="django.contrib.auth.backends.ModelBackend")
        StudentProfile.for_user(user)
        messages.success(request,"Your account is ready. Add your placement details to get started.")
        return redirect("profile")
    return render(request,"logbook/signup.html",{"form":form})

@login_required
def dashboard(request):
    p=StudentProfile.for_user(request.user); entries=LogEntry.objects.filter(user=request.user)
    return render(request,"logbook/dashboard.html",{"profile":p,"entries":entries[:5],"total":entries.count()})

@login_required
def profile(request):
    p=StudentProfile.for_user(request.user); form=StudentProfileForm(request.POST or None,instance=p)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Student and placement details saved."); return redirect("profile")
    return render(request,"logbook/profile.html",{"profile":p,"form":form})

@login_required
def logbook(request):
    form=LogEntryForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        entry=form.save(commit=False); entry.user=request.user; entry.save()
        messages.success(request,"Log book entry added."); return redirect("logbook")
    return render(request,"logbook/logbook.html",{"profile":StudentProfile.for_user(request.user),"form":form,"entries":LogEntry.objects.filter(user=request.user)})

@login_required
@require_POST
def delete_entry(request,pk):
    get_object_or_404(LogEntry,pk=pk,user=request.user).delete(); messages.success(request,"Entry deleted."); return redirect("logbook")

@login_required
def report(request):
    p=StudentProfile.for_user(request.user); form=ReportForm(request.POST or None,instance=p)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Report sections saved."); return redirect("report")
    return render(request,"logbook/report.html",{"profile":p,"form":form,"entry_count":LogEntry.objects.filter(user=request.user).count()})

def esc(value):
    # ReportLab's built-in Helvetica uses WinAnsi; normalize unsupported glyphs
    # so user-entered Unicode never makes PDF generation fail.
    value=str(value or "—").replace("·", "-").replace("—", "-").encode("cp1252", "replace").decode("cp1252")
    return value.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br/>")

def sections(p):
    return [("1. Introduction and objectives",p.objectives or "Add the purpose and objectives of your industrial attachment."),("2. Organisation background",p.organisation_background or "Add a brief background of the host organisation and department."),("3. Work completed and learning","This section is compiled from the dated log book entries below."),("4. Conclusion",p.conclusion or "Add your conclusion and overall assessment of the attachment."),("5. Recommendations",p.recommendations or "Add recommendations for the host organisation, university, or future students.")]

def add_docx_letterhead(section):
    section.header_distance=Inches(.22)
    table=section.header.add_table(rows=1,cols=2,width=Mm(170))
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    table.autofit=False
    table.columns[0].width=Mm(24); table.columns[1].width=Mm(146)
    logo_cell,text_cell=table.rows[0].cells
    logo_cell.width=Mm(24); text_cell.width=Mm(146)
    logo_cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    text_cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    image_para=logo_cell.paragraphs[0]; image_para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    image_para.add_run().add_picture(str(CREST_PATH),height=Mm(22))
    text_cell.text=""
    lines=((LETTERHEAD["university"],9,True),(LETTERHEAD["department"],11,True),(LETTERHEAD["address"],7,False),(LETTERHEAD["contact"],7,False),(LETTERHEAD["email"],7,False))
    for index,(value,size,bold) in enumerate(lines):
        para=text_cell.paragraphs[0] if index==0 else text_cell.add_paragraph()
        para.paragraph_format.space_before=Pt(0); para.paragraph_format.space_after=Pt(0); para.paragraph_format.line_spacing=1.0
        run=para.add_run(value); run.bold=bold; run.font.name="Aptos"; run.font.size=Pt(size); run.font.color.rgb=RGBColor(25,43,55)
    borders=OxmlElement("w:tblBorders")
    for edge in ("top","left","bottom","right","insideH","insideV"):
        item=OxmlElement(f"w:{edge}"); item.set(qn("w:val"),"nil"); borders.append(item)
    bottom=borders.find(qn("w:bottom")); bottom.set(qn("w:val"),"single"); bottom.set(qn("w:sz"),"8"); bottom.set(qn("w:space"),"5"); bottom.set(qn("w:color"),"9BAEB5")
    table._tbl.tblPr.append(borders)

def draw_pdf_letterhead(canvas,document):
    canvas.saveState()
    page_width,page_height=A4; left=18*mm
    canvas.drawImage(str(CREST_PATH),left,page_height-34*mm,width=18*mm,height=22*mm,preserveAspectRatio=True,anchor="c",mask="auto")
    x=left+24*mm; y=page_height-12*mm
    canvas.setFillColor(colors.HexColor("#192b37")); canvas.setFont("Helvetica-Bold",8); canvas.drawString(x,y,LETTERHEAD["university"])
    y-=5*mm; canvas.setFont("Helvetica-Bold",10); canvas.drawString(x,y,LETTERHEAD["department"])
    canvas.setFont("Helvetica",6.7)
    for line in (LETTERHEAD["address"],LETTERHEAD["contact"],LETTERHEAD["email"]):
        y-=4*mm; canvas.drawString(x,y,line)
    canvas.setStrokeColor(colors.HexColor("#9BAEB5")); canvas.setLineWidth(.7); canvas.line(left,page_height-38*mm,page_width-left,page_height-38*mm)
    canvas.restoreState()

def build_docx(p, entries, kind):
    doc=Document(); sec=doc.sections[0]; sec.page_width=Mm(210); sec.page_height=Mm(297)
    sec.top_margin=Mm(43); sec.bottom_margin=Mm(18); sec.left_margin=Mm(20); sec.right_margin=Mm(20)
    add_docx_letterhead(sec)
    doc.styles["Normal"].font.name="Aptos"; doc.styles["Normal"].font.size=Pt(10)
    title=doc.add_paragraph(); title.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=title.add_run((p.report_title if kind=="report" else "Industrial Attachment Log Book") or "Industrial Attachment Report"); r.bold=True; r.font.size=Pt(21); r.font.color.rgb=RGBColor(20,60,76)
    sub=doc.add_paragraph("BSc Computer Science · Industrial Attachment"); sub.alignment=WD_ALIGN_PARAGRAPH.CENTER
    detail=[("Student",p.student_name),("Student number",p.student_number),("Programme",p.programme),("Host organisation",p.organisation),("Department",p.department),("Workplace supervisor",p.workplace_supervisor),("Academic supervisor",p.academic_supervisor),("Attachment period",f"{p.start_date or '—'} to {p.end_date or '—'}")]
    table=doc.add_table(rows=0,cols=2); table.style="Light Shading Accent 1"
    for a,b in detail:
        c=table.add_row().cells; c[0].text=a; c[1].text=str(b or "—")
    ordered=list(entries.order_by("entry_date","pk"))
    if kind=="report":
        doc.add_page_break(); doc.add_heading("Report",1)
        for heading,body in sections(p):
            doc.add_heading(heading,2); doc.add_paragraph(body)
            if heading.startswith("3."):
                if not ordered: doc.add_paragraph("No log book entries have been recorded yet.")
                for e in ordered:
                    doc.add_heading(f"{e.entry_date:%d %B %Y} — {e.department or 'Work activities'}",3); doc.add_paragraph(e.activities)
                    for label,value in (("Skills learned",e.skills),("Challenges",e.challenges),("Reflection",e.reflection)):
                        if value: doc.add_paragraph(f"{label}: {value}")
    doc.add_page_break(); doc.add_heading("Industrial Attachment Log Book",1)
    if not ordered: doc.add_paragraph("No entries recorded.")
    for e in ordered:
        doc.add_heading(f"{e.entry_date:%A, %d %B %Y} · {e.department or 'Activities'}",2); doc.add_paragraph(e.activities)
        for label,value in (("Skills learned",e.skills),("Challenges",e.challenges),("Reflection",e.reflection)):
            if value: doc.add_paragraph(f"{label}: {value}")
    out=BytesIO(); doc.save(out); out.seek(0); return out

def build_pdf(p,entries,kind):
    out=BytesIO(); styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverX",parent=styles["Title"],fontSize=21,leading=25,textColor=colors.HexColor("#143c4c"),alignment=TA_CENTER,spaceAfter=10))
    styles.add(ParagraphStyle(name="UniX",parent=styles["Normal"],fontSize=12,leading=16,textColor=colors.HexColor("#147d76"),alignment=TA_CENTER,spaceAfter=14))
    styles.add(ParagraphStyle(name="BodyX",parent=styles["BodyText"],fontSize=9,leading=13,spaceAfter=5))
    ordered=list(entries.order_by("entry_date","pk")); title=(p.report_title if kind=="report" else "Industrial Attachment Log Book") or "Industrial Attachment Report"
    story=[Spacer(1,2*mm),Paragraph(esc(title),styles["CoverX"]),Paragraph("BSc Computer Science · Industrial Attachment",styles["UniX"]),Spacer(1,8*mm)]
    details=[("Student",p.student_name),("Student number",p.student_number),("Programme",p.programme),("Host organisation",p.organisation),("Department",p.department),("Workplace supervisor",p.workplace_supervisor),("Academic supervisor",p.academic_supervisor),("Attachment period",f"{p.start_date or '—'} to {p.end_date or '—'}")]
    data=[[Paragraph(f"<b>{esc(a)}</b>",styles["BodyX"]),Paragraph(esc(b),styles["BodyX"])] for a,b in details]
    t=Table(data,colWidths=[48*mm,112*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#eaf2f2")),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#d8e2e3")),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    if kind=="report":
        story += [PageBreak(),Paragraph("Report",styles["Heading1"])]
        for heading,body in sections(p):
            story += [Paragraph(esc(heading),styles["Heading2"]),Paragraph(esc(body),styles["BodyX"])]
            if heading.startswith("3."):
                if not ordered: story.append(Paragraph("No log book entries have been recorded yet.",styles["BodyX"]))
                for e in ordered:
                    story += [Paragraph(esc(f"{e.entry_date:%d %B %Y} — {e.department or 'Work activities'}"),styles["Heading3"]),Paragraph(esc(e.activities),styles["BodyX"])]
                    for label,value in (("Skills learned",e.skills),("Challenges",e.challenges),("Reflection",e.reflection)):
                        if value: story.append(Paragraph(f"<b>{label}:</b> {esc(value)}",styles["BodyX"]))
    story += [PageBreak(),Paragraph("Industrial Attachment Log Book",styles["Heading1"])]
    if not ordered: story.append(Paragraph("No entries recorded.",styles["BodyX"]))
    for e in ordered:
        story += [Paragraph(esc(f"{e.entry_date:%A, %d %B %Y} · {e.department or 'Activities'}"),styles["Heading2"]),Paragraph(esc(e.activities),styles["BodyX"])]
        for label,value in (("Skills learned",e.skills),("Challenges",e.challenges),("Reflection",e.reflection)):
            if value: story.append(Paragraph(f"<b>{label}:</b> {esc(value)}",styles["BodyX"]))
    SimpleDocTemplate(out,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=43*mm,bottomMargin=18*mm,title=title).build(story,onFirstPage=draw_pdf_letterhead,onLaterPages=draw_pdf_letterhead); out.seek(0); return out

@login_required
def download(request,kind,fmt):
    if kind not in {"logbook","report"} or fmt not in {"docx","pdf"}: raise Http404("Export not found")
    p=StudentProfile.for_user(request.user); entries=LogEntry.objects.filter(user=request.user)
    stream=build_docx(p,entries,kind) if fmt=="docx" else build_pdf(p,entries,kind)
    slug=re.sub(r"[^a-z0-9_-]+","_",p.student_name.lower()).strip("_") or "student"
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if fmt=="docx" else "application/pdf"
    response=HttpResponse(stream.getvalue(),content_type=mime); response["Content-Disposition"]=f'attachment; filename="{slug}_{kind}.{fmt}"'; return response
