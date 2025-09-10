"""
AI Customer Support System - Main Application
Complete solution for customer query resolution and ticket management
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import uuid
from typing import List, Dict
import re
from openpyxl import Workbook, load_workbook
import time
from io import BytesIO

# Import our modules
from categorizer import TicketCategorizer
from resolver import QueryResolver
from sheets_client import GoogleSheetsClient
from tagger import TicketTagger

# Page configuration
st.set_page_config(
    page_title="AI Customer Support System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .ticket-card {
        background: #2d3748;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: #2d5a27;
        color: #68d391;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #68d391;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'tickets' not in st.session_state:
        st.session_state.tickets = []
    if 'google_sheet_data' not in st.session_state:
        st.session_state.google_sheet_data = []
    if 'categorizer' not in st.session_state:
        st.session_state.categorizer = TicketCategorizer()
    if 'resolver' not in st.session_state:
        st.session_state.resolver = QueryResolver()
    if 'tagger' not in st.session_state:
        st.session_state.tagger = TicketTagger()
    if 'sheets_client' not in st.session_state:
        st.session_state.sheets_client = GoogleSheetsClient()
    if 'csv_loaded' not in st.session_state:
        st.session_state.csv_loaded = False
    if 'excel_autosave' not in st.session_state:
        st.session_state.excel_autosave = True
    if 'excel_path' not in st.session_state:
        st.session_state.excel_path = 'tickets.xlsx'
    if 'pending_query' not in st.session_state:
        st.session_state.pending_query = None
    if 'last_created_ticket_id' not in st.session_state:
        st.session_state.last_created_ticket_id = None
    if 'last_created_ticket_ai' not in st.session_state:
        st.session_state.last_created_ticket_ai = []
    if 'flash_ticket_id' not in st.session_state:
        st.session_state.flash_ticket_id = None
    if 'flash_ticket_status' not in st.session_state:
        st.session_state.flash_ticket_status = None

def load_csv_data():
    """Load sample tickets from CSV file."""
    try:
        if os.path.exists('sample_tickets.csv'):
            df = pd.read_csv('sample_tickets.csv')
            
            # Convert DataFrame to list of dictionaries
            tickets = []
            for _, row in df.iterrows():
                # Parse AI response and tags from string format
                ai_response = eval(row['ai_response']) if isinstance(row['ai_response'], str) else row['ai_response']
                tags = eval(row['tags']) if isinstance(row['tags'], str) else row['tags']
                # Robust boolean parse for 'solved'
                raw_solved = row.get('solved', False)
                if isinstance(raw_solved, str):
                    solved_val = raw_solved.strip().lower() in ("true", "1", "yes", "y")
                else:
                    solved_val = bool(raw_solved)
                
                ticket = {
                    "ticket_id": row['ticket_id'],
                    "customer_email": row['customer_email'],
                    "customer_name": row['customer_name'],
                    "issue_summary": row['issue_summary'],
                    "detailed_issue": row['detailed_issue'],
                    "category": row['category'],
                    "priority": row['priority'],
                    "status": row['status'],
                    "created_date": row['created_date'],
                    "created_time": "12:00:00",  # Default time since CSV doesn't have time
                    "platform": row['platform'],
                    "contact_type": "CSV Import",
                    "ai_response": ai_response,
                    "confidence": float(row['ai_confidence']),
                    "solved": solved_val,
                    "tags": tags
                }
                tickets.append(ticket)
            
            return tickets
        else:
            st.error("CSV file 'sample_tickets.csv' not found!")
            return []
    except Exception as e:
        st.error(f"Error loading CSV data: {str(e)}")
        return []

def load_excel_data(excel_path: str) -> List[Dict]:
    """Load tickets from an Excel file into the in-memory ticket format."""
    try:
        if not os.path.exists(excel_path):
            st.error(f"Excel file not found: {excel_path}")
            return []

        df = pd.read_excel(excel_path, engine='openpyxl')

        tickets: List[Dict] = []
        for _, row in df.iterrows():
            # Parse JSON list fields if saved as strings
            ai_response = row.get('ai_response')
            if isinstance(ai_response, str):
                try:
                    ai_response = json.loads(ai_response)
                except Exception:
                    ai_response = [ai_response]

            tags = row.get('tags')
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = [tags]

            ticket = {
                "ticket_id": row.get('ticket_id', f"TK-{uuid.uuid4().hex[:12].upper()}"),
                "customer_email": row.get('customer_email', ''),
                "customer_name": row.get('customer_name', ''),
                "issue_summary": row.get('issue_summary', ''),
                "detailed_issue": row.get('detailed_issue', ''),
                "category": row.get('category', 'General'),
                "priority": row.get('priority', 'Medium'),
                "tags": tags if isinstance(tags, list) else [],
                "status": row.get('status', 'Open'),
                "created_date": str(row.get('created_date', datetime.now().strftime('%Y-%m-%d'))).split(' ')[0],
                "created_time": str(row.get('created_time', datetime.now().strftime('%H:%M:%S'))),
                "ai_response": ai_response if isinstance(ai_response, list) else [],
                "confidence": float(row.get('confidence', 0.8)),
                "solved": bool(row.get('solved', False)),
                "platform": row.get('platform', 'Web'),
                "contact_type": row.get('contact_type', 'Web Form')
            }
            tickets.append(ticket)

        return tickets
    except Exception as e:
        st.error(f"Error loading Excel data: {str(e)}")
        return []

def save_ticket_to_excel(ticket: Dict, excel_path: str) -> bool:
    """Append a single ticket to an Excel file, creating it if missing.

    Returns True on success, False otherwise.
    """
    try:
        # Open in append mode using openpyxl so we don't rewrite the file
        columns = [
            'ticket_id', 'customer_email', 'customer_name', 'issue_summary', 'detailed_issue',
            'category', 'priority', 'tags', 'status', 'created_date', 'created_time',
            'ai_response', 'confidence', 'solved', 'platform', 'contact_type'
        ]
        # Ensure workbook exists and has header
        if os.path.exists(excel_path):
            wb = load_workbook(excel_path)
            ws = wb.active
            if ws.max_row == 1 and ws.max_column == 1 and ws.cell(row=1, column=1).value is None:
                ws.append(columns)
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = 'Tickets'
            ws.append(columns)

        # Prepare row
        row_dict = dict(ticket)
        if isinstance(row_dict.get('ai_response'), list):
            row_dict['ai_response'] = json.dumps(row_dict['ai_response'])
        if isinstance(row_dict.get('tags'), list):
            row_dict['tags'] = json.dumps(row_dict['tags'])
        row = [row_dict.get(col, '') for col in columns]

        ws.append(row)

        # Safe write with retries and atomic replace
        temp_path = excel_path + ".tmp"
        last_err = None
        for attempt in range(3):
            try:
                wb.save(temp_path)
                # Atomic replace minimizes lock windows
                os.replace(temp_path, excel_path)
                last_err = None
                break
            except PermissionError as pe:
                last_err = pe
                time.sleep(0.8)
            except Exception as e:
                last_err = e
                break
        if last_err:
            # Fallback: save to autosave file to avoid data loss when main is locked
            autosave_path = os.path.splitext(excel_path)[0] + "_autosave.xlsx"
            try:
                wb.save(autosave_path)
                st.warning(f"Main Excel is locked. Saved to autosave: {autosave_path}. Close Excel/OneDrive lock to resume writing to {excel_path}.")
            except Exception:
                raise last_err
        return True
    except Exception as e:
        st.error(f"Failed to write ticket to Excel: {str(e)}")
        return False

def save_all_tickets_to_excel(tickets: List[Dict], excel_path: str) -> bool:
    """Overwrite the Excel file with all tickets (used after edits)."""
    try:
        columns = [
            'ticket_id', 'customer_email', 'customer_name', 'issue_summary', 'detailed_issue',
            'category', 'priority', 'tags', 'status', 'created_date', 'created_time',
            'ai_response', 'confidence', 'solved', 'platform', 'contact_type'
        ]
        rows = []
        for t in tickets:
            row = dict(t)
            if isinstance(row.get('ai_response'), list):
                row['ai_response'] = json.dumps(row['ai_response'])
            if isinstance(row.get('tags'), list):
                row['tags'] = json.dumps(row['tags'])
            rows.append([row.get(c, '') for c in columns])

        wb = Workbook()
        ws = wb.active
        ws.title = 'Tickets'
        ws.append(columns)
        for r in rows:
            ws.append(r)

        temp_path = excel_path + ".tmp"
        last_err = None
        for attempt in range(3):
            try:
                wb.save(temp_path)
                os.replace(temp_path, excel_path)
                last_err = None
                break
            except PermissionError as pe:
                last_err = pe
                time.sleep(0.8)
            except Exception as e:
                last_err = e
                break
        if last_err:
            autosave_path = os.path.splitext(excel_path)[0] + "_autosave.xlsx"
            try:
                wb.save(autosave_path)
                st.warning(f"Main Excel is locked. Saved edited tickets to autosave: {autosave_path}.")
            except Exception:
                raise last_err
        return True
    except Exception as e:
        st.error(f"Failed to write all tickets to Excel: {str(e)}")
        return False

def sync_autosave_to_main(excel_path: str) -> bool:
    """If an autosave exists, merge it into the main Excel and remove autosave on success."""
    try:
        base, ext = os.path.splitext(excel_path)
        autosave_path = base + "_autosave" + ext
        if not os.path.exists(autosave_path):
            st.info("No autosave file found to sync.")
            return False

        # Load both files (if main missing, treat as empty)
        df_auto = pd.read_excel(autosave_path, engine='openpyxl')
        if os.path.exists(excel_path):
            df_main = pd.read_excel(excel_path, engine='openpyxl')
            # Merge on ticket_id without duplicates (autosave rows win)
            if 'ticket_id' in df_main.columns and 'ticket_id' in df_auto.columns:
                df_combined = pd.concat([df_main[~df_main['ticket_id'].isin(df_auto['ticket_id'])], df_auto], ignore_index=True)
            else:
                df_combined = pd.concat([df_main, df_auto], ignore_index=True)
        else:
            df_combined = df_auto

        # Write combined back using safe writer
        tickets = df_combined.to_dict(orient='records')
        ok = save_all_tickets_to_excel(tickets, excel_path)
        if ok:
            try:
                os.remove(autosave_path)
            except OSError:
                pass
            st.success("Autosave merged into main Excel.")
            return True
        return False
    except Exception as e:
        st.error(f"Failed to sync autosave: {str(e)}")
        return False

def create_sidebar():
    """Create the sidebar with settings."""
    st.sidebar.title("⚙️ Settings")
    
    # Excel autosave settings
    st.sidebar.subheader("📗 Excel Settings")
    st.session_state.excel_autosave = st.sidebar.checkbox("Autosave tickets to Excel", value=st.session_state.excel_autosave)
    st.session_state.excel_path = st.sidebar.text_input("Excel file path", value=st.session_state.excel_path)
    # Offer retry merge if autosave exists
    base, ext = os.path.splitext(st.session_state.excel_path)
    autosave_candidate = base + "_autosave" + ext
    if os.path.exists(autosave_candidate):
        if st.sidebar.button("🔁 Retry write (merge autosave)"):
            with st.spinner("Merging autosave into main Excel..."):
                sync_autosave_to_main(st.session_state.excel_path)
    if st.sidebar.button("📥 Load tickets from Excel"):
        with st.spinner("Loading tickets from Excel..."):
            xlsx_tickets = load_excel_data(st.session_state.excel_path)
            if xlsx_tickets:
                st.session_state.tickets = xlsx_tickets
                st.success(f"✅ Loaded {len(xlsx_tickets)} tickets from Excel")
            else:
                st.error("❌ No tickets loaded from Excel")
    
    # CSV Data Import
    st.sidebar.subheader("📁 Data Import")
    if st.sidebar.button("📊 Load Sample Data from CSV", type="primary"):
        with st.spinner("Loading sample data from CSV..."):
            csv_tickets = load_csv_data()
            if csv_tickets:
                st.session_state.tickets = csv_tickets
                st.session_state.csv_loaded = True
                st.sidebar.success(f"✅ Loaded {len(csv_tickets)} tickets from CSV!")
            else:
                st.sidebar.error("❌ Failed to load CSV data")
    
    if st.session_state.csv_loaded:
        st.sidebar.success("✅ CSV data loaded!")
    
    # Google Sheets Configuration
    st.sidebar.subheader("📊 Google Sheets Integration")
    google_credentials = st.sidebar.file_uploader(
        "Upload Google Sheets Credentials (JSON)",
        type=['json'],
        help="Upload your Google Sheets API credentials"
    )
    
    sheet_id = st.sidebar.text_input(
        "Google Sheet ID",
        value="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        help="Enter your Google Sheet ID"
    )
    
    if google_credentials:
        with open('temp_credentials.json', 'wb') as f:
            f.write(google_credentials.getvalue())
        st.session_state.sheets_client = GoogleSheetsClient('temp_credentials.json', sheet_id)
        st.sidebar.success("✅ Credentials uploaded!")
    
    # AI Configuration
    st.sidebar.subheader("🤖 AI Configuration")
    model_type = st.sidebar.selectbox(
        "AI Model",
        ["GPT-3.5", "GPT-4", "Gemini Pro", "Local Model"],
        index=0
    )
    
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.8,
        step=0.05
    )
    
    # Knowledge Base
    st.sidebar.subheader("📚 Knowledge Base")
    if st.sidebar.button("🔄 Refresh Knowledge Base"):
        st.session_state.resolver.load_knowledge_base()
        st.sidebar.success("Knowledge base refreshed!")
    # Download KB as Excel
    try:
        kb = getattr(st.session_state.resolver, 'knowledge_base', {})
        if isinstance(kb, dict) and kb:
            # Prepare DataFrame
            kb_rows = []
            for key, data in kb.items():
                kb_rows.append({
                    'key': key,
                    'problem': data.get('problem', ''),
                    'keywords': ', '.join(data.get('keywords', [])),
                    'solutions': '\n'.join(data.get('solutions', [])),
                    'category': data.get('category', '')
                })
            if kb_rows:
                import pandas as _pd
                df_kb = _pd.DataFrame(kb_rows, columns=['key','problem','keywords','solutions','category'])
                bio = BytesIO()
                with _pd.ExcelWriter(bio, engine='openpyxl') as writer:
                    df_kb.to_excel(writer, index=False, sheet_name='KnowledgeBase')
                bio.seek(0)
                st.sidebar.download_button(
                    label="⬇ Download Knowledge Base (Excel)",
                    data=bio,
                    file_name="knowledge_base.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as _e:
        st.sidebar.error(f"KB export failed: {str(_e)}")
    
    return {
        'google_credentials': google_credentials,
        'sheet_id': sheet_id,
        'model_type': model_type,
        'confidence_threshold': confidence_threshold
    }

def display_main_header():
    """Display the main header."""
    st.markdown('<h1 class="main-header">🤖 AI Customer Support System</h1>', unsafe_allow_html=True)
    st.markdown("### Smart Query Resolution & Ticket Management")
    st.markdown("---")

def create_query_resolution_tab():
    """Create the main query resolution tab."""
    st.header("💬 Customer Query Resolution")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Customer Information")
        customer_email = st.text_input("Customer Email", placeholder="customer@example.com")
        customer_name = st.text_input("Customer Name", placeholder="John Doe")
        
        st.subheader("Issue Details")
        issue_summary = st.text_input("Issue Summary", placeholder="Brief description of the problem")
        detailed_issue = st.text_area("Detailed Issue Description", placeholder="Please provide more details about your issue...", height=100)
        
        if st.button("🔍 Get AI Response", type="primary"):
            if customer_email and issue_summary and detailed_issue:
                with st.spinner("Analyzing your query..."):
                    # Get AI response using resolver
                    query_response = st.session_state.resolver.resolve_query(detailed_issue)
                    # Temporarily store pending query context
                    pending_ticket_id = f"TK-{uuid.uuid4().hex[:12].upper()}"
                    st.session_state.pending_query = {
                        'customer_email': customer_email,
                        'customer_name': customer_name,
                        'issue_summary': issue_summary,
                        'detailed_issue': detailed_issue,
                        'query_response': query_response,
                        'pending_ticket_id': pending_ticket_id
                    }
                
            else:
                st.error("Please fill in all required fields")

    # If we have a pending AI response, display it with satisfaction buttons
    if st.session_state.pending_query is not None:
        pq = st.session_state.pending_query
        st.subheader("🤖 AI Response")
        # Show pending ticket id first
        if pq.get('pending_ticket_id'):
            st.success(f"Ticket ID: {pq['pending_ticket_id']}")
        st.info(f"Category: {pq['query_response']['category']} | Confidence: {pq['query_response']['confidence']:.2f}")
        st.write("**Recommended Solutions:**")
        for i, solution in enumerate(pq['query_response']["solutions"], 1):
            st.write(f"{i}. {solution}")

        col_ok, col_not = st.columns(2)
        with col_ok:
            if st.button("✅ Satisfied - Close without ticket"):
                # Create a closed ticket (documentation of resolved query)
                response = dict(pq['query_response'])
                response['solved'] = True
                ticket = create_ticket(
                    pq['customer_email'], pq['customer_name'], pq['issue_summary'], pq['detailed_issue'],
                    response, status="Closed", solved=True, ticket_id_override=pq.get('pending_ticket_id')
                )
                st.session_state.last_created_ticket_id = ticket['ticket_id']
                st.session_state.last_created_ticket_ai = ticket['ai_response']
                st.session_state.flash_ticket_id = ticket['ticket_id']
                st.session_state.flash_ticket_status = ticket['status']
                st.success("Great! Marked as resolved and saved.")
                st.session_state.pending_query = None
                st.rerun()

        with col_not:
            if st.button("❌ Not satisfied - Create support ticket"):
                response = dict(pq['query_response'])
                response['solved'] = False
                ticket = create_ticket(
                    pq['customer_email'], pq['customer_name'], pq['issue_summary'], pq['detailed_issue'],
                    response, status="Open", solved=False, ticket_id_override=pq.get('pending_ticket_id')
                )
                st.session_state.last_created_ticket_id = ticket['ticket_id']
                st.session_state.last_created_ticket_ai = ticket['ai_response']
                st.session_state.flash_ticket_id = ticket['ticket_id']
                st.session_state.flash_ticket_status = ticket['status']
                st.warning(f"Ticket Created: {ticket['ticket_id']} - Our team will follow up.")
                st.session_state.pending_query = None
                st.rerun()
    
    with col2:
        st.subheader("📊 Quick Stats")
        total_tickets = len(st.session_state.tickets)
        solved_tickets = sum(1 for t in st.session_state.tickets if t["solved"])
        
        st.metric("Total Tickets", total_tickets)
        st.metric("Solved Today", solved_tickets)
        st.metric("Resolution Rate", f"{(solved_tickets/total_tickets*100):.1f}%" if total_tickets > 0 else "0%")
        
        # Last created ticket banner
        if st.session_state.last_created_ticket_id:
            st.markdown(f"**Last Ticket:** {st.session_state.last_created_ticket_id}")
            if st.session_state.last_created_ticket_ai:
                st.write("**AI Responses:**")
                for i, resp in enumerate(st.session_state.last_created_ticket_ai, 1):
                    st.write(f"{i}. {resp}")
        # One-time flash banner right after creation
        if st.session_state.flash_ticket_id:
            st.success(f"🎫 Ticket Created: {st.session_state.flash_ticket_id} | Status: {st.session_state.flash_ticket_status}")
            # Clear flash so it doesn't persist across reruns
            st.session_state.flash_ticket_id = None
            st.session_state.flash_ticket_status = None

        # Recent tickets
        if st.session_state.tickets:
            st.subheader("📋 Recent Tickets")
            for ticket in st.session_state.tickets[-3:]:
                with st.container():
                    st.write(f"**{ticket['ticket_id']}**")
                    st.write(f"*{ticket['issue_summary']}*")
                    st.write(f"Status: {ticket['status']}")

def create_ticket(customer_email: str, customer_name: str, issue_summary: str, detailed_issue: str, query_response: Dict, status: str = "Open", solved: bool | None = None, ticket_id_override: str | None = None) -> Dict:
    """Create a new support ticket using categorizer and tagger."""
    # Use high-entropy unique ID to avoid collisions in the same second
    ticket_id = ticket_id_override or f"TK-{uuid.uuid4().hex[:12].upper()}"
    
    # Use categorizer to categorize the ticket
    category_result = st.session_state.categorizer.categorize(detailed_issue)
    
    # Use tagger to extract tags
    tags = st.session_state.tagger.extract_tags(detailed_issue)
    
    # Decide solved flag
    solved_flag = query_response["solved"] if solved is None else solved

    ticket = {
        "ticket_id": ticket_id,
        "customer_email": customer_email,
        "customer_name": customer_name,
        "issue_summary": issue_summary,
        "detailed_issue": detailed_issue,
        "category": category_result["category"],
        "priority": category_result["priority"],
        "tags": tags,
        "status": status,
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "created_time": datetime.now().strftime("%H:%M:%S"),
        "ai_response": query_response["solutions"],
        "confidence": query_response["confidence"],
        "solved": solved_flag,
        "platform": "Web",
        "contact_type": "Web Form"
    }
    
    st.session_state.tickets.append(ticket)
    # Persist to Excel automatically
    if st.session_state.excel_autosave:
        success_excel = save_ticket_to_excel(ticket, st.session_state.excel_path)
        if success_excel:
            st.toast(f"Ticket saved to Excel ({st.session_state.excel_path})")
    return ticket

def create_ticket_management_tab():
    """Create ticket management tab."""
    st.header("🎫 Ticket Management")
    
    if st.session_state.tickets:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Open", "Closed", "In Progress"])
        with col2:
            priority_filter = st.selectbox("Filter by Priority", ["All", "High", "Medium", "Low"])
        with col3:
            category_filter = st.selectbox("Filter by Category", ["All"] + list(set(t["category"] for t in st.session_state.tickets)))
        
        # Filter tickets
        filtered_tickets = st.session_state.tickets
        if status_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t["status"] == status_filter]
        if priority_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t["priority"] == priority_filter]
        if category_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t["category"] == category_filter]
        
        # Display tickets
        for idx, ticket in enumerate(filtered_tickets):
            with st.expander(f"🎫 {ticket['ticket_id']} - {ticket['issue_summary']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer:** {ticket['customer_name']} ({ticket['customer_email']})")
                    st.write(f"**Category:** {ticket['category']}")
                    st.write(f"**Priority:** {ticket['priority']}")
                    st.write(f"**Status:** {ticket['status']}")
                    st.write(f"**Created:** {ticket['created_date']} {ticket['created_time']}")
                
                with col2:
                    st.write(f"**Confidence:** {ticket['confidence']:.2f}")
                    st.write(f"**Solved:** {'✅ Yes' if ticket['solved'] else '❌ No'}")
                    st.write(f"**Platform:** {ticket['platform']}")
                    st.write(f"**Tags:** {', '.join(ticket['tags'])}")
                
                st.write("**Issue Description:**")
                st.write(ticket['detailed_issue'])
                
                st.write("**AI Response:**")
                for response in ticket['ai_response']:
                    st.write(f"• {response}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Mark Solved", key=f"solve_{ticket['ticket_id']}_{idx}"):
                        ticket['status'] = "Closed"
                        ticket['solved'] = True
                        if st.session_state.excel_autosave:
                            save_all_tickets_to_excel(st.session_state.tickets, st.session_state.excel_path)
                        st.success("Ticket marked as solved!")
                        st.rerun()
                
                with col2:
                    if st.button(f"🔄 In Progress", key=f"progress_{ticket['ticket_id']}_{idx}"):
                        ticket['status'] = "In Progress"
                        if st.session_state.excel_autosave:
                            save_all_tickets_to_excel(st.session_state.tickets, st.session_state.excel_path)
                        st.success("Ticket status updated!")
                        st.rerun()
                
                with col3:
                    edit_key = f"edit_mode_{ticket['ticket_id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False
                    if st.button(f"📝 Edit", key=f"edit_{ticket['ticket_id']}_{idx}"):
                        st.session_state[edit_key] = not st.session_state[edit_key]

                if st.session_state.get(edit_key, False):
                    st.markdown("---")
                    st.subheader("Edit Ticket")
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        new_summary = st.text_input("Issue Summary", value=ticket['issue_summary'], key=f"sum_{ticket['ticket_id']}_{idx}")
                        new_status = st.selectbox("Status", ["Open", "In Progress", "Closed"], index=["Open","In Progress","Closed"].index(ticket['status']), key=f"stat_{ticket['ticket_id']}_{idx}")
                        new_priority = st.selectbox("Priority", ["Low","Medium","High","Critical"], index=["Low","Medium","High","Critical"].index(ticket['priority']) if ticket['priority'] in ["Low","Medium","High","Critical"] else 1, key=f"prio_{ticket['ticket_id']}_{idx}")
                        new_solved = st.checkbox("Solved", value=ticket['solved'], key=f"solv_{ticket['ticket_id']}_{idx}")
                    with e_col2:
                        new_category = st.text_input("Category", value=ticket['category'], key=f"cat_{ticket['ticket_id']}_{idx}")
                        new_tags_str = st.text_input("Tags (comma separated)", value=", ".join(ticket['tags']), key=f"tags_{ticket['ticket_id']}_{idx}")
                    new_detail = st.text_area("Detailed Issue Description", value=ticket['detailed_issue'], key=f"det_{ticket['ticket_id']}_{idx}")

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("💾 Save Changes", key=f"save_{ticket['ticket_id']}_{idx}"):
                            ticket['issue_summary'] = new_summary
                            ticket['detailed_issue'] = new_detail
                            ticket['status'] = new_status
                            ticket['priority'] = new_priority
                            ticket['category'] = new_category
                            ticket['solved'] = bool(new_solved)
                            ticket['tags'] = [t.strip() for t in new_tags_str.split(',') if t.strip()]
                            if st.session_state.excel_autosave:
                                ok = save_all_tickets_to_excel(st.session_state.tickets, st.session_state.excel_path)
                                if ok:
                                    st.toast("Edits saved to Excel")
                            st.session_state[edit_key] = False
                            st.success("Ticket updated.")
                            st.rerun()
                    with b2:
                        if st.button("✖ Cancel", key=f"cancel_{ticket['ticket_id']}_{idx}"):
                            st.session_state[edit_key] = False
    else:
        st.info("No tickets created yet. Go to 'Query Resolution' tab to create tickets.")

def create_google_sheets_tab():
    """Create Google Sheets integration tab."""
    st.header("📊 Data Integration & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Import Data")
        
        # CSV Import
        st.write("**From CSV File:**")
        if st.button("📊 Load Sample Data from CSV", type="primary"):
            with st.spinner("Loading sample data from CSV..."):
                csv_tickets = load_csv_data()
                if csv_tickets:
                    st.session_state.tickets = csv_tickets
                    st.session_state.csv_loaded = True
                    st.success(f"✅ Loaded {len(csv_tickets)} tickets from CSV!")
                else:
                    st.error("❌ Failed to load CSV data")
        
        # Google Sheets Import
        st.write("**From Google Sheets:**")
        if st.button("📊 Load Data from Google Sheets"):
            if st.session_state.sheets_client.sheet_id:
                with st.spinner("Loading data from Google Sheets..."):
                    tickets = st.session_state.sheets_client.read_tickets_from_sheet()
                    
                    if tickets:
                        st.session_state.google_sheet_data = tickets
                        st.success(f"✅ Loaded {len(tickets)} records from Google Sheets")
                        
                        # Display data
                        df = pd.DataFrame(tickets)
                        st.dataframe(df)
                    else:
                        st.error("❌ No data found in Google Sheets")
            else:
                st.error("❌ Please configure Google Sheet ID in settings")
    
    with col2:
        st.subheader("📤 Export Data")
        
        if st.session_state.tickets:
            # CSV Export
            st.write("**Export to CSV:**")
            if st.button("💾 Export Tickets to CSV", type="primary"):
                try:
                    df = pd.DataFrame(st.session_state.tickets)
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"tickets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    st.success("✅ CSV export ready for download!")
                except Exception as e:
                    st.error(f"❌ Error creating CSV export: {str(e)}")
            
            # Google Sheets Export
            st.write("**Export to Google Sheets:**")
            if st.button("💾 Export Tickets to Google Sheets"):
                with st.spinner("Exporting tickets to Google Sheets..."):
                    success = st.session_state.sheets_client.write_tickets_to_sheet(st.session_state.tickets)
                    
                    if success:
                        st.success("✅ Tickets exported to Google Sheets successfully!")
                    else:
                        st.error("❌ Failed to export tickets to Google Sheets")
        else:
            st.info("No tickets to export. Create some tickets first!")

def create_analytics_tab():
    """Create analytics and reporting tab."""
    st.header("📈 Analytics & Reports")
    
    if st.session_state.tickets:
        # Metrics
        total_tickets = len(st.session_state.tickets)
        solved_tickets = sum(1 for t in st.session_state.tickets if t["solved"])
        open_tickets = sum(1 for t in st.session_state.tickets if t["status"] == "Open")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tickets", total_tickets)
        with col2:
            st.metric("Solved Tickets", solved_tickets)
        with col3:
            st.metric("Open Tickets", open_tickets)
        with col4:
            st.metric("Resolution Rate", f"{(solved_tickets/total_tickets*100):.1f}%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution
            category_counts = {}
            for ticket in st.session_state.tickets:
                category = ticket["category"]
                category_counts[category] = category_counts.get(category, 0) + 1
            
            if category_counts:
                fig_cat = px.pie(
                    values=list(category_counts.values()),
                    names=list(category_counts.keys()),
                    title="Tickets by Category"
                )
                st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Priority distribution
            priority_counts = {}
            for ticket in st.session_state.tickets:
                priority = ticket["priority"]
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            if priority_counts:
                fig_priority = px.bar(
                    x=list(priority_counts.keys()),
                    y=list(priority_counts.values()),
                    title="Tickets by Priority",
                    color=list(priority_counts.keys()),
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_priority, use_container_width=True)
        
        # Daily ticket trends
        if len(st.session_state.tickets) > 1:
            st.subheader("📊 Daily Ticket Trends")
            daily_counts = {}
            for ticket in st.session_state.tickets:
                date = ticket["created_date"]
                daily_counts[date] = daily_counts.get(date, 0) + 1
            
            if daily_counts:
                df_daily = pd.DataFrame(list(daily_counts.items()), columns=['Date', 'Tickets'])
                fig_trend = px.line(df_daily, x='Date', y='Tickets', title='Tickets Created Over Time')
                st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No tickets available for analytics. Create some tickets first!")

def main():
    """Main application function."""
    initialize_session_state()
    
    # Create sidebar
    settings = create_sidebar()
    
    # Display main header
    display_main_header()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Query Resolution", 
        "🎫 Ticket Management", 
        "📊 Data Integration",
        "📈 Analytics"
    ])
    
    with tab1:
        create_query_resolution_tab()
    
    with tab2:
        create_ticket_management_tab()
    
    with tab3:
        create_google_sheets_tab()
    
    with tab4:
        create_analytics_tab()

if __name__ == "__main__":
    main()
