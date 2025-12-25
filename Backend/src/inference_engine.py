class InferenceEngine:
    """
    Implements forward chaining inference for production system.
    
    1. Match Phase: Find rules whose conditions match current facts
    2. Conflict Resolution: Select best rule using priority
    3. Execute Phase: Fire the selected rule
    """
    
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
    
    def match_rules(self, facts):
        
        matched_rules = []
        
        for rule in self.kb.get_rules():
            if self.evaluate_condition(rule['condition'], facts):
                matched_rules.append(rule)
        
        return matched_rules
    
    def evaluate_condition(self, condition, facts):
        
        for key, value in condition.items():
            # Check if fact exists
            if key not in facts:
                return False
            
            # For boolean conditions (like has_order_id)
            if isinstance(value, bool):
                if value and not facts.get(key):
                    return False
                if not value and facts.get(key):
                    return False
            # For exact value matching
            elif facts[key] != value:
                return False
        
        return True
    
    def resolve_conflict(self, matched_rules):
       
        if not matched_rules:
            return None
        
        # Select rule with highest priority
        return max(matched_rules, key=lambda r: r['priority'])
    
    def infer(self, facts):
        
        # Update knowledge base facts
        self.kb.update_facts(facts)
        
        # Match phase: Find matching rules
        matched_rules = self.match_rules(facts)
        
        # Conflict resolution: Select best rule
        selected_rule = self.resolve_conflict(matched_rules)
        
        return selected_rule
    
    def explain_inference(self, facts):
       
        matched_rules = self.match_rules(facts)
        selected_rule = self.resolve_conflict(matched_rules)
        
        return {
            'facts': facts,
            'matched_rules': [r['id'] for r in matched_rules],
            'selected_rule': selected_rule['id'] if selected_rule else None,
            'reason': 'Highest priority' if selected_rule else 'No matching rules'
        }
