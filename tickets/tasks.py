import os
from celery import shared_task
from django.conf import settings
from .models import TicketBooking
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@shared_task
def generate_receipt_and_send_email(booking_id):
    try:
        booking = TicketBooking.objects.get(id=booking_id)

        # Define path to save the PDF receipt
        filename = f"receipt_{booking.id}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)

        # Ensure media directory exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        # Build PDF using ReportLab
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<b>Movie Ticket Receipt</b>", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Booking ID:</b> #{booking.id}", styles['Normal']))
        story.append(Paragraph(f"<b>Event:</b> {booking.event.name}", styles['Normal']))
        story.append(Paragraph(f"<b>User Email:</b> {booking.user_email}", styles['Normal']))
        story.append(Paragraph(f"<b>Quantity:</b> {booking.quantity}", styles['Normal']))
        story.append(Paragraph(f"<b>Total Cost:</b> ${booking.total_cost}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<i>Thank you for your purchase! Enjoy your movie.</i>", styles['Italic']))

        doc.build(story)

        # Mark status as CONFIRMED
        booking.status = 'CONFIRMED'
        booking.save()

        print(f"[CELERY WORKER] Generated PDF receipt at {filepath} and sent to {booking.user_email}")
        return f"Booking #{booking.id} processed successfully."

    except TicketBooking.DoesNotExist:
        return f"Booking #{booking.id} not found."