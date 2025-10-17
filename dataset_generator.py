"""
Dataset Generator Module
Creates sample datasets for testing and demonstration
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import random
from typing import List, Dict

class DatasetGenerator:
    """
    Generates sample datasets for the customer support system.
    """
    
    def __init__(self):
        """Initialize the dataset generator."""
        self.sample_tickets = self._generate_sample_tickets()
    
    def _generate_sample_tickets(self) -> List[Dict]:
        """Generate sample ticket data."""
        return [
            {
                "ticket_id": "TK-1757338014",
                "customer_email": "john.doe@gmail.com",
                "customer_name": "John Doe",
                "issue_summary": "Login problem",
                "detailed_issue": "Cannot login to my account. Getting authentication error when I try to sign in.",
                "category": "Account Issues",
                "priority": "High",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.85,
                "solved": False,
                "ai_response": ["Reset your password", "Check email address", "Clear browser cache"],
                "tags": ["account", "login", "technical"]
            },
            {
                "ticket_id": "TK-1757338020",
                "customer_email": "jane.smith@gmail.com",
                "customer_name": "Jane Smith",
                "issue_summary": "Payment issue",
                "detailed_issue": "Payment not processing when I try to buy premium plan. Getting error message.",
                "category": "Payment Issues",
                "priority": "High",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.90,
                "solved": False,
                "ai_response": ["Check payment method", "Verify billing address", "Try different card"],
                "tags": ["payment", "billing", "urgent"]
            },
            {
                "ticket_id": "TK-1757340392",
                "customer_email": "mike.johnson@gmail.com",
                "customer_name": "Mike Johnson",
                "issue_summary": "Battery problem",
                "detailed_issue": "iPhone battery drains quickly after latest iOS update. Used to last all day, now dies in 4 hours.",
                "category": "Battery Issues",
                "priority": "Medium",
                "status": "Closed",
                "created_date": "2025-09-08",
                "platform": "Mobile",
                "ai_confidence": 0.88,
                "solved": True,
                "ai_response": ["Reduce screen brightness", "Enable Low Power Mode", "Check Battery Health"],
                "tags": ["battery", "mobile", "performance"]
            },
            {
                "ticket_id": "TK-1757340456",
                "customer_email": "sarah.wilson@gmail.com",
                "customer_name": "Sarah Wilson",
                "issue_summary": "API integration help",
                "detailed_issue": "Need help integrating your API with our CRM system. Documentation is unclear about authentication flow.",
                "category": "Technical Support",
                "priority": "Medium",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.92,
                "solved": False,
                "ai_response": ["Check API documentation", "Verify API key", "Contact technical support"],
                "tags": ["api", "technical", "integration"]
            },
            {
                "ticket_id": "TK-1757340523",
                "customer_email": "david.brown@gmail.com",
                "customer_name": "David Brown",
                "issue_summary": "App crashing",
                "detailed_issue": "Mobile app crashes when I try to upload photos. This is urgent as I need to submit my work.",
                "category": "Bug Reports",
                "priority": "Critical",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Mobile",
                "ai_confidence": 0.95,
                "solved": False,
                "ai_response": ["Update app to latest version", "Clear app cache", "Restart device"],
                "tags": ["bug", "mobile", "crash", "urgent"]
            },
            {
                "ticket_id": "TK-1757340589",
                "customer_email": "lisa.garcia@gmail.com",
                "customer_name": "Lisa Garcia",
                "issue_summary": "Feature request",
                "detailed_issue": "Can you add dark mode feature to the web interface? It would be great for night usage.",
                "category": "Feature Requests",
                "priority": "Low",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.75,
                "solved": False,
                "ai_response": ["Feature request noted", "Will be reviewed by product team", "Check roadmap for updates"],
                "tags": ["feature", "ui", "enhancement"]
            },
            {
                "ticket_id": "TK-1757340654",
                "customer_email": "robert.miller@gmail.com",
                "customer_name": "Robert Miller",
                "issue_summary": "Performance issue",
                "detailed_issue": "Website is loading very slowly on mobile devices. Takes 30 seconds to load each page.",
                "category": "Performance Issues",
                "priority": "Medium",
                "status": "In Progress",
                "created_date": "2025-09-08",
                "platform": "Mobile",
                "ai_confidence": 0.87,
                "solved": False,
                "ai_response": ["Check internet connection", "Clear browser cache", "Try different browser"],
                "tags": ["performance", "mobile", "slow"]
            },
            {
                "ticket_id": "TK-1757340721",
                "customer_email": "emily.davis@gmail.com",
                "customer_name": "Emily Davis",
                "issue_summary": "Security concern",
                "detailed_issue": "Received suspicious email claiming to be from your company asking for password reset.",
                "category": "Security Issues",
                "priority": "Critical",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.93,
                "solved": False,
                "ai_response": ["Do not click any links", "Report to security team", "Change password immediately"],
                "tags": ["security", "suspicious", "urgent"]
            },
            {
                "ticket_id": "TK-1757340788",
                "customer_email": "chris.anderson@gmail.com",
                "customer_name": "Chris Anderson",
                "issue_summary": "Account locked",
                "detailed_issue": "My account got locked after multiple failed login attempts. I need urgent access.",
                "category": "Account Issues",
                "priority": "High",
                "status": "Open",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.89,
                "solved": False,
                "ai_response": ["Reset password", "Contact support for unlock", "Check email for instructions"],
                "tags": ["account", "locked", "urgent"]
            },
            {
                "ticket_id": "TK-1757340855",
                "customer_email": "amanda.taylor@gmail.com",
                "customer_name": "Amanda Taylor",
                "issue_summary": "Data export",
                "detailed_issue": "How do I export my data in CSV format? I need it for my records.",
                "category": "Technical Support",
                "priority": "Low",
                "status": "Closed",
                "created_date": "2025-09-08",
                "platform": "Web",
                "ai_confidence": 0.82,
                "solved": True,
                "ai_response": ["Go to Settings > Export Data", "Select CSV format", "Download will be sent to email"],
                "tags": ["data", "export", "technical"]
            }
        ]
    
    def generate_csv_dataset(self, filename: str = "sample_tickets.csv") -> str:
        """
        Generate CSV dataset file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to generated file
        """
        df = pd.DataFrame(self.sample_tickets)
        df.to_csv(filename, index=False)
        print(f"CSV dataset generated: {filename}")
        return filename
    
    def generate_json_dataset(self, filename: str = "sample_tickets.json") -> str:
        """
        Generate JSON dataset file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to generated file
        """
        with open(filename, 'w') as f:
            json.dump(self.sample_tickets, f, indent=2)
        print(f"JSON dataset generated: {filename}")
        return filename
    
    def get_dataset_stats(self) -> Dict:
        """
        Get statistics about the generated dataset.
        
        Returns:
            Dictionary containing dataset statistics
        """
        df = pd.DataFrame(self.sample_tickets)
        
        stats = {
            "total_tickets": len(self.sample_tickets),
            "categories": df['category'].value_counts().to_dict(),
            "priorities": df['priority'].value_counts().to_dict(),
            "statuses": df['status'].value_counts().to_dict(),
            "platforms": df['platform'].value_counts().to_dict(),
            "solved_rate": (df['solved'].sum() / len(df)) * 100,
            "avg_confidence": df['ai_confidence'].mean()
        }
        
        return stats
    
    def create_google_sheets_format(self) -> List[List[str]]:
        """
        Create data in Google Sheets format.
        
        Returns:
            List of rows for Google Sheets
        """
        headers = [
            'Ticket ID', 'Customer Email', 'Customer Name', 'Issue Summary',
            'Detailed Issue', 'Category', 'Priority', 'Status', 'Created Date',
            'Platform', 'AI Confidence', 'Solved', 'AI Response', 'Tags'
        ]
        
        rows = [headers]
        
        for ticket in self.sample_tickets:
            row = [
                ticket['ticket_id'],
                ticket['customer_email'],
                ticket['customer_name'],
                ticket['issue_summary'],
                ticket['detailed_issue'],
                ticket['category'],
                ticket['priority'],
                ticket['status'],
                ticket['created_date'],
                ticket['platform'],
                str(ticket['ai_confidence']),
                str(ticket['solved']),
                '; '.join(ticket['ai_response']),
                ', '.join(ticket['tags'])
            ]
            rows.append(row)
        
        return rows
