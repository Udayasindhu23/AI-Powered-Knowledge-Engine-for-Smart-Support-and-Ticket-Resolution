"""
Chatbot Module
Interactive chatbot for customer support with conversation history and context management
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import json
import requests
import re
from urllib.parse import quote_plus
import os


class ChatMessage:
    """Represents a single chat message."""
    
    def __init__(self, role: str, content: str, timestamp: str = None, message_id: str = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.message_id = message_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary for storage."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp,
            'message_id': self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        """Create message from dictionary."""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=data.get('timestamp'),
            message_id=data.get('message_id')
        )

class Chatbot:
    """Interactive chatbot for customer support."""
    
    def __init__(self, resolver, categorizer=None, tagger=None, google_api_key=None, google_cse_id=None):
        """Initialize the chatbot with required components."""
        self.resolver = resolver
        self.categorizer = categorizer
        self.tagger = tagger
        self.conversation_history = []
        self.current_context = {}
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id
        self.search_enabled = bool(google_api_key and google_cse_id)
        
    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the conversation history."""
        message = ChatMessage(role, content)
        self.conversation_history.append(message)
        return message
    
    def get_conversation_context(self) -> str:
        """Get the conversation context for AI processing."""
        if not self.conversation_history:
            return ""
        
        context_parts = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages for context
            context_parts.append(f"{msg.role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def process_user_message(self, user_input: str) -> Dict:
        """Process user message and generate response."""
        # Add user message to history
        self.add_message("user", user_input)
        
        # Ticket lookup short-circuit: detect ticket IDs like TK-XXXXXXXXXXXX
        ticket_lookup = self._maybe_handle_ticket_lookup(user_input)
        if ticket_lookup is not None:
            # Add assistant response and return early
            assistant_message = self.add_message("assistant", ticket_lookup)
            self.current_context.update({'last_query': user_input, 'last_response': ticket_lookup})
            return {
                'response': ticket_lookup,
                'query_response': {'solutions': [], 'confidence': 1.0, 'category': 'Ticket Lookup'},
                'message_id': assistant_message.message_id,
                'timestamp': assistant_message.timestamp
            }

        # Get conversation context
        context = self.get_conversation_context()
        
        # Use resolver to get AI response
        query_response = self.resolver.resolve_query(user_input)
        
        # Generate contextual response
        response_content = self._generate_contextual_response(user_input, query_response, context)
        
        # Add assistant response to history
        assistant_message = self.add_message("assistant", response_content)
        
        # Update context
        self.current_context.update({
            'last_query': user_input,
            'last_response': response_content,
            'confidence': query_response.get('confidence', 0.0),
            'category': query_response.get('category', 'General')
        })
        
        return {
            'response': response_content,
            'query_response': query_response,
            'message_id': assistant_message.message_id,
            'timestamp': assistant_message.timestamp
        }
    
    def _generate_contextual_response(self, user_input: str, query_response: Dict, context: str) -> str:
        """Generate a contextual response based on conversation history."""
        solutions = query_response.get('solutions', [])
        confidence = query_response.get('confidence', 0.0)
        category = query_response.get('category', 'General')
        
        # Check if this is a follow-up question
        is_follow_up = self._is_follow_up_question(user_input, context)
        
        if is_follow_up and self.conversation_history:
            # Generate follow-up response
            response = self._generate_follow_up_response(user_input, solutions, confidence)
        else:
            # Generate initial response
            response = self._generate_initial_response(user_input, solutions, confidence, category)
        
        # Enhance with Google search if enabled
        enhanced_response = self._enhance_response_with_search(user_input, query_response, response)
        
        return enhanced_response
    
    def _is_follow_up_question(self, user_input: str, context: str) -> bool:
        """Check if the user input is a follow-up question."""
        follow_up_indicators = [
            "what about", "how about", "what if", "can you", "could you",
            "tell me more", "explain", "clarify", "elaborate", "more details",
            "what else", "anything else", "other options", "alternatives"
        ]
        
        user_lower = user_input.lower()
        return any(indicator in user_lower for indicator in follow_up_indicators)
    
    def _generate_initial_response(self, user_input: str, solutions: List[str], confidence: float, category: str) -> str:
        """Generate initial response to user query."""
        if confidence > 0.7:
            response = f"I understand you're having issues with {category.lower()}. Here are some solutions that should help:\n\n"
            for i, solution in enumerate(solutions[:3], 1):
                response += f"{i}. {solution}\n"
            response += f"\nThese solutions have a {confidence:.0%} confidence match with your issue. Would you like me to explain any of these in more detail?"
        elif confidence > 0.4:
            response = f"Based on your query, I found some general solutions that might help:\n\n"
            for i, solution in enumerate(solutions[:2], 1):
                response += f"{i}. {solution}\n"
            response += "\nIf these don't solve your issue, could you provide more specific details about what you're experiencing?"
        else:
            # Always provide at least a couple of actionable steps even at low confidence
            response = "Here are a couple of steps that often help in similar situations:\n\n"
            if solutions:
                for i, solution in enumerate(solutions[:2], 1):
                    response += f"{i}. {solution}\n"
                response += "\nIf these don't help, please share more specific details so I can give a targeted fix."
            else:
                response += (
                    "1. Restart the device/app and make sure it's updated to the latest version.\n"
                    "2. Check network/storage and try again.\n\n"
                    "If this persists, please share more details so I can pinpoint the cause."
                )
        
        return response
    
    def _generate_follow_up_response(self, user_input: str, solutions: List[str], confidence: float) -> str:
        """Generate follow-up response to user query."""
        if "explain" in user_input.lower() or "more details" in user_input.lower():
            if solutions:
                response = "Let me provide more detailed information:\n\n"
                for i, solution in enumerate(solutions, 1):
                    response += f"{i}. {solution}\n"
                response += "\nIs there anything specific about these solutions you'd like me to clarify?"
            else:
                response = "I'd be happy to provide more details. Could you specify which aspect you'd like me to explain further?"
        elif "what else" in user_input.lower() or "other options" in user_input.lower():
            if len(solutions) > 3:
                response = "Here are additional options:\n\n"
                for i, solution in enumerate(solutions[3:], 4):
                    response += f"{i}. {solution}\n"
            else:
                response = "I've provided the main solutions above. If these don't work for your specific situation, I'd recommend contacting our support team for personalized assistance."
        else:
            response = "I understand you need more help. Could you tell me which of the previous solutions you've tried, or if you're experiencing something different?"
        
        return response

    # ---- Ticket lookup helpers ----
    def _maybe_handle_ticket_lookup(self, user_input: str) -> Optional[str]:
        """
        If the user input contains a ticket id (e.g., TK-XXXXXXXXXXXX),
        fetch the ticket from in-memory tickets or Google Sheets and
        return a formatted summary. Returns None if not a lookup.
        """
        try:
            # Be flexible: allow IDs like TK-XXXXXXXX (letters/digits), ignore word boundaries
            m = re.search(r"(TK-[A-Z0-9]{6,})", user_input.upper())
            if not m:
                return None
            ticket_id = m.group(0)

            # 1) Search in memory
            ticket = None
            tickets = getattr(st.session_state, 'tickets', []) or []
            for t in tickets:
                if str(t.get('ticket_id', '')).upper() == ticket_id:
                    ticket = t
                    break

            # 2) If not found, fallback to local Excel (no JSON/Google required)
            if ticket is None:
                try:
                    excel_path = getattr(st.session_state, 'excel_path', 'tickets.xlsx')
                    if excel_path and os.path.exists(excel_path):
                        import pandas as _pd
                        df = _pd.read_excel(excel_path, engine='openpyxl')
                        rows = df.to_dict(orient='records')
                        mapped = [self._map_sheet_row_to_ticket(row) for row in rows]
                        # Update in-memory cache
                        if mapped:
                            if not isinstance(st.session_state.tickets, list):
                                st.session_state.tickets = []
                            seen = {str(t.get('ticket_id')) for t in st.session_state.tickets}
                            for mt in mapped:
                                if str(mt.get('ticket_id')) not in seen:
                                    st.session_state.tickets.append(mt)
                                    seen.add(str(mt.get('ticket_id')))
                        for t in mapped:
                            if str(t.get('ticket_id', '')).upper() == ticket_id:
                                ticket = t
                                break
                except Exception:
                    pass

            if ticket is None:
                return f"I couldn't find ticket {ticket_id}. Please ensure it's in the app or Google Sheet and try again."

            return self._format_ticket_summary(ticket)
        except Exception:
            return None

    def _map_sheet_row_to_ticket(self, row: Dict) -> Dict:
        """Map a Google Sheets row (dict with human headers) to internal ticket schema."""
        if not isinstance(row, dict):
            return {}
        # Accept header variations
        def g(key: str, *alts: str) -> str:
            for k in (key,)+alts:
                if k in row:
                    return row.get(k, '')
            return ''
        # Parse simple list fields
        ai_resp = [s.strip() for s in str(g('AI Response')).split(';') if s.strip()] if g('AI Response') else []
        tags = [s.strip() for s in str(g('Tags')).split(',') if s.strip()] if g('Tags') else []
        solved_val = str(g('Solved')).strip().lower() in {"true","1","yes","y"}
        confidence_val = 0.0
        try:
            confidence_val = float(g('AI Confidence'))
        except Exception:
            confidence_val = 0.0
        return {
            'ticket_id': g('Ticket ID'),
            'customer_email': g('Customer Email'),
            'customer_name': g('Customer Name'),
            'issue_summary': g('Issue Summary'),
            'detailed_issue': g('Detailed Issue'),
            'category': g('Category'),
            'priority': g('Priority'),
            'status': g('Status'),
            'created_date': g('Created Date'),
            'created_time': g('Created Time'),
            'platform': g('Platform'),
            'contact_type': g('Contact Type'),
            'ai_response': ai_resp,
            'confidence': confidence_val,
            'solved': solved_val,
            'tags': tags,
            'sentiment': ''
        }

    def _format_ticket_summary(self, t: Dict) -> str:
        """Format a ticket dict into a human answer for the chat."""
        lines = []
        lines.append(f"Ticket {t.get('ticket_id','')}")
        lines.append(f"Status: {t.get('status','Open')} | Priority: {t.get('priority','Medium')} | Category: {t.get('category','General')}")
        if t.get('customer_name') or t.get('customer_email'):
            lines.append(f"Customer: {t.get('customer_name','')} <{t.get('customer_email','')}>")
        if t.get('created_date') or t.get('created_time'):
            lines.append(f"Created: {t.get('created_date','')} {t.get('created_time','')}")
        if t.get('issue_summary'):
            lines.append(f"Issue: {t.get('issue_summary')}")
        if t.get('detailed_issue'):
            lines.append(f"Details: {t.get('detailed_issue')}")
        if isinstance(t.get('ai_response'), list) and t['ai_response']:
            lines.append("AI Suggested Solutions:")
            for i, s in enumerate(t['ai_response'][:5], 1):
                lines.append(f"  {i}. {s}")
        if t.get('tags'):
            lines.append(f"Tags: {', '.join(t.get('tags', []))}")
        if t.get('sentiment'):
            lines.append(f"Sentiment: {t.get('sentiment')}")
        # Add explicit note if ticket is closed but still provide solutions
        if str(t.get('status','')).strip().lower() == 'closed':
            lines.append("Note: This ticket is closed. The solutions above are the resolution steps that were recommended.")
        return "\n".join(lines)
    
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        self.current_context = {}
    
    def get_conversation_summary(self) -> Dict:
        """Get a summary of the current conversation."""
        if not self.conversation_history:
            return {"message_count": 0, "last_message": None}
        
        return {
            "message_count": len(self.conversation_history),
            "last_message": self.conversation_history[-1].content if self.conversation_history else None,
            "conversation_duration": self._calculate_duration(),
            "context": self.current_context
        }
    
    def _calculate_duration(self) -> str:
        """Calculate conversation duration."""
        if len(self.conversation_history) < 2:
            return "0 minutes"
        
        try:
            start_time = datetime.strptime(self.conversation_history[0].timestamp, "%H:%M:%S")
            end_time = datetime.strptime(self.conversation_history[-1].timestamp, "%H:%M:%S")
            duration = end_time - start_time
            return f"{duration.seconds // 60} minutes"
        except:
            return "Unknown"
    
    def export_conversation(self) -> List[Dict]:
        """Export conversation history for storage."""
        return [msg.to_dict() for msg in self.conversation_history]
    
    def import_conversation(self, conversation_data: List[Dict]):
        """Import conversation history from storage."""
        self.conversation_history = [ChatMessage.from_dict(msg) for msg in conversation_data]
    
    def search_google(self, query: str, num_results: int = 3) -> List[Dict]:
        """
        Search Google for additional information.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, snippet, and link
        """
        if not self.search_enabled:
            return []
        
        try:
            # Google Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': num_results,
                'safe': 'medium'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'display_link': item.get('displayLink', '')
                })
            
            return results
            
        except Exception as e:
            st.warning(f"Google search failed: {str(e)}")
            return []
    
    def _should_search_google(self, user_input: str, query_response: Dict) -> bool:
        """
        Determine if we should search Google for additional information.
        
        Args:
            user_input: User's message
            query_response: Response from knowledge base
            
        Returns:
            True if should search Google
        """
        # Search if confidence is low or user asks for latest information
        low_confidence = query_response.get('confidence', 0) < 0.5
        
        # Keywords that suggest need for current information
        current_info_keywords = [
            'latest', 'recent', 'new', 'update', 'current', 'today', 'now',
            'news', 'trending', 'popular', 'best', 'top', 'reviews'
        ]
        
        user_lower = user_input.lower()
        needs_current_info = any(keyword in user_lower for keyword in current_info_keywords)
        
        # Search if asking about specific products, services, or companies
        specific_queries = [
            'what is', 'how to', 'where to', 'when', 'why', 'who',
            'compare', 'difference', 'vs', 'alternative'
        ]
        
        is_specific_query = any(phrase in user_lower for phrase in specific_queries)
        
        return low_confidence or needs_current_info or is_specific_query
    
    def _format_search_results(self, search_results: List[Dict]) -> str:
        """
        Format search results for display.
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted string of search results
        """
        if not search_results:
            return ""
        
        formatted = "\n\n**🔍 Additional Information from Google Search:**\n"
        
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            link = result.get('link', '#')
            
            # Truncate snippet if too long
            if len(snippet) > 150:
                snippet = snippet[:147] + "..."
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   {snippet}\n"
            formatted += f"   [Read more]({link})\n\n"
        
        return formatted
    
    def _enhance_response_with_search(self, user_input: str, query_response: Dict, base_response: str) -> str:
        """
        Enhance the base response with Google search results.
        
        Args:
            user_input: User's message
            query_response: Response from knowledge base
            base_response: Original response
            
        Returns:
            Enhanced response with search results
        """
        if not self.search_enabled:
            return base_response
        
        # Determine if we should search: allow global override and configurable threshold
        try:
            search_always = bool(getattr(st.session_state, 'search_always', False))
            conf_threshold = float(getattr(st.session_state, 'search_conf_threshold', 0.7))
        except Exception:
            search_always = False
            conf_threshold = 0.7

        if not search_always:
            # Use generalized trigger conditions
            low_confidence = query_response.get('confidence', 0) < conf_threshold
            should_search = low_confidence or self._should_search_google(user_input, query_response)
            if not should_search:
                return base_response
        
        # Create search query (broader intent coverage)
        search_query = f"{user_input} troubleshooting support fix steps solution"
        
        # Add context from conversation if available
        if self.current_context.get('category'):
            search_query += f" {self.current_context['category']}"
        
        # Perform search
        search_results = self.search_google(search_query, num_results=2)
        
        if search_results:
            # Add search results to response
            enhanced_response = base_response
            enhanced_response += self._format_search_results(search_results)
            
            # Add disclaimer
            enhanced_response += "\n*Note: External search results are provided for additional context and may not be from our official support channels.*"
            
            return enhanced_response
        
        return base_response
