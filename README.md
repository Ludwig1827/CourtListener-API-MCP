# CourtListener Legal Research API MCP Server

A Model Context Protocol (MCP) server that provides comprehensive access to the CourtListener.com legal database API v4. This tool enables AI assistants to search, analyze, and retrieve legal cases, court opinions, dockets, and judicial information.

## 🏛️ Features

- **Case Search**: Full-text search across millions of court opinions
- **Citation Lookup**: Find cases by legal citation (e.g., "410 U.S. 113")
- **Docket Search**: Access court dockets and case filings
- **Opinion Analysis**: Retrieve full case text and detailed analysis
- **Court Information**: Search federal and state court databases
- **Judge Lookup**: Find information about judges and court personnel
- **Case Comparison**: Side-by-side analysis of legal cases
- **Citation Analysis**: Extract and analyze case citations
- **Impact Assessment**: Evaluate legal and societal impact of cases
- **Pagination Support**: Handle large result sets with cursor-based pagination

## 📋 Requirements

- Python 3.8+
- CourtListener.com API token (free registration required)
- Required Python packages:
  - `mcp`
  - `requests`
  - `python-dotenv`
  - `openai` (for client integration)

## 🚀 Quick Start

### 1. Get Your API Token

1. Visit [CourtListener.com/api](https://www.courtlistener.com/api/)
2. Create a free account
3. Generate an API token
4. Note: Free accounts get 5,000 queries per hour

### 2. Install Dependencies

```bash
pip install mcp requests python-dotenv openai
```

### 3. Set Up Environment

Create a `.env` file in your project directory:

```env
COURTLISTENER_API_TOKEN=your_token_here
OPENAI_API_KEY=your_openai_key_here
```

### 4. Test Your Setup

```bash
python test.py
```

This will verify your API token and connection.

### 5. Run the Server

```bash
# Start MCP server
mcp run server.py

# Or run the client example
python client.py
```

## 🔧 Available Tools

### Core Search Tools

#### `search_cases`
Search court opinions with advanced filtering options.

```python
# Example usage in prompts:
# "Find Supreme Court cases about constitutional law from 2020-2023"
# "Search for cases mentioning 'F-1 visa' and 'business'"
```

**Parameters:**
- `query`: Full-text search with AND, OR, NOT operators
- `case_name`: Specific case name search
- `court`: Court identifier (scotus, ca1-ca11, etc.)
- `date_filed_after/before`: Date range filtering (YYYY-MM-DD)
- `cited_gt`: Minimum citation count
- `judge`: Judge name filter
- `limit`: Max results (default 20)

#### `lookup_citation`
Find cases by legal citation.

```python
# Example: lookup_citation("576 U.S. 644")
# Returns: Detailed case information for the citation
```

#### `search_dockets`
Search court dockets and case filings.

**Parameters:**
- `case_name`: Case name search
- `docket_number`: Specific docket number
- `court`: Court identifier
- `nature_of_suit`: Case type filtering
- Date range filters

### Analysis Tools

#### `get_case_summary`
Get comprehensive case analysis with full text.

**Parameters:**
- `case_identifier`: Opinion ID, URL, or case name
- `summary_type`: Type of analysis (overview, legal_analysis, key_holdings)
- `max_text_length`: Text length limit for analysis

#### `compare_cases`
Side-by-side comparison of two legal cases.

```python
# Example: compare_cases("Roe v. Wade", "Dobbs v. Jackson", "holdings")
```

#### `extract_case_citations`
Analyze citations within a case opinion.

#### `analyze_case_impact`
Evaluate the broader legal and societal impact of a case.

### Utility Tools

#### `search_courts`
Find information about federal and state courts.

#### `search_people`
Search for judges and court personnel.

#### `search_with_pagination`
Handle large result sets across multiple pages.

## 🏛️ Court Identifiers

### Federal Courts
- `scotus` - Supreme Court of the United States
- `ca1` through `ca11` - Circuit Courts of Appeals (1st-11th Circuit)
- `cadc` - D.C. Circuit Court of Appeals
- `cafc` - Federal Circuit Court of Appeals
- `fd` - Federal District Courts
- `fb` - Federal Bankruptcy Courts

### State Courts
State court identifiers follow patterns like:
- `cal` - California Supreme Court
- `ny` - New York Court of Appeals
- `tex` - Texas Supreme Court

## 📊 Rate Limits

- **Authenticated API**: 5,000 queries per hour
- **Citation Lookup**: 60 citations per minute
- **Maintenance Window**: Thursdays 21:00-23:59 PT

## 💻 Usage Examples

### Basic Case Search
```python
# Find recent business visa cases
search_cases(
    query="F-1 visa business startup",
    date_filed_after="2020-01-01",
    limit="10"
)
```

### Citation Lookup
```python
# Look up a famous case
lookup_citation("410 U.S. 113")  # Roe v. Wade
```

### Comprehensive Case Analysis
```python
# Get detailed analysis of a case
get_case_summary(
    case_identifier="Bush v. Gore",
    summary_type="legal_analysis",
    max_text_length="15000"
)
```

### Compare Legal Cases
```python
# Compare two related cases
compare_cases(
    case1_identifier="Citizens United v. FEC",
    case2_identifier="Austin v. Michigan Chamber of Commerce",
    comparison_focus="holdings"
)
```

## 🔍 Search Query Syntax

CourtListener supports advanced search syntax:

- **Phrase Search**: `"exact phrase"`
- **Boolean**: `constitutional AND law`
- **Exclusion**: `privacy NOT criminal`
- **Field Search**: `caseName:"Bush v. Gore"`
- **Wildcards**: `immigra*` (matches immigration, immigrant, etc.)

## 🛠️ Integration with AI Assistants

This MCP server is designed to work with AI assistants for legal research. Example prompts:

- *"Find cases about F-1 visa students starting businesses"*
- *"Compare the holdings in Citizens United and Austin v. Michigan"*
- *"Analyze the impact of Dobbs v. Jackson on reproductive rights"*
- *"What Supreme Court cases cite Brown v. Board of Education?"*

## 📁 Project Structure

```
├── server.py          # MCP server implementation
├── client.py          # Example client usage
├── test.py           # API connectivity test
├── .env              # Environment variables
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## 🚨 Error Handling

The server includes comprehensive error handling for:

- **Rate Limiting**: Automatic retry with exponential backoff
- **Authentication**: Clear error messages for token issues
- **Network Issues**: Timeout handling and retries
- **Invalid Queries**: Helpful error messages and suggestions

## 🔐 Security Notes

- Store API tokens in environment variables only
- Never commit tokens to version control
- Use `.gitignore` to exclude `.env` files
- Consider using more restrictive API permissions for production

## 📚 Additional Resources

- [CourtListener API Documentation](https://www.courtlistener.com/api/rest-info/)
- [Legal Citation Guide](https://www.law.cornell.edu/citation/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [CourtListener Help Center](https://www.courtlistener.com/help/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is provided as-is for educational and research purposes. Please respect CourtListener's terms of service and API usage guidelines.

## ⚠️ Disclaimers

- This tool is for research purposes only
- Legal information should be verified through official sources
- Not a substitute for professional legal advice
- CourtListener data may have limitations or delays

## 🆘 Troubleshooting

### Common Issues

**"Authentication failed"**
- Check your API token in `.env`
- Verify token is active on CourtListener.com
- Ensure no extra spaces in token

**"Rate limit exceeded"**
- Wait before making more requests
- Consider upgrading to paid plan for higher limits
- Implement request throttling in your application

**"No results found"**
- Try broader search terms
- Check court identifiers and date formats
- Verify case names and citations

### Getting Help

1. Run `python test.py` to diagnose issues
2. Check CourtListener status page
3. Review API documentation
4. Contact CourtListener support for API issues

---

Built with ❤️ for legal research and AI-assisted analysis.
