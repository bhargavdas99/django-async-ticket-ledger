from rest_framework import serializers
from .models import Event, TicketBooking

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'total_tickets', 'available_tickets', 'price_per_ticket']


class TicketBookingSerializer(serializers.ModelSerializer):
    event_details = EventSerializer(source='event', read_only=True)

    class Meta:
        model = TicketBooking
        fields = ['id', 'event', 'event_details', 'user_email', 'quantity', 'total_cost', 'status', 'created_at']
        read_only_fields = ['total_cost', 'status', 'created_at']

    def validate(self, attrs):
        event = attrs['event']
        quantity = attrs['quantity']

        # Business Rule 1: Check availability
        if event.available_tickets < quantity:
            raise serializers.ValidationError({
                "quantity": f"Only {event.available_tickets} tickets left for this event."
            })
        
        return attrs