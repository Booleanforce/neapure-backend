from django.db import models
from django.utils.translation import gettext_lazy as _

class KBCategory(models.TextChoices):
    PRODUCT_INFO = "PRODUCT_INFO", _("Product Info")
    PRICING = "PRICING", _("Pricing")
    WARRANTY = "WARRANTY", _("Warranty")
    INSTALLATION = "INSTALLATION", _("Installation")
    MAINTENANCE = "MAINTENANCE", _("Maintenance")
    FILTER_REPLACEMENT = "FILTER_REPLACEMENT", _("Filter Replacement")
    SERVICE_CHARGES = "SERVICE_CHARGES", _("Service Charges")
    DELIVERY = "DELIVERY", _("Delivery")
    GENERAL_FAQ = "GENERAL_FAQ", _("General FAQ")
    RECOMMENDATION = "RECOMMENDATION", _("Recommendation")

class MessageRole(models.TextChoices):
    USER = "USER", _("User")
    ASSISTANT = "ASSISTANT", _("Assistant")

class AnswerSource(models.TextChoices):
    DIRECT_PRODUCT_LOOKUP = "DIRECT_PRODUCT_LOOKUP", _("Direct Product Lookup")
    DIRECT_COMPARISON = "DIRECT_COMPARISON", _("Direct Comparison")
    DIRECT_FAQ_MATCH = "DIRECT_FAQ_MATCH", _("Direct FAQ Match")
    LLM_GENERATED = "LLM_GENERATED", _("LLM Generated")
