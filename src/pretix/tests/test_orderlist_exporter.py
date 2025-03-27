import pytest
from django.utils.timezone import now
from pretix.base.models import Event, Order, Organizer, SalesChannel
from pretix.base.exporters.orderlist import OrderListExporter
from django import forms
from django_scopes import scopes_disabled

@pytest.fixture

def event():
    organizer = Organizer.objects.create(name='Test Organizer', slug='test')
    event = Event.objects.create(
        organizer=organizer,
        name='Test Event',
        slug='test',
        date_from=now(),
        live=True
    )
    return event

@pytest.fixture

def order(event):
    organizer = event.organizer
    with scopes_disabled():
        sales_channel, created = SalesChannel.objects.get_or_create(
            organizer=organizer,
            identifier='web',
            defaults={
                'label': 'Web',
                'type': 'web',
                'position': 0
            }
        )
    order = Order.objects.create(
        code='TEST1234',
        event=event,
        email='test@example.com',
        status=Order.STATUS_PAID,
        datetime=now(),
        total=100,
        sales_channel=sales_channel
    )
    return order

@pytest.mark.django_db

def test_order_list_exporter(event, order):
    with scopes_disabled():
        exporter = OrderListExporter(event.organizer, event)
        form_data = {
            'columns': ['order_code', 'email', 'order_total'],
            'paid_only': True,
            'include_payment_amounts': False,
            'group_multiple_choice': False,
            'date_range': None,
            'event_date_range': None
        }
        headers = next(exporter.iterate_orders(form_data))
        expected_headers = ['Order code', 'Email', 'Order total']
        for header in expected_headers:
            assert header in headers

        rows = [row for row in exporter.iterate_orders(form_data) if not isinstance(row, exporter.ProgressSetTotal)]
        assert len(rows) == 2  # One for headers, one for the order

        # Extract only the selected columns from the data row
        data_row = rows[1]
        selected_data = [data_row[headers.index(header)] for header in expected_headers]
        assert selected_data == ['TEST1234', 'test@example.com', 100]
