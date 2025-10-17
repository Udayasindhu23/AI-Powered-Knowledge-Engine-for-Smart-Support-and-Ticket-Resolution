"""
Query Resolver Module
Handles customer query resolution using knowledge base with FAISS RAG

Supports loading the knowledge base from an Excel file (knowledge_base.xlsx)
with the following columns:
 - key: unique identifier (e.g., phone_screen_issues)
 - problem: brief problem statement
 - keywords: comma-separated keywords (e.g., phone,screen,touch)
 - solutions: one solution per line or separated by ';'
 - category: category label

If the Excel file is not present or fails to load, falls back to a built-in KB.
Uses FAISS vector search for semantic similarity matching.
"""

import json
from typing import Dict, List
import os
import pandas as pd
import re
from rag_engine import RAGEngine, create_documents_from_knowledge_base

class QueryResolver:
    """
    AI-powered query resolution system with FAISS RAG.
    """
    
    def __init__(self, use_rag: bool = True):
        """Initialize the resolver."""
        self.use_rag = use_rag
        self.knowledge_base = self.load_knowledge_base()
        self.rag_engine = None
        
        if self.use_rag:
            try:
                self.rag_engine = RAGEngine()
                # Convert knowledge base to documents and add to RAG
                documents = create_documents_from_knowledge_base(self.knowledge_base)
                self.rag_engine.add_documents(documents)
                print("✅ RAG engine initialized with FAISS")
            except Exception as e:
                print(f"⚠️ RAG engine initialization failed: {e}")
                print("Falling back to keyword-based search")
                self.use_rag = False
    
    def load_knowledge_base(self) -> Dict:
        """Load the knowledge base for query resolution.

        Tries Excel (knowledge_base.xlsx) first; falls back to defaults.
        """
        # Try Excel first
        excel_path = 'knowledge_base.xlsx'
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path, engine='openpyxl')
                required_cols = {"key", "problem", "keywords", "solutions", "category"}
                if not required_cols.issubset(set(c.lower() for c in df.columns)):
                    # Try case-insensitive mapping
                    colmap = {c.lower(): c for c in df.columns}
                else:
                    colmap = {c.lower(): c for c in df.columns}

                def parse_keywords(val):
                    if isinstance(val, str):
                        return [k.strip().lower() for k in re.split(r"[,;]", val) if k.strip()]
                    return []

                def parse_solutions(val):
                    if isinstance(val, str):
                        parts = re.split(r"[\n;]", val)
                        return [p.strip() for p in parts if p.strip()]
                    if isinstance(val, list):
                        return [str(v).strip() for v in val if str(v).strip()]
                    return []

                kb: Dict[str, Dict] = {}
                for _, row in df.iterrows():
                    key = str(row[colmap.get('key')]).strip()
                    if not key or key.lower() == 'nan':
                        continue
                    problem = str(row.get(colmap.get('problem'), '')).strip()
                    keywords = parse_keywords(row.get(colmap.get('keywords')))
                    solutions = parse_solutions(row.get(colmap.get('solutions')))
                    category = str(row.get(colmap.get('category'), 'General')).strip()
                    if not solutions:
                        continue
                    kb[key] = {
                        "problem": problem,
                        "keywords": keywords,
                        "solutions": solutions,
                        "category": category
                    }
                if kb:
                    return kb
            except Exception:
                # Fall back to defaults if Excel parse fails
                pass

        return {
            "login_issues": {
                "problem": "Cannot login to account",
                "keywords": ["login", "signin", "password", "account", "credentials", "authentication"],
                "solutions": [
                    "Reset your password using the 'Forgot Password' link",
                    "Check if your email address is correct",
                    "Clear your browser cache and cookies",
                    "Try logging in from an incognito/private window",
                    "Ensure your account is not locked or suspended",
                    "Contact support if the issue persists"
                ],
                "category": "Account Issues"
            },
            "phone_screen_issues": {
                "problem": "Phone screen problems (cracked, unresponsive, touch not working)",
                "keywords": ["phone", "mobile", "screen", "display", "touch", "digitizer", "glass", "crack", "unresponsive"],
                "solutions": [
                    "Restart the phone and try again",
                    "Remove any screen protector and test touch response",
                    "Check for software updates and install the latest version",
                    "Boot into safe mode to rule out third-party apps",
                    "Run touchscreen calibration (if supported)",
                    "If physically cracked, visit an authorized service center for replacement"
                ],
                "category": "Phone - Screen"
            },
            "phone_charging_issues": {
                "problem": "Phone not charging or charging slowly",
                "keywords": ["phone", "mobile", "charge", "charging", "charger", "cable", "battery", "port"],
                "solutions": [
                    "Try a different power adapter and USB cable",
                    "Clean the charging port gently with a soft brush",
                    "Check for debris or moisture in the port",
                    "Disable optimized charging/enable normal charging mode",
                    "Update to the latest OS version",
                    "If still not charging, contact service for port/battery diagnostics"
                ],
                "category": "Phone - Charging"
            },
            "phone_network_issues": {
                "problem": "Phone network or connectivity problems",
                "keywords": ["phone", "mobile", "network", "signal", "sim", "4g", "5g", "lte", "no service", "wifi", "bluetooth", "hotspot"],
                "solutions": [
                    "Toggle Airplane mode OFF/ON and re-check",
                    "Remove and reinsert the SIM card",
                    "Reset network settings from Settings > System > Reset",
                    "Forget and reconnect to Wi‑Fi; try a different network",
                    "Update carrier settings/OS to latest version",
                    "Contact your carrier if there is a local outage"
                ],
                "category": "Phone - Connectivity"
            },
            "phone_storage_issues": {
                "problem": "Phone storage full or running out of space",
                "keywords": ["phone", "mobile", "storage", "space", "memory full", "cleanup", "delete"],
                "solutions": [
                    "Delete unused apps and large media files",
                    "Clear app caches (Photos, social, browsers)",
                    "Enable automatic photo backup and remove local copies",
                    "Move files to cloud or SD card (if supported)",
                    "Review Downloads and Screen Recordings folders",
                    "Restart the phone after cleanup to reclaim space"
                ],
                "category": "Phone - Storage"
            },
            "phone_overheating": {
                "problem": "Phone overheating",
                "keywords": ["phone", "mobile", "hot", "overheat", "temperature", "warm"],
                "solutions": [
                    "Remove the case and let the device cool down",
                    "Close background apps and reduce screen brightness",
                    "Avoid gaming or heavy apps while charging",
                    "Update apps and OS to latest versions",
                    "Disable high-usage features temporarily (hotspot, GPS)",
                    "If overheating persists, contact service for diagnostics"
                ],
                "category": "Phone - Thermal"
            },
            "phone_camera_issues": {
                "problem": "Phone camera blurry or not working",
                "keywords": ["phone", "mobile", "camera", "photo", "video", "blurry", "focus", "flash"],
                "solutions": [
                    "Clean camera lens and remove any case blocking it",
                    "Tap to focus and hold steady; disable macro if too close",
                    "Clear Camera app cache and restart the app",
                    "Test in safe mode to exclude third-party camera apps",
                    "Update OS and Camera app",
                    "If hardware damage suspected, visit service center"
                ],
                "category": "Phone - Camera"
            },
            "phone_audio_issues": {
                "problem": "No sound or distorted audio",
                "keywords": ["phone", "mobile", "audio", "sound", "speaker", "volume", "mute"],
                "solutions": [
                    "Increase media/call volume and disable Do Not Disturb",
                    "Clean the speaker grills; remove debris or case obstructions",
                    "Toggle Bluetooth off to avoid routing audio to another device",
                    "Restart phone and test with different apps",
                    "Update OS and media apps",
                    "If still distorted/no output, seek hardware diagnostics"
                ],
                "category": "Phone - Audio"
            },
            "phone_mic_issues": {
                "problem": "Microphone not working during calls or recordings",
                "keywords": ["phone", "mobile", "microphone", "mic", "record", "call", "voice"],
                "solutions": [
                    "Remove case/screen protectors blocking the mic openings",
                    "Test mic in Voice Recorder and in calls",
                    "Disable noise suppression enhancements if available",
                    "Check app permissions for microphone access",
                    "Restart device and update OS",
                    "If no input detected, contact service"
                ],
                "category": "Phone - Microphone"
            },
            "phone_call_quality": {
                "problem": "Poor call quality or dropped calls",
                "keywords": ["phone", "mobile", "call", "quality", "dropped", "voice", "volte"],
                "solutions": [
                    "Toggle VoLTE/Wi‑Fi calling and retest",
                    "Move to an area with better signal or switch network band",
                    "Reset network settings",
                    "Update carrier settings/OS",
                    "Try a different SIM or contact carrier to check local outages"
                ],
                "category": "Phone - Calls"
            },
            "phone_sms_mms": {
                "problem": "SMS/MMS not sending or receiving",
                "keywords": ["phone", "mobile", "sms", "mms", "message", "text", "imessage"],
                "solutions": [
                    "Ensure mobile data is on for MMS and correct APN settings",
                    "Clear Messages app cache and restart phone",
                    "Turn iMessage/RCS off and on (where applicable)",
                    "Check recipient number format and block lists",
                    "Contact carrier to confirm messaging service status"
                ],
                "category": "Phone - Messaging"
            },
            "phone_gps_issues": {
                "problem": "GPS inaccurate or not locking location",
                "keywords": ["phone", "mobile", "gps", "location", "maps", "navigation"],
                "solutions": [
                    "Enable High Accuracy/Precise Location settings",
                    "Calibrate compass; avoid cases that interfere with sensors",
                    "Clear Maps app cache and offline data",
                    "Update OS and Google Play Services/Apple Maps components",
                    "Test outdoors with clear view of sky"
                ],
                "category": "Phone - GPS"
            },
            "phone_bluetooth_pairing": {
                "problem": "Bluetooth won’t pair or drops connection",
                "keywords": ["phone", "mobile", "bluetooth", "pair", "audio", "headphones", "car"],
                "solutions": [
                    "Forget device and re-pair; keep device in pairing mode",
                    "Toggle Bluetooth OFF/ON and restart the phone",
                    "Update firmware of the accessory if available",
                    "Keep devices within 1–2 meters and remove other BT pairings",
                    "Reset network settings if persistent"
                ],
                "category": "Phone - Bluetooth"
            },
            "phone_notifications": {
                "problem": "Notifications not arriving",
                "keywords": ["phone", "mobile", "notification", "alerts", "push", "dnd", "battery optimization"],
                "solutions": [
                    "Disable Do Not Disturb and Focus modes",
                    "Allow app notifications and set them to ‘Immediate’",
                    "Exclude the app from battery optimization/background limits",
                    "Check network connectivity and app-specific notification settings",
                    "Update the app and OS"
                ],
                "category": "Phone - Notifications"
            },
            "phone_hotspot_tether": {
                "problem": "Hotspot/tethering not working",
                "keywords": ["phone", "mobile", "hotspot", "tether", "share", "wifi", "usb"],
                "solutions": [
                    "Confirm hotspot plan/carrier support and enable hotspot",
                    "Change hotspot band (2.4 GHz/5 GHz) and password",
                    "Try USB tethering or Bluetooth tethering as a test",
                    "Turn off VPN and reset network settings"
                ],
                "category": "Phone - Hotspot"
            },
            "phone_update_fail": {
                "problem": "OS update download/install fails",
                "keywords": ["phone", "mobile", "update", "upgrade", "install", "download", "error"],
                "solutions": [
                    "Free up storage space (at least 5–10 GB recommended)",
                    "Charge to 50%+ and connect to reliable Wi‑Fi",
                    "Clear updater cache (Android) or use iTunes/Finder (iOS)",
                    "Retry after reboot; if persistent, factory reset after backup"
                ],
                "category": "Phone - Updates"
            },
            "phone_sdcard_storage": {
                "problem": "SD card not detected or read-only",
                "keywords": ["phone", "mobile", "sd", "micro sd", "storage", "card"],
                "solutions": [
                    "Re-seat the SD card and clean contacts",
                    "Test the card in a PC; back up and reformat to exFAT/FAT32",
                    "Use a branded high-speed card; avoid counterfeit cards",
                    "If slot still fails, seek hardware service"
                ],
                "category": "Phone - SD Card"
            },
            "phone_biometric": {
                "problem": "Face ID/Touch ID not working",
                "keywords": ["phone", "mobile", "face id", "touch id", "fingerprint", "biometric"],
                "solutions": [
                    "Clean sensors and ensure nothing blocks the camera/home button",
                    "Re-register fingerprints/face in a well-lit environment",
                    "Remove screen protectors that interfere",
                    "Update OS and disable glove mode if enabled",
                    "If sensor errors persist, contact service"
                ],
                "category": "Phone - Biometric"
            },
            "phone_water_damage": {
                "problem": "Suspected water damage",
                "keywords": ["phone", "mobile", "water", "liquid", "moisture", "wet"],
                "solutions": [
                    "Power off immediately and do not charge",
                    "Dry externally; avoid heat sources, do not shake",
                    "Leave in a dry, ventilated place for 24–48 hours",
                    "Seek professional inspection—liquid damage may not be covered"
                ],
                "category": "Phone - Liquid Damage"
            },
            "battery_issues": {
                "problem": "iPhone battery drains quickly",
                "keywords": ["phone", "mobile", "battery", "charge", "power", "drain", "charging", "life"],
                "solutions": [
                    "Reduce screen brightness",
                    "Turn off Background App Refresh",
                    "Enable Low Power Mode",
                    "Check Battery Health in Settings",
                    "Update iOS to the latest version",
                    "If issue persists, consider battery replacement"
                ],
                "category": "Battery Issues"
            },
            "payment_issues": {
                "problem": "Payment processing problems",
                "keywords": ["payment", "billing", "charge", "refund", "transaction", "card", "money"],
                "solutions": [
                    "Check your payment method details",
                    "Verify billing address matches your card",
                    "Try a different payment method",
                    "Contact your bank if card is declined",
                    "Clear browser cache and try again",
                    "Check if your account has sufficient funds"
                ],
                "category": "Payment Issues"
            },
            "performance_issues": {
                "problem": "App running slowly",
                "keywords": ["phone", "mobile", "slow", "performance", "timeout", "lag", "speed", "loading"],
                "solutions": [
                    "Close unnecessary apps running in background",
                    "Restart the application",
                    "Check your internet connection",
                    "Update to the latest version",
                    "Clear app cache if possible",
                    "Restart your device"
                ],
                "category": "Performance Issues"
            },
            "api_integration": {
                "problem": "API integration help needed",
                "keywords": ["api", "integrate", "help", "support", "technical", "documentation"],
                "solutions": [
                    "Check our API documentation",
                    "Verify your API key is correct",
                    "Ensure you're using the correct endpoints",
                    "Check rate limits and quotas",
                    "Review error messages for specific issues",
                    "Contact our technical support team"
                ],
                "category": "Technical Support"
            },
            "bug_reports": {
                "problem": "Application bugs or errors",
                "keywords": ["bug", "error", "broken", "crash", "issue", "not working"],
                "solutions": [
                    "Try refreshing the page or restarting the app",
                    "Clear browser cache and cookies",
                    "Update to the latest version",
                    "Check if the issue occurs on different devices",
                    "Report the bug with detailed steps to reproduce",
                    "Contact support with error messages"
                ],
                "category": "Bug Reports"
            },
            "security_concerns": {
                "problem": "Security issues or concerns",
                "keywords": ["security", "hack", "breach", "suspicious", "unauthorized", "threat"],
                "solutions": [
                    "Change your password immediately",
                    "Enable two-factor authentication",
                    "Check your account for unauthorized activity",
                    "Contact our security team immediately",
                    "Review your account settings",
                    "Report any suspicious activity"
                ],
                "category": "Security Issues"
            }
        }
    
    def resolve_query(self, query: str) -> Dict:
        """
        Resolve a customer query using RAG or keyword-based search.
        
        Args:
            query: The customer query
            
        Returns:
            Dictionary containing solutions, confidence, and category
        """
        if self.use_rag and self.rag_engine:
            return self._resolve_with_rag(query)
        else:
            return self._resolve_with_keywords(query)
    
    def _resolve_with_rag(self, query: str) -> Dict:
        """Resolve query using FAISS RAG engine."""
        try:
            # Search using RAG
            results = self.rag_engine.search(query, top_k=3, score_threshold=0.3)
            
            if results:
                # Get the best match
                best_result = results[0]
                metadata = best_result['metadata']
                
                return {
                    "solutions": metadata.get('solutions', []),
                    "confidence": best_result['score'],
                    "category": metadata.get('category', 'General'),
                    "solved": True,
                    "matched_keywords": metadata.get('keywords', []),
                    "kb_key": metadata.get('key'),
                    "search_method": "RAG",
                    "similar_results": len(results)
                }
            else:
                # No good match found with RAG
                return self._get_fallback_response()
                
        except Exception as e:
            print(f"⚠️ RAG search failed: {e}")
            return self._resolve_with_keywords(query)
    
    def _resolve_with_keywords(self, query: str) -> Dict:
        """Resolve query using keyword-based search (fallback)."""
        query_lower = query.lower()
        
        # Find best matching knowledge base entry
        best_match = None
        best_key: str | None = None
        best_score = 0
        matched_keywords = []
        
        phone_boost_keywords = {"phone", "mobile", "android", "iphone", "ios", "smartphone", "device"}

        for key, data in self.knowledge_base.items():
            score = 0
            keywords = data["keywords"]
            
            # Calculate similarity score
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
                    matched_keywords.append(keyword)
            # Extra weight if the query mentions phone/device context
            if any(k in query_lower for k in phone_boost_keywords):
                score += 1.5
            
            # Normalize score
            normalized_score = score / len(keywords) if keywords else 0
            
            if normalized_score > best_score:
                best_score = normalized_score
                best_match = data
                best_key = key
        
        # Slightly lower threshold to return solutions more often for phone support
        if best_match and best_score > 0.2:
            return {
                "solutions": best_match["solutions"],
                "confidence": best_score,
                "category": best_match["category"],
                "solved": True,
                "matched_keywords": matched_keywords,
                "kb_key": best_key,
                "search_method": "Keywords"
            }
        else:
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict:
        """Get fallback response when no good match is found."""
        generic_phone_tips = [
            "Restart the phone and ensure it's updated to the latest OS.",
            "Clear cache or reinstall the problematic app if applicable.",
            "Check storage, battery health, and network settings.",
            "If the issue persists, back up your data and contact service support."
        ]
        return {
            "solutions": generic_phone_tips,
            "confidence": 0.4,
            "category": "Phone - General",
            "solved": False,
            "matched_keywords": [],
            "search_method": "Fallback"
        }
    
    def get_similar_queries(self, query: str) -> List[Dict]:
        """
        Get similar queries from the knowledge base.
        
        Args:
            query: The customer query
            
        Returns:
            List of similar queries with solutions
        """
        query_lower = query.lower()
        similar_queries = []
        
        for key, data in self.knowledge_base.items():
            score = 0
            matched_keywords = []
            
            for keyword in data["keywords"]:
                if keyword in query_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                normalized_score = score / len(data["keywords"])
                similar_queries.append({
                    "problem": data["problem"],
                    "solutions": data["solutions"],
                    "score": normalized_score,
                    "matched_keywords": matched_keywords,
                    "category": data["category"]
                })
        
        # Sort by score descending
        similar_queries.sort(key=lambda x: x["score"], reverse=True)
        return similar_queries[:3]  # Return top 3 similar queries
