"""
Google Sheets Client Module
Handles all Google Sheets operations for the customer support system
"""

import pandas as pd
import json
from typing import List, Dict, Optional
import os

# Google API imports with error handling
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    print("Google API libraries not installed. Google Sheets integration will be disabled.")
    GOOGLE_AVAILABLE = False

class GoogleSheetsClient:
    """
    Google Sheets client for customer support system.
    """
    
    def __init__(self, credentials_file: str = None, sheet_id: str = None):
        """
        Initialize Google Sheets client.
        
        Args:
            credentials_file: Path to Google credentials JSON file
            sheet_id: Google Sheets document ID
        """
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not GOOGLE_AVAILABLE:
            print("Google API libraries not available.")
            return False
            
        try:
            # Define the scopes
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            
            creds = None
            # The file token.json stores the user's access and refresh tokens.
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        print(f"Credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('sheets', 'v4', credentials=creds)
            print("Successfully authenticated with Google Sheets")
            return True
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return False
    
    def read_tickets_from_sheet(self, sheet_name: str = 'Tickets') -> List[Dict]:
        """
        Read ticket data from Google Sheets.
        
        Args:
            sheet_name: Name of the sheet tab
            
        Returns:
            List of ticket dictionaries
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            range_name = f'{sheet_name}!A:N'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print("No data found in the sheet")
                return []
            
            # First row as headers
            headers = values[0]
            tickets = []
            
            for row in values[1:]:
                # Pad row with empty strings if it's shorter than headers
                while len(row) < len(headers):
                    row.append('')
                
                ticket = dict(zip(headers, row))
                tickets.append(ticket)
            
            print(f"Successfully read {len(tickets)} tickets from Google Sheets")
            return tickets
            
        except Exception as e:
            print(f"Error reading from Google Sheets: {str(e)}")
            return []
    
    def write_tickets_to_sheet(self, tickets: List[Dict], sheet_name: str = 'Tickets') -> bool:
        """
        Write tickets to Google Sheets.
        
        Args:
            tickets: List of ticket dictionaries
            sheet_name: Name of the sheet tab to write to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # Prepare data for writing
            if not tickets:
                print("No tickets to write")
                return False
            
            # Define headers
            headers = [
                'Ticket ID', 'Customer Email', 'Customer Name', 'Issue Summary',
                'Detailed Issue', 'Category', 'Priority', 'Status', 'Created Date',
                'Platform', 'AI Confidence', 'Solved', 'AI Response', 'Tags'
            ]
            
            # Prepare values array
            values = [headers]  # Header row
            
            for ticket in tickets:
                row = [
                    ticket.get('ticket_id', ''),
                    ticket.get('customer_email', ''),
                    ticket.get('customer_name', ''),
                    ticket.get('issue_summary', ''),
                    ticket.get('detailed_issue', ''),
                    ticket.get('category', ''),
                    ticket.get('priority', ''),
                    ticket.get('status', ''),
                    ticket.get('created_date', ''),
                    ticket.get('platform', ''),
                    str(ticket.get('confidence', 0)),
                    str(ticket.get('solved', False)),
                    '; '.join(ticket.get('ai_response', [])),
                    ', '.join(ticket.get('tags', []))
                ]
                values.append(row)
            
            # Clear existing data in the range
            clear_range = f'{sheet_name}!A:N'
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.sheet_id,
                range=clear_range
            ).execute()
            
            # Write new data
            body = {'values': values}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"Successfully wrote {len(tickets)} tickets to Google Sheets")
            return True
            
        except Exception as e:
            print(f"Error writing to Google Sheets: {str(e)}")
            return False
    
    def create_sample_dataset(self) -> bool:
        """
        Create a sample dataset in Google Sheets.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # Sample ticket data
            sample_data = [
                ['Ticket ID', 'Customer Email', 'Customer Name', 'Issue Summary', 'Detailed Issue', 'Category', 'Priority', 'Status', 'Created Date', 'Platform', 'AI Confidence', 'Solved', 'AI Response', 'Tags'],
                ['TK-1757338014', 'john.doe@gmail.com', 'John Doe', 'Login problem', 'Cannot login to my account. Getting authentication error.', 'Account Issues', 'High', 'Open', '2025-09-08', 'Web', '0.85', 'False', 'Reset password; Check email; Clear cache', 'account, login, technical'],
                ['TK-1757338020', 'jane.smith@gmail.com', 'Jane Smith', 'Payment issue', 'Payment not processing when I try to buy premium plan.', 'Payment Issues', 'High', 'Open', '2025-09-08', 'Web', '0.90', 'False', 'Check payment method; Verify billing address', 'payment, billing, urgent'],
                ['TK-1757340392', 'mike.johnson@gmail.com', 'Mike Johnson', 'Battery problem', 'iPhone battery drains quickly after latest update.', 'Battery Issues', 'Medium', 'Closed', '2025-09-08', 'Mobile', '0.88', 'True', 'Reduce brightness; Enable Low Power Mode', 'battery, mobile, performance'],
                ['TK-1757340456', 'sarah.wilson@gmail.com', 'Sarah Wilson', 'API integration help', 'Need help integrating your API with our CRM system.', 'Technical Support', 'Medium', 'Open', '2025-09-08', 'Web', '0.92', 'False', 'Check API documentation; Verify API key', 'api, technical, integration'],
                ['TK-1757340523', 'david.brown@gmail.com', 'David Brown', 'App crashing', 'Mobile app crashes when I try to upload photos.', 'Bug Reports', 'Critical', 'Open', '2025-09-08', 'Mobile', '0.95', 'False', 'Update app; Clear cache; Restart device', 'bug, mobile, crash'],
                ['TK-1757340589', 'lisa.garcia@gmail.com', 'Lisa Garcia', 'Feature request', 'Can you add dark mode feature to the web interface?', 'Feature Requests', 'Low', 'Open', '2025-09-08', 'Web', '0.75', 'False', 'Feature request noted; Will be reviewed', 'feature, ui, enhancement'],
                ['TK-1757340654', 'robert.miller@gmail.com', 'Robert Miller', 'Performance issue', 'Website is loading very slowly on mobile devices.', 'Performance Issues', 'Medium', 'In Progress', '2025-09-08', 'Mobile', '0.87', 'False', 'Check internet connection; Clear cache', 'performance, mobile, slow'],
                ['TK-1757340721', 'emily.davis@gmail.com', 'Emily Davis', 'Security concern', 'Received suspicious email claiming to be from your company.', 'Security Issues', 'Critical', 'Open', '2025-09-08', 'Web', '0.93', 'False', 'Do not click links; Report to security team', 'security, suspicious, urgent'],
                ['TK-1757340788', 'chris.anderson@gmail.com', 'Chris Anderson', 'Account locked', 'My account got locked after multiple failed login attempts.', 'Account Issues', 'High', 'Open', '2025-09-08', 'Web', '0.89', 'False', 'Reset password; Contact support for unlock', 'account, locked, urgent'],
                ['TK-1757340855', 'amanda.taylor@gmail.com', 'Amanda Taylor', 'Data export', 'How do I export my data in CSV format?', 'Technical Support', 'Low', 'Closed', '2025-09-08', 'Web', '0.82', 'True', 'Go to Settings > Export Data; Select CSV format', 'data, export, technical']
            ]
            
            # Write sample data
            body = {'values': sample_data}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range='Tickets!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print("Successfully created sample dataset in Google Sheets")
            return True
            
        except Exception as e:
            print(f"Error creating sample dataset: {str(e)}")
            return False
    
    def get_sheet_info(self) -> Dict:
        """
        Get information about the Google Sheet.
        
        Returns:
            Dictionary containing sheet information
        """
        if not self.service:
            if not self.authenticate():
                return {}
        
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()
            
            sheets = sheet_metadata.get('sheets', [])
            sheet_info = {
                'title': sheet_metadata.get('properties', {}).get('title', ''),
                'sheet_count': len(sheets),
                'sheets': []
            }
            
            for sheet in sheets:
                sheet_props = sheet.get('properties', {})
                sheet_info['sheets'].append({
                    'title': sheet_props.get('title', ''),
                    'sheet_id': sheet_props.get('sheetId', ''),
                    'row_count': sheet_props.get('gridProperties', {}).get('rowCount', 0),
                    'column_count': sheet_props.get('gridProperties', {}).get('columnCount', 0)
                })
            
            return sheet_info
            
        except Exception as e:
            print(f"Error getting sheet info: {str(e)}")
            return {}
