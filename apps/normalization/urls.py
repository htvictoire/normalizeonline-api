from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.normalization.views import DatasetViewSet, instance_status_webhook

router = DefaultRouter()
router.register(r"datasets", DatasetViewSet, basename="dataset")

urlpatterns = router.urls + [
    path("webhook/instance-status/", instance_status_webhook, name="instance-status-webhook"),
]
