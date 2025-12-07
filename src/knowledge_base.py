"""
Knowledge Base Module
Implements production system for knowledge representation
Demonstrates: Knowledge Representation (Unit 4 - Production Systems)
"""

import json
import os

class KnowledgeBase:
    """
    Represents the knowledge base using production system approach.
    Components:
    - Facts (Working Memory): Current conversation state
    - Rules (Production Memory): IF-THEN rules
    - Data: Products, orders, policies
    """
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.products = self.load_json('products.json')
        self.orders = self.load_json('orders.json')
        self.policies = self.load_json('policies.json')
        self.rules = self.load_json('rules.json')['rules']
        self.facts = {}  # Working memory - stores current state
        
    def load_json(self, filename):
        """Load JSON data file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filepath} not found")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {filepath}")
            return {}
    
    def get_product(self, product_id):
        """Retrieve product information"""
        return self.products.get(product_id)
    
    def get_order(self, order_id):
        """Retrieve order information"""
        return self.orders.get(order_id)
    
    def get_rules(self):
        """Get all production rules"""
        return self.rules
    
    def get_return_policy(self):
        """Get return policy information"""
        return self.policies.get('return_policy', {})
    
    def get_shipping_policy(self):
        """Get shipping policy information"""
        return self.policies.get('shipping_policy', {})
    
    def get_warranty_policy(self):
        """Get warranty policy information"""
        return self.policies.get('warranty_policy', {})
    
    def get_faq(self):
        """Get FAQ information"""
        return self.policies.get('faq', {})
    
    def search_products(self, category=None, max_price=None, keyword=None):
        """Search products based on criteria"""
        results = []
        
        for product_id, product in self.products.items():
            # Filter by category
            if category and product.get('category', '').lower() != category.lower():
                continue
            
            # Filter by price
            if max_price and product.get('price', 0) > max_price:
                continue
            
            # Filter by keyword
            if keyword:
                keyword_lower = keyword.lower()
                name_match = keyword_lower in product.get('name', '').lower()
                category_match = keyword_lower in product.get('category', '').lower()
                features_match = any(keyword_lower in f.lower() for f in product.get('features', []))
                
                if not (name_match or category_match or features_match):
                    continue
            
            results.append({
                'id': product_id,
                **product
            })
        
        return results
    
    def update_facts(self, new_facts):
        """Update working memory with new facts"""
        self.facts.update(new_facts)
    
    def get_facts(self):
        """Get current facts from working memory"""
        return self.facts
    
    def clear_facts(self):
        """Clear working memory"""
        self.facts = {}
