class ProductAnswerService:

    @staticmethod
    def answer_single_product(product, intent_keyword=None):
        name = product.name
        price = f"৳{product.price:,.2f}"
        
        # Build features list
        features_list = ""
        for i, f in enumerate(product.key_features[:5]):
            features_list += f"\n- {f}"
            
        warranty = f"{product.warranty_duration_months} months"
        
        maintenance = ""
        if product.recommended_replacement_months:
            maintenance = f"\n*Maintenance:* We recommend replacing the filters every {product.recommended_replacement_months} months."
            
        perfect_for = f"\n*Perfect For:* {product.perfect_for}" if product.perfect_for else ""
        
        # We can vary phrasing slightly based on intent keyword
        if intent_keyword in ["price", "cost", "koto"]:
            intro = f"The price of the **{name}** is **{price}**."
            body = f"\nIt comes with a {warranty} warranty.{perfect_for}\n\nHere are some of its key features:{features_list}{maintenance}"
        elif intent_keyword in ["warranty", "guarantee"]:
            intro = f"The **{name}** comes with a **{warranty} warranty**."
            body = f"\nIts current price is {price}.{perfect_for}\n\nKey features include:{features_list}{maintenance}"
        else:
            intro = f"Here is the information for the **{name}**:"
            body = f"\n*Price:* {price}\n*Warranty:* {warranty}{perfect_for}\n\n*Key Features:*{features_list}{maintenance}"
            
        return f"{intro}{body}"

    @staticmethod
    def answer_comparison(product_a, product_b):
        price_a = f"৳{product_a.price:,.2f}"
        price_b = f"৳{product_b.price:,.2f}"
        
        # Structured comparison
        ans = f"Here is a comparison between the **{product_a.name}** and the **{product_b.name}**:\n\n"
        
        ans += f"**Price:**\n"
        ans += f"- {product_a.name}: {price_a}\n"
        ans += f"- {product_b.name}: {price_b}\n\n"
        
        ans += f"**Key Features ({product_a.name}):**\n"
        for f in product_a.key_features[:3]:
            ans += f"- {f}\n"
            
        ans += f"\n**Key Features ({product_b.name}):**\n"
        for f in product_b.key_features[:3]:
            ans += f"- {f}\n"
            
        ans += f"\n**Warranty:**\n"
        ans += f"- {product_a.name}: {product_a.warranty_duration_months} months\n"
        ans += f"- {product_b.name}: {product_b.warranty_duration_months} months\n"
        
        # Recommendation
        if product_a.price > product_b.price:
            more_expensive, cheaper = product_a, product_b
        else:
            more_expensive, cheaper = product_b, product_a
            
        ans += f"\n**Recommendation:**\nIf you want a more premium option with advanced features, go with the **{more_expensive.name}**. For a more affordable and straightforward setup, the **{cheaper.name}** is a great choice."
        return ans
