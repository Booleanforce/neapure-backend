from django.core.management.base import BaseCommand
from apps.ai_assistant.models import KnowledgeBase
from apps.ai_assistant.constants import KBCategory

class Command(BaseCommand):
    help = 'Seeds initial FAQ entries into the KnowledgeBase'

    def handle(self, *args, **kwargs):
        faqs = [
            {
                "title": "Family of 5 Recommendation",
                "category": KBCategory.RECOMMENDATION,
                "question": "Which purifier is best for a family of 5?",
                "answer": "For a family of 5, we highly recommend the NeaPure Max. It offers a larger storage capacity and faster purification rate to keep up with higher daily water consumption.",
                "tags": ["family", "5", "five", "recommendation", "best"]
            },
            {
                "title": "Pro vs Max Comparison",
                "category": KBCategory.PRODUCT_INFO,
                "question": "What is the difference between NeaPure Pro and NeaPure Max?",
                "answer": "The NeaPure Pro is a great balance of features and price, ideal for medium families. The NeaPure Max adds AI-powered monitoring, a larger tank, and a premium design, perfect for larger households or those wanting top-tier smart features.",
                "tags": ["difference", "compare", "pro", "max", "vs"]
            },
            {
                "title": "Installation Charges",
                "category": KBCategory.INSTALLATION,
                "question": "Is installation free? How much does installation cost?",
                "answer": "Standard installation is completely FREE inside Dhaka. For areas outside Dhaka, a nominal service charge may apply depending on the exact location.",
                "tags": ["installation", "free", "cost", "charge", "install"]
            },
            {
                "title": "Filter Replacement Intervals",
                "category": KBCategory.FILTER_REPLACEMENT,
                "question": "How often do I need to change the filters?",
                "answer": "We generally recommend changing the Sediment and Pre-Carbon filters every 6 months, and the RO membrane every 12 to 18 months, depending on your local water quality.",
                "tags": ["filter", "change", "replace", "how often", "duration"]
            },
            {
                "title": "Warranty Coverage",
                "category": KBCategory.WARRANTY,
                "question": "What does the warranty cover?",
                "answer": "Our standard 12-month warranty covers all electrical components (like the pump and adapter) against manufacturing defects. Consumable filters are not covered under this warranty.",
                "tags": ["warranty", "cover", "include", "electrical"]
            },
            {
                "title": "Delivery Time",
                "category": KBCategory.DELIVERY,
                "question": "How long does delivery take?",
                "answer": "We typically deliver and install within 24 to 48 hours inside Dhaka. Outside Dhaka, delivery takes 3 to 5 business days.",
                "tags": ["delivery", "time", "how long", "days"]
            }
        ]

        count = 0
        for faq in faqs:
            kb, created = KnowledgeBase.objects.get_or_create(
                question=faq["question"],
                defaults={
                    "title": faq["title"],
                    "category": faq["category"],
                    "answer": faq["answer"],
                    "tags": faq["tags"]
                }
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Created KB: {faq["title"]}'))
            else:
                self.stdout.write(f'Already exists: {faq["title"]}')
                
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} new KB entries.'))
