# 🤖 AI Customer Support System

A complete, professional customer support solution that answers queries, creates tickets, and integrates seamlessly with Google Sheets.

## 🚀 Quick Start

### Windows (Super Easy)
```bash
launch_app.bat
```

### Manual Launch
```bash
pip install -r requirements.txt
streamlit run main.py --server.port 8501
```

## 🌟 Features

### 💬 Query Resolution
- **AI-Powered Answers**: Intelligent responses using knowledge base
- **Automatic Ticket Creation**: Creates tickets for unresolved queries
- **Real-time Processing**: Instant query analysis and response
- **Smart Categorization**: Automatically categorizes issues

### 🎫 Ticket Management
- **Complete Ticket Lifecycle**: Create, track, and resolve tickets
- **Status Management**: Open, In Progress, Closed statuses
- **Priority Assignment**: High, Medium, Low, Critical priority levels
- **Customer Information**: Track customer details and contact info

### 📊 Google Sheets Integration
- **Import Data**: Load existing tickets from Google Sheets
- **Export Results**: Save all tickets back to Google Sheets
- **Real-time Sync**: Keep data synchronized
- **Sample Dataset**: Built-in sample data for testing

### 📈 Analytics & Reporting
- **Performance Metrics**: Resolution rates, ticket counts
- **Visual Charts**: Category and priority distributions
- **Trend Analysis**: Daily ticket creation trends
- **Real-time Stats**: Live dashboard updates

## 📁 Project Structure

```
Milestone/
├── main.py                 # 🤖 Main Streamlit application
├── categorizer.py          # 🏷️ Ticket categorization logic
├── resolver.py             # 💬 Query resolution system
├── tagger.py               # 🏷️ Intelligent tagging system
├── sheets_client.py        # 📊 Google Sheets integration
├── dataset_generator.py    # 📊 Sample dataset generator
├── requirements.txt        # 📦 Python dependencies
├── launch_app.bat         # 🚀 Windows launcher
├── sample_tickets.csv     # 📊 Sample dataset (generated)
└── README.md              # 📚 Documentation
```

## 🎯 How to Use

### 1. Launch the Application
```bash
launch_app.bat
```
The app opens at: http://localhost:8501

### 2. Answer Customer Queries
1. Go to "Query Resolution" tab
2. Enter customer information
3. Describe the issue
4. Click "Get AI Response"
5. System provides solution or creates ticket

### 3. Manage Tickets
1. Go to "Ticket Management" tab
2. View all created tickets
3. Filter by status, priority, or category
4. Update ticket status
5. Mark tickets as solved

### 4. Google Sheets Integration
1. Go to "Google Sheets" tab
2. Upload credentials JSON file
3. Enter your Google Sheet ID
4. Import/export data as needed

## 📊 Sample Dataset

The system includes a comprehensive sample dataset with 10 tickets covering:
- Account Issues (login problems, account locked)
- Payment Issues (payment processing, billing)
- Battery Issues (iPhone battery problems)
- Technical Support (API integration, data export)
- Bug Reports (app crashes, performance issues)
- Feature Requests (dark mode, new features)
- Performance Issues (slow loading, timeouts)
- Security Issues (suspicious emails, breaches)

## 🔧 Google Sheets Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Sheets API
4. Create OAuth 2.0 credentials
5. Download JSON file
6. Upload in the app settings

## 📱 Interface Overview

### Query Resolution Tab
- Customer information form
- Issue description area
- AI response display
- Quick stats sidebar

### Ticket Management Tab
- Ticket list with filters
- Detailed ticket view
- Status update buttons
- Search and filter options

### Google Sheets Tab
- Import/export functionality
- Data preview
- Sync status
- Sample data creation

### Analytics Tab
- Performance metrics
- Visual charts
- Trend analysis
- Export options

## 🎨 Professional Features

✅ **AI-Powered Query Resolution** - Intelligent responses using knowledge base  
✅ **Automatic Ticket Creation** - Creates tickets for unresolved queries  
✅ **Google Sheets Integration** - Full import/export functionality  
✅ **Professional Interface** - Modern, dark-themed UI  
✅ **Real-time Processing** - Instant query analysis  
✅ **Complete Workflow** - From query to resolution  
✅ **Sample Dataset** - Ready-to-use test data  
✅ **Modular Architecture** - Clean, maintainable code  

## 🚀 Ready to Use!

Your AI Customer Support System is complete and ready to:
- Answer customer queries intelligently
- Create and manage support tickets
- Integrate with Google Sheets
- Provide analytics and reporting
- Handle real customer support workflows

**Just run `launch_app.bat` and start helping customers!** 🎉