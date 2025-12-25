"""
Knowledge Base Module
Implements production system for knowledge representation
Demonstrates: Knowledge Representation (Unit 4 - Production Systems)
"""

import json
from typing import Optional, List, Dict, Any


class KnowledgeBase:
    """
    Represents the knowledge base using production system approach.
    Components:
    - Facts (Working Memory): Current conversation state
    - Rules (Production Memory): IF-THEN rules
    - Data: Products, orders, policies (from PostgreSQL)
    """
    
    def __init__(self, db=None):
        """
        Initialize with database connection.
        
        Args:
            db: Database instance for PostgreSQL queries
        """
        self.db = db
        self.facts = {}  # Working memory - stores current state
        
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Query product from database.
        
        Args:
            product_id: Product ID (e.g., P001)
            
        Returns:
            Product dict with all fields or None if not found
        """
        if not self.db:
            return None
            
        query = """
            SELECT id, name, price, category, features, 
                   returnable, return_window, stock
            FROM products
            WHERE id = %s
        """
        results = self.db.execute_query(query, (product_id,))
        
        if not results:
            return None
            
        row = results[0]
        return {
            'id': row['id'],
            'name': row['name'],
            'price': float(row['price']),
            'category': row['category'],
            'features': row['features'] if row['features'] else [],
            'returnable': row['returnable'],
            'return_window': row['return_window'],
            'stock': row['stock']
        }
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Query order from database.
        
        Args:
            order_id: Order ID (e.g., ORD12345)
            
        Returns:
            Order dict with all fields or None if not found
        """
        if not self.db:
            return None
            
        query = """
            SELECT id, product_id, customer_id, status, order_date,
                   delivery_date, tracking_number, quantity, total
            FROM orders
            WHERE id = %s
        """
        results = self.db.execute_query(query, (order_id,))
        
        if not results:
            return None
            
        row = results[0]
        return {
            'id': row['id'],
            'product_id': row['product_id'],
            'customer_id': row['customer_id'],
            'status': row['status'],
            'order_date': str(row['order_date']) if row['order_date'] else None,
            'delivery_date': str(row['delivery_date']) if row['delivery_date'] else None,
            'tracking_number': row['tracking_number'],
            'quantity': row['quantity'],
            'total': float(row['total'])
        }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Query all rules from database.
        
        Returns:
            List of rule dictionaries
        """
        if not self.db:
            return []
            
        query = """
            SELECT id, name, condition, action, priority, response_template
            FROM rules
            ORDER BY priority DESC
        """
        results = self.db.execute_query(query)
        
        rules = []
        for row in results:
            rules.append({
                'id': row['id'],
                'name': row['name'],
                'condition': row['condition'] if row['condition'] else {},
                'action': row['action'],
                'priority': row['priority'],
                'response_template': row['response_template']
            })
        return rules
    
    def get_return_policy(self) -> Dict[str, Any]:
        """
        Query return policy from database.
        
        Returns:
            Return policy dict or empty dict if not found
        """
        if not self.db:
            return {}
            
        query = """
            SELECT policy_data
            FROM policies
            WHERE policy_type = 'return_policy'
        """
        results = self.db.execute_query(query)
        
        if not results:
            return {}
            
        return results[0]['policy_data'] if results[0]['policy_data'] else {}
    
    def get_shipping_policy(self) -> Dict[str, Any]:
        """
        Query shipping policy from database.
        
        Returns:
            Shipping policy dict or empty dict if not found
        """
        if not self.db:
            return {}
            
        query = """
            SELECT policy_data
            FROM policies
            WHERE policy_type = 'shipping_policy'
        """
        results = self.db.execute_query(query)
        
        if not results:
            return {}
            
        return results[0]['policy_data'] if results[0]['policy_data'] else {}
    
    def get_warranty_policy(self) -> Dict[str, Any]:
        """
        Query warranty policy from database.
        
        Returns:
            Warranty policy dict or empty dict if not found
        """
        if not self.db:
            return {}
            
        query = """
            SELECT policy_data
            FROM policies
            WHERE policy_type = 'warranty_policy'
        """
        results = self.db.execute_query(query)
        
        if not results:
            return {}
            
        return results[0]['policy_data'] if results[0]['policy_data'] else {}
    
    def get_faq(self) -> Dict[str, Any]:
        """
        Query FAQ from database.
        
        Returns:
            FAQ dict or empty dict if not found
        """
        if not self.db:
            return {}
            
        query = """
            SELECT policy_data
            FROM policies
            WHERE policy_type = 'faq'
        """
        results = self.db.execute_query(query)
        
        if not results:
            return {}
            
        return results[0]['policy_data'] if results[0]['policy_data'] else {}

    
    def search_products(self, category: str = None, max_price: float = None, 
                        keyword: str = None) -> List[Dict[str, Any]]:
        """
        Search products with filters using database queries.
        
        Args:
            category: Filter by category (case-insensitive)
            max_price: Filter by maximum price
            keyword: Filter by keyword in name, category, or features
            
        Returns:
            List of matching product dictionaries
        """
        if not self.db:
            return []
        
        # Build dynamic query with filters
        query = """
            SELECT id, name, price, category, features, 
                   returnable, return_window, stock
            FROM products
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND LOWER(category) = LOWER(%s)"
            params.append(category)
        
        if max_price is not None:
            query += " AND price <= %s"
            params.append(max_price)
        
        if keyword:
            query += """ AND (
                LOWER(name) LIKE LOWER(%s) OR 
                LOWER(category) LIKE LOWER(%s) OR
                EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(features) AS f
                    WHERE LOWER(f) LIKE LOWER(%s)
                )
            )"""
            keyword_pattern = f"%{keyword}%"
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        query += " ORDER BY name"
        
        results = self.db.execute_query(query, tuple(params) if params else None)
        
        products = []
        for row in results:
            products.append({
                'id': row['id'],
                'name': row['name'],
                'price': float(row['price']),
                'category': row['category'],
                'features': row['features'] if row['features'] else [],
                'returnable': row['returnable'],
                'return_window': row['return_window'],
                'stock': row['stock']
            })
        return products
    
    def update_facts(self, new_facts: Dict[str, Any]) -> None:
        """Update working memory with new facts."""
        self.facts.update(new_facts)
    
    def get_facts(self) -> Dict[str, Any]:
        """Get current facts from working memory."""
        return self.facts
    
    def clear_facts(self) -> None:
        """Clear working memory."""
        self.facts = {}
