

import json
from typing import Optional, List, Dict, Any


class KnowledgeBase:
    """
    - Facts (Working Memory): Current conversation state
    - Rules (Production Memory): IF-THEN rules
    - Data: Products, orders, policies (from PostgreSQL)
    """
    
    def __init__(self, db=None):
        
        self.db = db
        self.facts = {}  # Working memory - stores current state
        
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        
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
        
        if not self.db:
            return []
            
        query = """
            SELECT id, name, condition, action, priority, response_template
            FROM rules
            ORDER BY priority DESC
            LIMIT 10
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
        
        query += " ORDER BY name LIMIT 10"
        
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

    def search_products_advanced(
        self, 
        name: str = None, 
        feature: str = None, 
        category: str = None
    ) -> List[Dict[str, Any]]:
        
        if not self.db:
            return []
        
        # Build dynamic query with filters using AND logic
        query = """
            SELECT id, name, price, category, features, 
                   returnable, return_window, stock
            FROM products
            WHERE 1=1
        """
        params = []
        
        if name:
            query += " AND name ILIKE %s"
            params.append(f"%{name}%")
        
        if feature:
            query += """ AND EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(features::jsonb) AS f
                WHERE f ILIKE %s
            )"""
            params.append(f"%{feature}%")
        
        if category:
            query += " AND LOWER(category) = LOWER(%s)"
            params.append(category)
        
        query += " ORDER BY id LIMIT 10"
        
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

    def get_user_orders(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        
        if user_id is None:
            return None
            
        if not self.db:
            return []
            
        query = """
            SELECT id, product_id, customer_id, user_id, status, order_date,
                   delivery_date, tracking_number, quantity, total
            FROM orders
            WHERE user_id = %s
            ORDER BY order_date DESC
            LIMIT 10
        """
        results = self.db.execute_query(query, (user_id,))
        
        orders = []
        for row in results:
            orders.append({
                'id': row['id'],
                'product_id': row['product_id'],
                'customer_id': row['customer_id'],
                'user_id': row['user_id'],
                'status': row['status'],
                'order_date': str(row['order_date']) if row['order_date'] else None,
                'delivery_date': str(row['delivery_date']) if row['delivery_date'] else None,
                'tracking_number': row['tracking_number'],
                'quantity': row['quantity'],
                'total': float(row['total'])
            })
        return orders

    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        
        if user_id is None:
            return None
            
        if not self.db:
            return None
            
        query = """
            SELECT id, email, name, role, created_at, last_login
            FROM users
            WHERE id = %s
        """
        results = self.db.execute_query(query, (user_id,))
        
        if not results:
            return None
            
        row = results[0]
        return {
            'id': row['id'],
            'email': row['email'],
            'name': row['name'],
            'role': row['role'],
            'created_at': str(row['created_at']) if row['created_at'] else None,
            'last_login': str(row['last_login']) if row['last_login'] else None
        }

    def get_content_based_recommendations(self, limit: int = 5) -> List[Dict[str, Any]]:
        
        if not self.db:
            return []
        
        # Use subquery to avoid GROUP BY issues with JSON column
        query = """
            SELECT p.id, p.name, p.price, p.category, p.features,
                   p.returnable, p.return_window, p.stock,
                   COALESCE(click_counts.click_count, 0) as click_count
            FROM products p
            LEFT JOIN (
                SELECT product_id, COUNT(*) as click_count
                FROM user_product_interactions
                WHERE interaction_type = 'click'
                GROUP BY product_id
            ) click_counts ON p.id = click_counts.product_id
            ORDER BY click_count DESC, p.name ASC
            LIMIT %s
        """
        results = self.db.execute_query(query, (limit,))
        
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
                'stock': row['stock'],
                'click_count': row['click_count']
            })
        return products

    def get_personalized_recommendations(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        
        if user_id is None or not self.db:
            return []
        
        # Get categories from user's orders
        query = """
            SELECT DISTINCT p.category
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = %s AND o.status != 'Cancelled'
        """
        category_results = self.db.execute_query(query, (user_id,))
        
        if not category_results:
            return []
        
        categories = [row['category'] for row in category_results]
        
        # Get products from those categories that user hasn't ordered
        placeholders = ', '.join(['%s'] * len(categories))
        query = f"""
            SELECT p.id, p.name, p.price, p.category, p.features,
                   p.returnable, p.return_window, p.stock
            FROM products p
            WHERE p.category IN ({placeholders})
              AND p.stock > 0
              AND p.id NOT IN (
                  SELECT DISTINCT product_id FROM orders WHERE user_id = %s
              )
            ORDER BY p.category, p.price DESC
            LIMIT %s
        """
        params = tuple(categories) + (user_id, limit)
        results = self.db.execute_query(query, params)
        
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

    def get_hybrid_recommendations(self, user_id: int = None, total_limit: int = 10) -> Dict[str, Any]:
        
        personalized_limit = 5
        content_limit = 5
        
        # Get personalized recommendations if user is authenticated
        personalized = []
        if user_id:
            personalized = self.get_personalized_recommendations(user_id, limit=personalized_limit + 5)
        
        # Calculate how many content-based we need
        # If no personalized, get all 10 from content-based
        actual_personalized_count = min(len(personalized), personalized_limit)
        needed_content = total_limit - actual_personalized_count
        
        # Get content-based recommendations (most clicked)
        content_based = self.get_content_based_recommendations(limit=needed_content + 5)
        
        # Build combined list without duplicates
        seen_ids = set()
        combined = []
        
        # Add personalized first (higher priority for logged-in users)
        for product in personalized:
            if len(combined) >= personalized_limit:
                break
            if product['id'] not in seen_ids:
                product['source'] = 'personalized'
                combined.append(product)
                seen_ids.add(product['id'])
        
        # Fill remaining slots with content-based (excluding already added)
        for product in content_based:
            if len(combined) >= total_limit:
                break
            if product['id'] not in seen_ids:
                product['source'] = 'content_based'
                combined.append(product)
                seen_ids.add(product['id'])
        
        return {
            'content_based': [p for p in combined if p.get('source') == 'content_based'],
            'personalized': [p for p in combined if p.get('source') == 'personalized'],
            'combined': combined[:total_limit]
        }

    def record_interaction(self, user_id: int, product_id: str, interaction_type: str) -> bool:
        
        if not self.db or user_id is None:
            return False
        
        valid_types = ['click', 'like', 'share', 'view', 'wishlist']
        if interaction_type not in valid_types:
            return False
        
        query = """
            INSERT INTO user_product_interactions (user_id, product_id, interaction_type)
            VALUES (%s, %s, %s)
        """
        return self.db.execute_write(query, (user_id, product_id, interaction_type))
