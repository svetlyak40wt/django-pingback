from django.db import models
from django.contrib.contenttypes.models import ContentType


class PingbackClientManager(models.Manager):
    def count_for_link(self, object, link):
        ctype = ContentType.objects.get_for_model(object)
        return self.filter(content_type=ctype, object_id=object.id, url=link).count()
