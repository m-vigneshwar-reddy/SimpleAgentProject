"""
Export utilities for travel plans
Supports: PDF, Excel (XLSX), Word (DOCX), JSON, iCal
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
import json


def export_to_pdf(plan, filename="travel_itinerary.pdf"):
    """Export travel plan to PDF"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    memory = plan.get('memory', {})
    destination = memory.get('destination', 'Unknown')
    days = memory.get('days', 0)
    
    story.append(Paragraph(f"Travel Itinerary: {destination}", title_style))
    story.append(Paragraph(f"{days}-Day Trip", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    # Budget Overview
    story.append(Paragraph("Budget Overview", styles['Heading2']))
    budget = plan.get('budget_breakdown', {})
    
    budget_data = [
        ['Category', 'Amount (€)'],
        ['Total Budget', f"€{budget.get('total_budget', 0):.2f}"],
        ['Accommodation', f"€{budget.get('accommodation', 0):.2f}"],
        ['Food & Dining', f"€{budget.get('food', 0):.2f}"],
        ['Activities', f"€{budget.get('activities', 0):.2f}"],
        ['Transport', f"€{budget.get('transport', 0):.2f}"],
        ['Miscellaneous', f"€{budget.get('miscellaneous', 0):.2f}"],
    ]
    
    budget_table = Table(budget_data, colWidths=[3*inch, 2*inch])
    budget_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(budget_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Hotels
    story.append(Paragraph("Recommended Hotels", styles['Heading2']))
    hotels = plan.get('hotels', [])
    
    for hotel in hotels:
        hotel_text = f"<b>{hotel.get('name', 'N/A')}</b> - €{hotel.get('price', 0):.2f}/night<br/>"
        hotel_text += f"Location: {hotel.get('area', 'N/A')}<br/>"
        hotel_text += f"Rating: {'⭐' * int(hotel.get('rating', 0))}<br/>"
        hotel_text += f"{hotel.get('description', '')}"
        story.append(Paragraph(hotel_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Daily Itinerary
    story.append(PageBreak())
    story.append(Paragraph("Daily Itinerary", styles['Heading2']))
    
    itinerary = plan.get('itinerary', {})
    for day_name, day_plan in itinerary.items():
        story.append(Paragraph(day_name, styles['Heading3']))
        
        # Create detailed table for the day
        day_data = [['Time', 'Place & Details']]
        
        for period in ['morning', 'afternoon', 'evening']:
            activity = day_plan.get(period, {})
            
            # Build detailed info text
            details = []
            details.append(f"<b>{activity.get('place_name', 'N/A')}</b>")
            details.append(f"Activity: {activity.get('activity', 'N/A')}")
            details.append(f"Address: {activity.get('address', 'N/A')}")
            details.append(f"Hours: {activity.get('opening_hours', 'Check locally')}")
            details.append(f"Cost: €{activity.get('cost', 0):.2f}")
            details.append(f"Duration: {activity.get('duration', 'N/A')}")
            details.append(f"Rating: {'⭐' * int(activity.get('rating', 0))}")
            if activity.get('booking_required'):
                details.append("⚠️ Booking recommended")
            
            details_text = "<br/>".join(details)
            
            day_data.append([
                period.capitalize(),
                Paragraph(details_text, styles['Normal'])
            ])
        
        day_table = Table(day_data, colWidths=[1.5*inch, 4.5*inch])
        day_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E3F2FD')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(day_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Travel Tips
    story.append(PageBreak())
    story.append(Paragraph("Important Travel Tips", styles['Heading2']))
    
    tips = plan.get('tips', [])
    for i, tip in enumerate(tips, 1):
        story.append(Paragraph(f"{i}. {tip}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(story)
    return filename


def export_to_excel(plan, filename="travel_itinerary.xlsx"):
    """Export travel plan to Excel"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return None
    
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Sheet 1: Overview
    ws_overview = wb.create_sheet("Overview")
    memory = plan.get('memory', {})
    budget = plan.get('budget_breakdown', {})
    
    # Headers
    header_fill = PatternFill(start_color="1E88E5", end_color="1E88E5", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=14)
    
    ws_overview['A1'] = "Travel Plan Overview"
    ws_overview['A1'].font = Font(bold=True, size=16, color="1E88E5")
    
    # Trip Details
    ws_overview['A3'] = "Destination:"
    ws_overview['B3'] = memory.get('destination', 'N/A')
    ws_overview['A4'] = "Duration:"
    ws_overview['B4'] = f"{memory.get('days', 0)} days"
    ws_overview['A5'] = "Purpose:"
    ws_overview['B5'] = memory.get('purpose', 'N/A')
    ws_overview['A6'] = "Style:"
    ws_overview['B6'] = memory.get('style', 'N/A')
    
    # Budget Breakdown
    ws_overview['A8'] = "Budget Breakdown"
    ws_overview['A8'].font = header_font
    ws_overview['A8'].fill = header_fill
    ws_overview['B8'].fill = header_fill
    
    budget_rows = [
        ("Total Budget", budget.get('total_budget', 0)),
        ("Accommodation", budget.get('accommodation', 0)),
        ("Food & Dining", budget.get('food', 0)),
        ("Activities", budget.get('activities', 0)),
        ("Transport", budget.get('transport', 0)),
        ("Miscellaneous", budget.get('miscellaneous', 0)),
    ]
    
    row = 9
    for label, amount in budget_rows:
        ws_overview[f'A{row}'] = label
        ws_overview[f'B{row}'] = f"€{amount:.2f}"
        row += 1
    
    # Sheet 2: Itinerary
    ws_itinerary = wb.create_sheet("Daily Itinerary")
    
    ws_itinerary['A1'] = "Daily Itinerary"
    ws_itinerary['A1'].font = Font(bold=True, size=16, color="1E88E5")
    
    # Headers
    headers = ['Day', 'Time', 'Place Name', 'Activity', 'Address', 'Hours', 'Cost (€)', 'Rating', 'Booking Required']
    for col, header in enumerate(headers, 1):
        cell = ws_itinerary.cell(row=3, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    # Itinerary data
    row = 4
    itinerary = plan.get('itinerary', {})
    
    for day_name, day_plan in itinerary.items():
        for period in ['morning', 'afternoon', 'evening']:
            activity = day_plan.get(period, {})
            
            ws_itinerary.cell(row=row, column=1).value = day_name
            ws_itinerary.cell(row=row, column=2).value = period.capitalize()
            ws_itinerary.cell(row=row, column=3).value = activity.get('place_name', 'N/A')
            ws_itinerary.cell(row=row, column=4).value = activity.get('activity', 'N/A')
            ws_itinerary.cell(row=row, column=5).value = activity.get('address', 'N/A')
            ws_itinerary.cell(row=row, column=6).value = activity.get('opening_hours', 'N/A')
            ws_itinerary.cell(row=row, column=7).value = activity.get('cost', 0)
            ws_itinerary.cell(row=row, column=8).value = activity.get('rating', 0)
            ws_itinerary.cell(row=row, column=9).value = "Yes" if activity.get('booking_required') else "No"
            
            row += 1
    
    # Adjust column widths
    ws_itinerary.column_dimensions['A'].width = 12
    ws_itinerary.column_dimensions['B'].width = 12
    ws_itinerary.column_dimensions['C'].width = 30
    ws_itinerary.column_dimensions['D'].width = 25
    ws_itinerary.column_dimensions['E'].width = 25
    ws_itinerary.column_dimensions['F'].width = 20
    ws_itinerary.column_dimensions['G'].width = 10
    ws_itinerary.column_dimensions['H'].width = 10
    ws_itinerary.column_dimensions['I'].width = 15
    
    # Sheet 3: Hotels
    ws_hotels = wb.create_sheet("Hotels")
    ws_hotels['A1'] = "Hotel Recommendations"
    ws_hotels['A1'].font = Font(bold=True, size=16, color="1E88E5")
    
    hotel_headers = ['Hotel Name', 'Price/Night (€)', 'Area', 'Rating', 'Description']
    for col, header in enumerate(hotel_headers, 1):
        cell = ws_hotels.cell(row=3, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
    
    hotels = plan.get('hotels', [])
    for row, hotel in enumerate(hotels, 4):
        ws_hotels.cell(row=row, column=1).value = hotel.get('name', 'N/A')
        ws_hotels.cell(row=row, column=2).value = hotel.get('price', 0)
        ws_hotels.cell(row=row, column=3).value = hotel.get('area', 'N/A')
        ws_hotels.cell(row=row, column=4).value = hotel.get('rating', 0)
        ws_hotels.cell(row=row, column=5).value = hotel.get('description', 'N/A')
    
    ws_hotels.column_dimensions['A'].width = 25
    ws_hotels.column_dimensions['B'].width = 15
    ws_hotels.column_dimensions['C'].width = 20
    ws_hotels.column_dimensions['D'].width = 10
    ws_hotels.column_dimensions['E'].width = 40
    
    # Sheet 4: Packing List
    ws_packing = wb.create_sheet("Packing List")
    ws_packing['A1'] = "Packing List"
    ws_packing['A1'].font = Font(bold=True, size=16, color="1E88E5")
    
    packing_list = plan.get('packing_list', {})
    row = 3
    
    for category, items in packing_list.items():
        ws_packing.cell(row=row, column=1).value = category
        ws_packing.cell(row=row, column=1).font = Font(bold=True)
        row += 1
        
        for item in items:
            ws_packing.cell(row=row, column=1).value = f"  • {item}"
            row += 1
        
        row += 1
    
    ws_packing.column_dimensions['A'].width = 50
    
    # Save
    wb.save(filename)
    return filename


def export_to_json(plan, filename="travel_itinerary.json"):
    """Export travel plan to JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    return filename


def export_to_ical(plan, filename="travel_itinerary.ics", start_date=None):
    """Export travel plan to iCalendar format"""
    if start_date is None:
        start_date = datetime.now().date()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    
    ical_content = ["BEGIN:VCALENDAR"]
    ical_content.append("VERSION:2.0")
    ical_content.append("PRODID:-//AI Travel Planner//EN")
    ical_content.append(f"X-WR-CALNAME:Trip to {plan.get('memory', {}).get('destination', 'Unknown')}")
    
    itinerary = plan.get('itinerary', {})
    
    for day_idx, (day_name, day_plan) in enumerate(itinerary.items()):
        current_date = start_date + timedelta(days=day_idx)
        
        for period, time_start in [('morning', '09:00'), ('afternoon', '14:00'), ('evening', '19:00')]:
            activity = day_plan.get(period, {})
            place_name = activity.get('place_name', 'Activity')
            activity_type = activity.get('activity', 'Free time')
            
            if place_name and place_name != 'Free Time':
                ical_content.append("BEGIN:VEVENT")
                ical_content.append(f"DTSTART:{current_date.strftime('%Y%m%d')}T{time_start.replace(':', '')}00")
                
                # Calculate end time (add duration)
                duration_hours = 2 if period == 'evening' else 3
                end_time_hour = int(time_start.split(':')[0]) + duration_hours
                ical_content.append(f"DTEND:{current_date.strftime('%Y%m%d')}T{end_time_hour:02d}0000")
                
                # Event title with place name
                ical_content.append(f"SUMMARY:{place_name}")
                
                # Description with all details
                description_parts = [
                    f"Activity: {activity_type}",
                    f"Address: {activity.get('address', 'N/A')}",
                    f"Hours: {activity.get('opening_hours', 'Check locally')}",
                    f"Cost: €{activity.get('cost', 0):.2f}",
                    f"Rating: {'⭐' * int(activity.get('rating', 0))}",
                    f"\\n{activity.get('description', '')}"
                ]
                if activity.get('booking_required'):
                    description_parts.append("\\n⚠️ BOOKING RECOMMENDED")
                
                ical_content.append(f"DESCRIPTION:{' - '.join(description_parts)}")
                
                # Location with address
                location = f"{place_name}, {activity.get('address', plan.get('memory', {}).get('destination', 'Unknown'))}"
                ical_content.append(f"LOCATION:{location}")
                
                ical_content.append(f"UID:{day_idx}-{period}@travelplanner.com")
                ical_content.append("END:VEVENT")
    
    ical_content.append("END:VCALENDAR")
    
    with open(filename, 'w') as f:
        f.write('\n'.join(ical_content))
    
    return filename


def generate_qr_code(text, filename="itinerary_qr.png"):
    """Generate QR code for itinerary sharing"""
    try:
        import qrcode
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)
        return filename
    except ImportError:
        return None
