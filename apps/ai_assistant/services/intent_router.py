import logging
from apps.products.selectors.product_selector import ProductSelector
from apps.ai_assistant.constants import AnswerSource
from apps.ai_assistant.selectors.knowledge_base_selector import KnowledgeBaseSelector
from apps.ai_assistant.services.product_answer_service import ProductAnswerService
from apps.ai_assistant.services.llm_fallback_service import LLMFallbackService

logger = logging.getLogger(__name__)

class IntentRouter:

    @staticmethod
    def classify_and_answer(message_content, session_history):
        msg_lower = message_content.lower()
        
        # 1. Detect products
        products = ProductSelector.get_products()
        mentioned_products = []
        for p in products:
            p_name_lower = p.name.lower()
            tokens = p_name_lower.split()
            matched = False
            for token in tokens:
                if len(token) > 2 and token not in ["neapure", "the", "for", "and"]:
                    if token in msg_lower:
                        matched = True
                        break
            if matched:
                mentioned_products.append(p)
                
        # 2. Check for single product + price/spec intent
        spec_keywords = ["price", "cost", "koto", "taka", "spec", "feature", "warranty", "guarantee", "capacity", "include"]
        intent_keyword = None
        for k in spec_keywords:
            if k in msg_lower:
                intent_keyword = k
                break
                
        if len(mentioned_products) == 1 and intent_keyword:
            logger.info("Routing: DIRECT_PRODUCT_LOOKUP")
            answer = ProductAnswerService.answer_single_product(mentioned_products[0], intent_keyword)
            return answer, AnswerSource.DIRECT_PRODUCT_LOOKUP
            
        # 3. Check for comparison intent (2 products)
        comp_keywords = ["difference", "vs", "compare", "better", "which"]
        has_comp_keyword = any(k in msg_lower for k in comp_keywords)
        
        if len(mentioned_products) == 2 and has_comp_keyword:
            logger.info("Routing: DIRECT_COMPARISON")
            answer = ProductAnswerService.answer_comparison(mentioned_products[0], mentioned_products[1])
            return answer, AnswerSource.DIRECT_COMPARISON
            
        # 4. Search Knowledge Base
        kb_matches = KnowledgeBaseSelector.search_knowledge_base(message_content, limit=3, min_score=0.3)
        if kb_matches:
            top_match, score = kb_matches[0]
            if score >= 0.5: # Confident threshold
                logger.info(f"Routing: DIRECT_FAQ_MATCH (score {score:.2f})")
                return top_match.answer, AnswerSource.DIRECT_FAQ_MATCH
                
        # 5. LLM Fallback
        logger.info("Routing: LLM_GENERATED")
        
        context_parts = [
            "You are a helpful customer support AI for NeaPure, a premium water purifier brand in Bangladesh.",
            "Only use the product/FAQ information given below. If you're not sure, say so honestly and suggest the customer use Live Chat or Call Us (+8809613112233). Do not invent prices, specs, or policies."
        ]
        
        if mentioned_products:
            context_parts.append("\nRelevant Products mentioned:")
            for p in mentioned_products:
                context_parts.append(f"- {p.name}: Price ৳{p.price:,.2f}, Warranty {p.warranty_duration_months} months, Features: {', '.join(p.key_features[:3])}")
                
        if kb_matches:
            context_parts.append("\nRelevant FAQ context:")
            for kb, score in kb_matches:
                context_parts.append(f"Q: {kb.question}\nA: {kb.answer}")
                
        system_prompt = "\n".join(context_parts)
        
        answer = LLMFallbackService.generate_with_context(system_prompt, session_history, message_content)
        return answer, AnswerSource.LLM_GENERATED
