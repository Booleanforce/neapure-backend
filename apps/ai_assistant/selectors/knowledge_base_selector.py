import re
from apps.ai_assistant.models import KnowledgeBase

class KnowledgeBaseSelector:

    @staticmethod
    def search_knowledge_base(query, limit=3, min_score=0.5):
        # Extract meaningful keywords (length > 2, alphanumeric)
        words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        
        # Stopwords
        stopwords = {"the", "and", "for", "with", "that", "this", "are", "you", "what", "how", "why", "when", "can", "does", "will"}
        words = words - stopwords
        
        if not words:
            return []
            
        kbs = KnowledgeBase.objects.all()
        results = []
        for kb in kbs:
            text = f"{kb.title} {kb.question} {kb.answer} {' '.join(kb.tags)}".lower()
            
            hits = sum(1 for w in words if w in text)
            score = hits / len(words)
            
            if min_score is None or score >= min_score:
                results.append((kb, score))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
