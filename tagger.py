"""
Ticket Tagger Module
Handles intelligent tagging of support tickets
"""

import re
from typing import List, Dict
from collections import Counter

class TicketTagger:
    """
    AI-powered ticket tagging system.
    """
    
    def __init__(self):
        """Initialize the tagger."""
        self.tag_patterns = {
            "technical": ["api", "integration", "code", "technical", "programming", "development"],
            "account": ["login", "password", "account", "user", "profile", "authentication"],
            "payment": ["payment", "billing", "charge", "refund", "transaction", "money"],
            "bug": ["bug", "error", "broken", "crash", "issue", "problem"],
            "performance": ["slow", "performance", "timeout", "lag", "speed", "loading"],
            "feature": ["feature", "request", "new", "enhancement", "improvement"],
            "security": ["security", "hack", "breach", "suspicious", "unauthorized"],
            "mobile": ["mobile", "phone", "app", "ios", "android", "device"],
            "web": ["website", "browser", "web", "online", "internet"],
            "urgent": ["urgent", "critical", "emergency", "asap", "immediately"],
            "battery": ["battery", "charge", "power", "drain", "charging"],
            "ui": ["interface", "ui", "ux", "design", "layout", "button"],
            "data": ["data", "export", "import", "file", "download", "upload"],
            "notification": ["notification", "alert", "email", "message", "reminder"]
        }
        
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "can", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
        }
    
    def extract_tags(self, text: str) -> List[str]:
        """
        Extract relevant tags from ticket text.
        
        Args:
            text: The ticket text to analyze
            
        Returns:
            List of relevant tags
        """
        text_lower = text.lower()
        tags = []
        
        # Extract tags based on patterns
        for tag_type, keywords in self.tag_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(tag_type)
                    break
        
        # Extract additional tags from text
        additional_tags = self._extract_keywords(text)
        tags.extend(additional_tags)
        
        # Remove duplicates and return
        return list(set(tags))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for tagging.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of extracted keywords
        """
        # Clean and tokenize text
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text_clean.split()
        
        # Remove stop words and short words
        keywords = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Count word frequency
        word_counts = Counter(keywords)
        
        # Return most common keywords (top 5)
        return [word for word, count in word_counts.most_common(5)]
    
    def get_tag_suggestions(self, text: str) -> List[Dict]:
        """
        Get tag suggestions with confidence scores.
        
        Args:
            text: The ticket text
            
        Returns:
            List of tag suggestions with scores
        """
        text_lower = text.lower()
        suggestions = []
        
        for tag_type, keywords in self.tag_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                confidence = min(score / len(keywords), 1.0)
                suggestions.append({
                    "tag": tag_type,
                    "confidence": confidence,
                    "matched_keywords": matched_keywords
                })
        
        # Sort by confidence descending
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions
    
    def categorize_by_tags(self, tags: List[str]) -> str:
        """
        Categorize ticket based on tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Primary category based on tags
        """
        tag_weights = {
            "technical": 0.3,
            "account": 0.25,
            "payment": 0.2,
            "bug": 0.15,
            "performance": 0.1
        }
        
        category_scores = {}
        for tag in tags:
            if tag in tag_weights:
                category_scores[tag] = category_scores.get(tag, 0) + tag_weights[tag]
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return "general"
    
    def get_priority_from_tags(self, tags: List[str]) -> str:
        """
        Determine priority based on tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Priority level
        """
        if "urgent" in tags or "critical" in tags:
            return "Critical"
        elif "bug" in tags or "security" in tags:
            return "High"
        elif "performance" in tags or "account" in tags:
            return "Medium"
        else:
            return "Low"
