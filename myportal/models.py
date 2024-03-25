import uuid
from django.db import models


class Resource(models.Model):
    uuid = models.CharField(default=uuid.uuid4, editable=False, unique=True, max_length=50)
    resource_type = models.CharField(default="single", max_length=50)
    publication_name = models.CharField(max_length=255)
    publication_type = models.CharField(default="Geospatial Files", max_length=50)  # geospatial/workflow/others
    description = models.CharField(max_length=1024, null=True)
    keywords = models.CharField(max_length=1024, null=True)
    path = models.CharField(max_length=255)
    task_id = models.CharField(null=True, max_length=50)
    status = models.CharField(null=True, max_length=50)
    user_id = models.CharField(null=True, max_length=50)
    created_time = models.DateTimeField(null=True, auto_now_add=True)
    modified_time = models.DateTimeField(null=True, auto_now=True)
    extra_info = models.CharField(max_length=1024, null=True)

    def __str__(self):
        created_time_formatted = self.created_time.strftime('%Y-%m-%d %H:%M:%S') if self.created_time else 'N/A'
        return (f"Resource UUID: {self.uuid}, "
                f"Resource Type: {self.resource_type}, "
                f"Publication Name: {self.publication_name}, "
                f"Publication Type: {self.publication_type}, "
                f"Path: {self.path}, "
                f"Task ID: {self.task_id}, "
                f"Status: {self.status}, "
                f"User ID: {self.user_id}, "
                f"Created Time: {created_time_formatted}")


class FileInfo(models.Model):
    path = models.URLField()
    info = models.CharField(max_length=255)

    def __str__(self):
        return self.path