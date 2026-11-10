"""Delete product images only after they are no longer referenced in the database."""

import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Product

logger = logging.getLogger(__name__)


def _delete_image_if_unreferenced(storage, image_name, product_id, action):
    if not image_name or Product.objects.filter(image=image_name).exists():
        return

    try:
        storage.delete(image_name)
    except Exception:
        logger.exception(
            "Product %s was %s, but its unreferenced Supabase image %s could not be removed.",
            product_id,
            action,
            image_name,
        )


@receiver(pre_save, sender=Product)
def remember_previous_product_image(sender, instance, **kwargs):
    """Remember the persisted image before an existing product is updated."""
    instance._previous_image_name = None
    if not instance.pk:
        return

    instance._previous_image_name = (
        sender.objects.filter(pk=instance.pk)
        .values_list("image", flat=True)
        .first()
    )


@receiver(post_save, sender=Product)
def delete_replaced_product_image(sender, instance, created, **kwargs):
    """Clean up a replaced image after commit, provided no product still uses it."""
    if created:
        return

    old_image_name = getattr(instance, "_previous_image_name", None)
    current_image_name = (
        sender.objects.filter(pk=instance.pk)
        .values_list("image", flat=True)
        .first()
    )
    if not old_image_name or old_image_name == current_image_name:
        return

    storage = instance.image.storage
    transaction.on_commit(
        lambda: _delete_image_if_unreferenced(
            storage, old_image_name, instance.pk, "updated"
        )
    )


@receiver(post_delete, sender=Product)
def delete_unreferenced_product_image(sender, instance, **kwargs):
    """Remove a product image only after no remaining product references it."""
    image_name = instance.image.name if instance.image else None
    if not image_name:
        return

    _delete_image_if_unreferenced(
        instance.image.storage, image_name, instance.pk, "deleted"
    )
