from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .models import Event, TicketBooking
from .serializers import EventSerializer, TicketBookingSerializer
from .tasks import generate_receipt_and_send_email

class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class BookTicketView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = TicketBookingSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        event_id = serializer.validated_data['event'].id
        quantity = serializer.validated_data['quantity']
        user_email = serializer.validated_data['user_email']

        # Wrap database operations in an atomic transaction to handle race conditions
        with transaction.atomic():
            # Lock the row using select_for_update() to prevent double-booking concurrent issues
            event = Event.objects.select_for_update().get(id=event_id)
            
            # Re-verify stock inside the lock
            if event.available_tickets < quantity:
                return Response(
                    {"error": "Tickets sold out during checkout process."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Deduct tickets & update DB
            event.available_tickets -= quantity
            event.save()

            total_cost = event.price_per_ticket * quantity

            # Save initial pending booking
            booking = TicketBooking.objects.create(
                event=event,
                user_email=user_email,
                quantity=quantity,
                total_cost=total_cost,
                status='PENDING'
            )

        # Trigger Celery task asynchronously outside the database lock
        generate_receipt_and_send_email.delay(booking.id)

        response_serializer = TicketBookingSerializer(booking)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)