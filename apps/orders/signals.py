import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order
from apps.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Order)
def store_original_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Order.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Order)
def trigger_order_notifications(sender, instance, created, **kwargs):
    if not instance.user:
        return

    # Status mapping for titles and messages
    status_mapping = {
        'pending': {
            'title': 'Order Received',
            'message': f'Thank you for your order! Your order #{instance.order_number} has been received and is pending approval.',
            'types': ['push', 'in_app', 'email']
        },
        'accepted': {
            'title': 'Order Accepted',
            'message': f'Great news! Your order #{instance.order_number} has been accepted by the shop.',
            'types': ['push', 'in_app']
        },
        'processing': {
            'title': 'Order Processing',
            'message': f'Your order #{instance.order_number} is now being processed.',
            'types': ['push', 'in_app']
        },
        'in_transit': {
            'title': 'Order In Transit',
            'message': f'Your order #{instance.order_number} is on the way! Our delivery agent is en route.',
            'types': ['push', 'in_app']
        },
        'delivered': {
            'title': 'Order Delivered',
            'message': f'Your order #{instance.order_number} has been delivered successfully. Thank you for shopping with us!',
            'types': ['push', 'in_app', 'email']
        },
        'cancelled': {
            'title': 'Order Cancelled',
            'message': f'Your order #{instance.order_number} has been cancelled.',
            'types': ['push', 'in_app', 'email']
        }
    }

    send_notif = False
    current_status = instance.status

    if created:
        send_notif = True
    else:
        original_status = getattr(instance, '_original_status', None)
        if original_status and original_status != current_status:
            send_notif = True

    if send_notif and current_status in status_mapping:
        config = status_mapping[current_status]
        try:
            NotificationService.send_notification(
                user_id=instance.user.id,
                title=config['title'],
                message=config['message'],
                notification_types=config['types'],
                data={
                    'order_id': instance.id,
                    'order_number': instance.order_number,
                    'status': current_status
                }
            )
        except Exception as e:
            logger.error(f"Failed to send order notification for order {instance.order_number}: {e}")
