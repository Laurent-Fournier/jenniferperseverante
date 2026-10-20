from django.core.cache import cache
from django.conf import settings

from .models import LabelLg

CACHE_TIMEOUT = 3600  # 1 heure, ajustez selon la fréquence des mises à jour


def labels(request):
    language = getattr(request, "lg", "fr")[:2]
    cache_key = f"labels_{language}"

    labels_dict = cache.get(cache_key)
    if labels_dict is None:
        labels_dict = {
            row.code: row.label
            for row in LabelLg.objects.filter(language_code=language)
        }
        cache.set(cache_key, labels_dict, timeout=CACHE_TIMEOUT)

    return {"labels": labels_dict}


# def labels(request):
#     language = getattr(request, "lg", "fr")[:2]

#     labels = {
#         row.code: row.label for row in LabelLg.objects.filter(language_code=language)
#     }

#     return {"labels": labels}
