"""
Ticket Categorizer Module
Handles intelligent categorization of support tickets
"""

import re
from typing import Dict, List
from datetime import datetime

class TicketCategorizer:
    """
    AI-powered ticket categorization system.
    """
    
    def __init__(self):
        """Initialize the categorizer."""
        self.categories = {
            "Account Issues": {
                "keywords": ["login", "password", "account", "signin", "signup", "authentication", "locked", "credentials"],
                "priority": "High"
            },
            "Payment Issues": {
                "keywords": ["payment", "billing", "charge", "refund", "transaction", "card", "money", "invoice"],
                "priority": "High"
            },
            "Technical Support": {
                "keywords": ["api", "integration", "help", "support", "technical", "documentation", "guide"],
                "priority": "Medium"
            },
            "Bug Reports": {
                "keywords": ["bug", "error", "broken", "crash", "issue", "problem", "not working", "failed"],
                "priority": "Critical"
            },
            "Performance Issues": {
                "keywords": ["slow", "performance", "timeout", "lag", "speed", "loading", "response"],
                "priority": "Medium"
            },
            "Feature Requests": {
                "keywords": ["feature", "request", "new", "enhancement", "improvement", "suggestion"],
                "priority": "Low"
            },
            "Battery Issues": {
                "keywords": ["battery", "charge", "power", "drain", "charging", "life"],
                "priority": "Medium"
            },
            "Security Issues": {
                "keywords": ["security", "hack", "breach", "suspicious", "unauthorized", "threat"],
                "priority": "Critical"
            }
        }
    
    def categorize(self, ticket_text: str) -> Dict:
        """
        Categorize a ticket based on its content.
        
        Args:
            ticket_text: The ticket content to categorize
            
        Returns:
            Dictionary containing category, priority, and confidence
        """
        text_lower = ticket_text.lower()
        
        # Calculate scores for each category
        category_scores = {}
        for category, config in self.categories.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    score += 1
            
            # Normalize score by number of keywords
            normalized_score = score / len(config["keywords"])
            category_scores[category] = normalized_score
        
        # Find best category
        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]
        
        # Determine priority
        priority = self.categories[best_category]["priority"]
        
        # Adjust priority based on urgency keywords
        urgency_keywords = ["urgent", "critical", "emergency", "asap", "immediately"]
        if any(keyword in text_lower for keyword in urgency_keywords):
            if priority == "Low":
                priority = "Medium"
            elif priority == "Medium":
                priority = "High"
            else:
                priority = "Critical"
        
        # Calculate confidence
        confidence = min(best_score * 2, 1.0)  # Scale to 0-1
        
        return {
            "category": best_category,
            "priority": priority,
            "confidence": confidence,
            "reasoning": f"Categorized as {best_category} based on keyword matching"
        }
    
    def get_category_suggestions(self, ticket_text: str) -> List[Dict]:
        """
        Get multiple category suggestions for a ticket.
        
        Args:
            ticket_text: The ticket content
            
        Returns:
            List of category suggestions with scores
        """
        text_lower = ticket_text.lower()
        suggestions = []
        
        for category, config in self.categories.items():
            score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                normalized_score = score / len(config["keywords"])
                suggestions.append({
                    "category": category,
                    "score": normalized_score,
                    "matched_keywords": matched_keywords,
                    "priority": config["priority"]
                })
        
        # Sort by score descending
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:3]  # Return top 3 suggestions
