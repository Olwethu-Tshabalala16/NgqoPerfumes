"""Delete unreferenced product images when their database records are removed."""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Product

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Product)
def delete_unreferenced_product_image(sender, instance, **kwargs):
    """Remove a product image only after no remaining product references it."""
    image_name = instance.image.name if instance.image else None
    if not image_name:
        return

    if Product.objects.filter(image=image_name).exists():
        return

    try:
        instance.image.storage.delete(image_name)
    except Exception:
        # A failed remote cleanup must not undo the database deletion. Log it
        # so the orphan can be investigated and removed without losing the row.
        logger.exception(
            "Product %s was deleted, but its Supabase image %s could not be removed.",
            instance.pk,
            image_name,
        )
