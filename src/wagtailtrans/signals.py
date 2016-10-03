from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete
from wagtail.wagtailcore.models import get_page_models, Site

from wagtailtrans.models import (
    Language, TranslatablePage, get_default_language)
from wagtailtrans.permissions import (
    get_or_create_language_group, create_group_permissions)


def synchronize_trees(sender, instance, **kwargs):
    """synchronize the translation trees when
    a TranslatablePage is created or moved.

    :param sender: Sender model
    :param instance: TranslatablePage instance
    :param kwargs: kwargs e.g. created

    """
    if (
        not kwargs.get('created') or
        not settings.WAGTAILTRANS_SYNC_TREE or
        not getattr(instance, 'language', False) or
        not instance.language.is_default or
        not instance.get_site()
    ):
        return

    for language in Language.objects.filter(is_default=False):
        instance.create_translation(language, copy_fields=True)


def synchronize_deletions(sender, instance, **kwargs):
    """We use pre_delete because when sync is disabled the foreign_key on
    canonical pages on_delete is set_null.

    :param sender: Sender model
    :param instance: TranslatablePage Instance
    :param kwargs: kwargs

    """
    page = TranslatablePage.objects.filter(pk=instance.pk).first()
    if settings.WAGTAILTRANS_SYNC_TREE and page:
        TranslatablePage.objects.filter(canonical_page=page).delete()


def create_new_language_tree(sender, instance, **kwargs):
    """Signal will catch creation of a new language
    If sync trees is enabled it will create a whole new tree with
    correlating language.

    :param sender: Sender model
    :param instance: Language instance
    :param kwargs: kwargs e.g. created

    """
    if kwargs.get('created'):
        # create group and page permissions
        group = get_or_create_language_group(instance)
        create_group_permissions(group, instance)

    if not kwargs.get('created') or not settings.WAGTAILTRANS_SYNC_TREE:
        return

    for site in Site.objects.all():
        site_pages = site.root_page.get_children().values_list('pk', flat=True)
        canonical_home_page = (
            TranslatablePage.objects
            .filter(pk__in=site_pages, language=get_default_language())
            .first())

        for child_page in canonical_home_page.get_descendants(inclusive=True):
            child_page.specific.create_translation(instance, copy_fields=True)


def register_signal_handlers():
    """Registers signal handlers.

    To create a signal for TranslatablePage we have to use wagtails
    get_page_model.

    """
    post_save.connect(create_new_language_tree, sender=Language)

    for model in get_page_models():
        post_save.connect(synchronize_trees, sender=model)
        pre_delete.connect(synchronize_deletions, sender=model)
