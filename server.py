from mcp.server.fastmcp import FastMCP
import requests
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import time

# Initialize the MCP server
mcp = FastMCP("CourtListener Legal Research API v4")

# Base configuration for CourtListener API v4
COURTLISTENER_BASE_URL = "https://www.courtlistener.com/api/rest/v4"

def get_api_token():
    """Get CourtListener API token from environment variable."""
    token = os.environ.get('COURTLISTENER_API_TOKEN')
    if not token:
        return None
    return token

def make_api_request(endpoint: str, params: Dict[str, Any] = None, retries: int = 3) -> Dict[str, Any]:
    """Make a request to the CourtListener API v4 with proper authentication and retry logic."""
    token = get_api_token()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    if token:
        headers['Authorization'] = f'Token {token}'
    
    url = f"{COURTLISTENER_BASE_URL}/{endpoint}/"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            
            # Handle rate limiting
            if response.status_code == 429:
                return {"error": "Rate limit exceeded. Free accounts have 5,000 queries/hour. Please wait before making more requests."}
            
            # Handle authentication errors
            if response.status_code == 401:
                return {"error": "Authentication failed. Check your COURTLISTENER_API_TOKEN environment variable."}
            
            # Handle not found / invalid cursor
            if response.status_code == 404:
                return {"error": "Not found or invalid cursor. Try removing pagination parameters."}
            
            response.raise_for_status()
            return response.json()
            
        except requests.Timeout:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            return {"error": f"Request timed out after {retries} attempts. CourtListener API may be slow or unavailable."}
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"error": f"API request failed after {retries} attempts: {str(e)}"}
    
    return {"error": "Maximum retries exceeded"}

@mcp.tool()
def search_cases(
    query: str = "",
    case_name: str = "",
    court: str = "",
    date_filed_after: str = "",
    date_filed_before: str = "",
    cited_gt: str = "",
    judge: str = "",
    highlight: str = "on",
    limit: str = "20"
) -> str:
    """
    Search cases using the unified search API (v4).
    
    Args:
        query: Full-text search query (supports AND, OR, NOT, quotes for phrases)
        case_name: Case name search
        court: Court identifier (scotus, ca1-ca11, cadc, cafc, etc.)
        date_filed_after: Date in YYYY-MM-DD format
        date_filed_before: Date in YYYY-MM-DD format  
        cited_gt: Minimum citation count
        judge: Judge name
        highlight: Enable highlighting (on/off)
        limit: Max results to return (API returns 20 per page)
    """
    params = {
        'type': 'o',  # Search opinions
        'format': 'json'
    }
    
    # Build query string
    query_parts = []
    if query:
        query_parts.append(query)
    if case_name:
        query_parts.append(f'caseName:"{case_name}"')
    
    if query_parts:
        params['q'] = ' AND '.join(query_parts)
    
    # Add filters using v4 camelCase format for search API
    if court:
        params['court'] = court
    if date_filed_after:
        params['filed_after'] = date_filed_after
    if date_filed_before:
        params['filed_before'] = date_filed_before
    if cited_gt:
        params['cited_gt'] = cited_gt
    if judge:
        params['judge'] = judge
    if highlight:
        params['highlight'] = highlight
    
    result = make_api_request("search", params)
    
    if "error" in result:
        return result["error"]
    
    if 'results' not in result:
        return "No results found"
    
    # Calculate how many to show
    try:
        max_results = min(int(limit), len(result['results']))
    except ValueError:
        max_results = len(result['results'])
    
    output = f"Found {result.get('count', 0)} cases (showing {max_results}):\n\n"
    
    for i, case in enumerate(result['results'][:max_results], 1):
        output += f"{i}. {case.get('caseName', 'Unknown Case')}\n"
        output += f"   Court: {case.get('court', 'Unknown Court')}\n"
        output += f"   Date: {case.get('dateFiled', 'Unknown Date')}\n"
        output += f"   Docket: {case.get('docketNumber', 'N/A')}\n"
        output += f"   Citations: {case.get('citeCount', 0)}\n"
        
        if case.get('status'):
            output += f"   Status: {case['status']}\n"
        
        if case.get('absolute_url'):
            output += f"   URL: https://www.courtlistener.com{case['absolute_url']}\n"
        
        # Show snippet if highlighting is enabled
        if case.get('snippet'):
            snippet = case['snippet'].replace('<mark>', '**').replace('</mark>', '**')
            output += f"   Snippet: {snippet}\n"
        
        output += "\n"
    
    # Add pagination info
    if result.get('next'):
        output += "More results available. Use cursor pagination for additional pages.\n"
    
    return output

@mcp.tool()
def get_opinion_by_id(opinion_id: str, include_text: str = "no") -> str:
    """
    Get detailed information about a specific opinion by ID.
    
    Args:
        opinion_id: The opinion ID
        include_text: Whether to include opinion text (yes/no) - text can be very long
    """
    # Use field selection for performance
    if include_text.lower() == "yes":
        fields = "id,cluster,author_str,type,download_url,absolute_url,plain_text"
    else:
        fields = "id,cluster,author_str,type,download_url,absolute_url"
    
    params = {'fields': fields}
    result = make_api_request(f"opinions/{opinion_id}", params)
    
    if "error" in result:
        return result["error"]
    
    # Format detailed opinion info
    cluster = result.get('cluster', {})
    
    output = f"OPINION DETAILS (ID: {opinion_id})\n"
    output += f"Case: {cluster.get('case_name', 'Unknown')}\n"
    output += f"Date Filed: {cluster.get('date_filed', 'Unknown')}\n"
    output += f"Author: {result.get('author_str', 'Unknown')}\n"
    output += f"Type: {result.get('type', 'Unknown')}\n"
    output += f"Citations: {cluster.get('citation_count', 0)}\n"
    output += f"Precedential Status: {cluster.get('precedential_status', 'Unknown')}\n"
    
    if result.get('download_url'):
        output += f"PDF Download: {result['download_url']}\n"
    
    # Add text content if requested and available
    if include_text.lower() == "yes" and result.get('plain_text'):
        text = result['plain_text'][:2000]  # Limit to first 2000 chars
        output += f"\nOpinion Text (first 2000 chars):\n{text}...\n"
    
    output += f"Full URL: https://www.courtlistener.com{result.get('absolute_url', '')}\n"
    
    return output

@mcp.tool()
def search_dockets(
    case_name: str = "",
    docket_number: str = "",
    court: str = "",
    date_filed_after: str = "",
    date_filed_before: str = "",
    nature_of_suit: str = "",
    limit: str = "20"
) -> str:
    """
    Search court dockets using the dockets API.
    
    Args:
        case_name: Case name search
        docket_number: Docket number
        court: Court identifier
        date_filed_after: Date in YYYY-MM-DD format
        date_filed_before: Date in YYYY-MM-DD format
        nature_of_suit: Nature of suit description
        limit: Max results to show
    """
    params = {
        'fields': 'id,case_name,docket_number,court,date_filed,nature_of_suit,absolute_url'
    }
    
    # Add filters using snake_case for direct API endpoints
    if case_name:
        params['case_name__icontains'] = case_name
    if docket_number:
        params['docket_number__icontains'] = docket_number
    if court:
        params['court'] = court
    if date_filed_after:
        params['date_filed__gte'] = date_filed_after
    if date_filed_before:
        params['date_filed__lte'] = date_filed_before
    if nature_of_suit:
        params['nature_of_suit__icontains'] = nature_of_suit
    
    result = make_api_request("dockets", params)
    
    if "error" in result:
        return result["error"]
    
    if 'results' not in result:
        return "No dockets found"
    
    try:
        max_results = min(int(limit), len(result['results']))
    except ValueError:
        max_results = len(result['results'])
    
    output = f"Found {result.get('count', 0)} dockets (showing {max_results}):\n\n"
    
    for i, docket in enumerate(result['results'][:max_results], 1):
        court_info = docket.get('court', {})
        
        output += f"{i}. {docket.get('case_name', 'Unknown Case')}\n"
        output += f"   Docket: {docket.get('docket_number', 'N/A')}\n"
        output += f"   Court: {court_info.get('full_name', 'Unknown') if isinstance(court_info, dict) else court_info}\n"
        output += f"   Date Filed: {docket.get('date_filed', 'Unknown')}\n"
        output += f"   Nature of Suit: {docket.get('nature_of_suit', 'N/A')}\n"
        output += f"   URL: https://www.courtlistener.com{docket.get('absolute_url', '')}\n\n"
    
    return output

@mcp.tool()
def lookup_citation(citation: str) -> str:
    """
    Look up case information by citation using the Citation Lookup API.
    Limited to 60 valid citations per minute.
    
    Args:
        citation: Legal citation (e.g., "410 U.S. 113", "576 U.S. 644")
    """
    # Use the dedicated citation lookup endpoint
    url = f"https://www.courtlistener.com/api/rest/v3/citations/{citation}/"
    
    token = get_api_token()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    if token:
        headers['Authorization'] = f'Token {token}'
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 429:
            return "Rate limit exceeded for citation lookup (60 citations/minute). Please wait before trying again."
        
        if response.status_code == 404:
            return f"Citation '{citation}' not found in the database."
        
        response.raise_for_status()
        result = response.json()
        
    except requests.RequestException as e:
        return f"Citation lookup failed: {str(e)}"
    
    if result.get('status') == 404:
        return f"Citation '{citation}' not found: {result.get('error_message', 'Unknown error')}"
    
    clusters = result.get('clusters', [])
    if not clusters:
        return f"No cases found for citation: {citation}"
    
    output = f"CITATION LOOKUP: {citation}\n\n"
    
    for i, cluster in enumerate(clusters, 1):
        docket = cluster.get('docket', {})
        court = docket.get('court', {})
        
        output += f"Match {i}:\n"
        output += f"  Case: {cluster.get('case_name', 'Unknown')}\n"
        output += f"  Court: {court.get('full_name', 'Unknown')}\n"
        output += f"  Date: {cluster.get('date_filed', 'Unknown')}\n"
        output += f"  Citations: {cluster.get('citation_count', 0)}\n"
        output += f"  Docket: {docket.get('docket_number', 'N/A')}\n"
        
        # Show all citations for this case
        if cluster.get('citations'):
            cites = [cite.get('cite', 'N/A') for cite in cluster['citations']]
            output += f"  All Citations: {', '.join(cites)}\n"
        
        if cluster.get('absolute_url'):
            output += f"  URL: https://www.courtlistener.com{cluster['absolute_url']}\n"
        
        output += "\n"
    
    return output

@mcp.tool()
def search_courts(name: str = "", jurisdiction: str = "") -> str:
    """
    Search for court information.
    
    Args:
        name: Court name search (partial matches allowed)
        jurisdiction: Jurisdiction filter (F=Federal, S=State, FB=Federal Bankruptcy, etc.)
    """
    params = {
        'fields': 'id,full_name,short_name,jurisdiction,start_date,end_date,absolute_url'
    }
    
    if name:
        params['full_name__icontains'] = name
    if jurisdiction:
        params['jurisdiction'] = jurisdiction
    
    result = make_api_request("courts", params)
    
    if "error" in result:
        return result["error"]
    
    if 'results' not in result:
        return "No courts found"
    
    output = f"Found {len(result['results'])} courts:\n\n"
    
    for i, court in enumerate(result['results'], 1):
        output += f"{i}. {court.get('full_name', 'Unknown Court')}\n"
        output += f"   Short Name: {court.get('short_name', 'N/A')}\n"
        output += f"   ID: {court.get('id', 'N/A')}\n"
        output += f"   Jurisdiction: {court.get('jurisdiction', 'N/A')}\n"
        
        if court.get('start_date'):
            output += f"   Start Date: {court['start_date']}\n"
        if court.get('end_date'):
            output += f"   End Date: {court['end_date']}\n"
        
        output += f"   URL: https://www.courtlistener.com{court.get('absolute_url', '')}\n\n"
    
    return output

@mcp.tool()
def search_people(
    name: str = "",
    court: str = "",
    position_type: str = "",
    limit: str = "20"
) -> str:
    """
    Search for judges and other court personnel.
    
    Args:
        name: Person's name (partial matches)
        court: Court identifier where they served
        position_type: Position type filter
        limit: Max results to show
    """
    params = {
        'fields': 'id,name_full,positions,absolute_url'
    }
    
    if name:
        params['name_full__icontains'] = name
    if court:
        params['positions__court'] = court
    if position_type:
        params['positions__position_type'] = position_type
    
    result = make_api_request("people", params)
    
    if "error" in result:
        return result["error"]
    
    if 'results' not in result:
        return "No people found"
    
    try:
        max_results = min(int(limit), len(result['results']))
    except ValueError:
        max_results = len(result['results'])
    
    output = f"Found {result.get('count', 0)} people (showing {max_results}):\n\n"
    
    for i, person in enumerate(result['results'][:max_results], 1):
        output += f"{i}. {person.get('name_full', 'Unknown Person')}\n"
        
        positions = person.get('positions', [])
        if positions:
            output += f"   Positions:\n"
            for pos in positions[:3]:  # Show first 3 positions
                court_info = pos.get('court', {})
                court_name = court_info.get('full_name', 'Unknown Court') if isinstance(court_info, dict) else str(court_info)
                output += f"     - {court_name}"
                if pos.get('date_start'):
                    output += f" ({pos['date_start']}"
                    if pos.get('date_termination'):
                        output += f" - {pos['date_termination']}"
                    output += ")"
                output += "\n"
        
        output += f"   URL: https://www.courtlistener.com{person.get('absolute_url', '')}\n\n"
    
    return output

@mcp.tool()
def search_with_pagination(
    search_type: str,
    query: str = "",
    cursor: str = "",
    max_pages: str = "3"
) -> str:
    """
    Perform paginated search across multiple pages using cursor-based pagination.
    
    Args:
        search_type: Type of search (opinions, dockets, courts, people)
        query: Search query
        cursor: Pagination cursor (leave empty for first page)
        max_pages: Maximum pages to fetch (default 3, max 10)
    """
    if search_type not in ['opinions', 'dockets', 'courts', 'people']:
        return "Error: search_type must be one of: opinions, dockets, courts, people"
    
    try:
        max_pages_int = min(int(max_pages), 10)
    except ValueError:
        max_pages_int = 3
    
    params = {}
    if query:
        if search_type == 'opinions':
            params['q'] = query
        else:
            # For other endpoints, search in name fields
            if search_type == 'dockets':
                params['case_name__icontains'] = query
            elif search_type == 'courts':
                params['full_name__icontains'] = query
            elif search_type == 'people':
                params['name_full__icontains'] = query
    
    if cursor:
        params['cursor'] = cursor
    
    all_results = []
    current_cursor = cursor
    pages_fetched = 0
    
    while pages_fetched < max_pages_int:
        if current_cursor:
            params['cursor'] = current_cursor
        elif 'cursor' in params:
            del params['cursor']
        
        result = make_api_request(search_type, params)
        
        if "error" in result:
            return result["error"]
        
        if 'results' not in result or not result['results']:
            break
        
        all_results.extend(result['results'])
        pages_fetched += 1
        
        # Get next cursor
        next_url = result.get('next')
        if not next_url:
            break
        
        # Extract cursor from next URL
        if 'cursor=' in next_url:
            current_cursor = next_url.split('cursor=')[1].split('&')[0]
        else:
            break
    
    if not all_results:
        return f"No {search_type} found"
    
    output = f"Found {len(all_results)} {search_type} across {pages_fetched} pages:\n\n"
    
    for i, item in enumerate(all_results, 1):
        if search_type == 'opinions':
            cluster = item.get('cluster', {})
            output += f"{i}. {cluster.get('case_name', 'Unknown Case')}\n"
        elif search_type == 'dockets':
            output += f"{i}. {item.get('case_name', 'Unknown Case')}\n"
        elif search_type == 'courts':
            output += f"{i}. {item.get('full_name', 'Unknown Court')}\n"
        elif search_type == 'people':
            output += f"{i}. {item.get('name_full', 'Unknown Person')}\n"
        
        if item.get('absolute_url'):
            output += f"   URL: https://www.courtlistener.com{item['absolute_url']}\n"
        output += "\n"
    
    return output

@mcp.tool()
def get_case_summary(
    case_identifier: str,
    summary_type: str = "overview",
    max_text_length: str = "10000"
) -> str:
    """
    Get full case text and provide a structured summary.
    
    Args:
        case_identifier: Opinion ID, URL, or case name (e.g., "118395", "Bush v. Gore")
        summary_type: Type of summary (overview, legal_analysis, key_holdings, timeline)
        max_text_length: Maximum characters of case text to analyze (default 10000)
    """
    
    # Determine opinion ID from input
    opinion_id = None
    
    if case_identifier.isdigit():
        # Direct opinion ID
        opinion_id = case_identifier
    elif "opinion/" in case_identifier:
        # Extract ID from URL
        try:
            opinion_id = case_identifier.split("/opinion/")[1].split("/")[0]
        except IndexError:
            return f"Error: Could not extract opinion ID from URL: {case_identifier}"
    else:
        # Search for the case by name
        search_result = make_api_request("search", {
            'type': 'o', 
            'q': f'"{case_identifier}"',
            'fields': 'id,absolute_url'
        })
        
        if "error" in search_result:
            return f"Error searching for case: {search_result['error']}"
        
        results = search_result.get('results', [])
        if not results:
            return f"No cases found for: {case_identifier}"
        
        # Get opinion ID from first result
        first_result = results[0]
        absolute_url = first_result.get('absolute_url', '')
        if '/opinion/' in absolute_url:
            try:
                opinion_id = absolute_url.split('/opinion/')[1].split('/')[0]
            except IndexError:
                return f"Error: Could not extract opinion ID from search result"
        else:
            return f"Error: No opinion URL found in search results"
    
    if not opinion_id:
        return f"Error: Could not determine opinion ID from '{case_identifier}'"
    
    # Get full opinion details
    result = make_api_request(f"opinions/{opinion_id}", {
        'fields': 'id,cluster,author_str,type,download_url,absolute_url,plain_text,html,date_created'
    })
    
    if "error" in result:
        return f"Error fetching opinion {opinion_id}: {result['error']}"
    
    # Safely extract case information
    try:
        cluster = result.get('cluster', {})
        if isinstance(cluster, dict):
            case_name = cluster.get('case_name', 'Unknown Case')
            date_filed = cluster.get('date_filed', 'Unknown Date')
            docket = cluster.get('docket', {})
            if isinstance(docket, dict):
                court = docket.get('court', {})
                court_name = court.get('full_name', 'Unknown Court') if isinstance(court, dict) else str(court)
            else:
                court_name = 'Unknown Court'
        else:
            case_name = 'Unknown Case'
            date_filed = 'Unknown Date'
            court_name = 'Unknown Court'
        
        author = result.get('author_str', 'Unknown Author')
        
    except Exception as e:
        return f"Error parsing case information: {str(e)}"
    
    # Get opinion text
    opinion_text = result.get('plain_text', '') or result.get('html', '')
    
    if not opinion_text:
        return f"Error: No text available for {case_name} (Opinion ID: {opinion_id}). This case may only have a PDF version."
    
    # Limit text length
    try:
        max_length = int(max_text_length)
        if len(opinion_text) > max_length:
            opinion_text = opinion_text[:max_length] + "\\n\\n[TEXT TRUNCATED FOR ANALYSIS]"
    except ValueError:
        max_length = 10000
        opinion_text = opinion_text[:max_length]
    
    # Create analysis prompt based on summary type
    if summary_type == "overview":
        structure = """
1. CASE OVERVIEW (2-3 sentences)
2. KEY FACTS (bullet points)
3. LEGAL ISSUE(S) (what questions did the court address?)
4. HOLDING (the court's decision)
5. REASONING (why the court decided this way)
6. SIGNIFICANCE (impact and importance)
"""
    elif summary_type == "legal_analysis":
        structure = """
1. PROCEDURAL POSTURE (how the case got to this court)
2. LEGAL STANDARDS APPLIED (tests, precedents cited)
3. MAJORITY OPINION ANALYSIS
4. CONCURRING/DISSENTING OPINIONS (if any)
5. PRECEDENTIAL VALUE (how this affects future cases)
6. CRITICAL ANALYSIS (strengths/weaknesses of reasoning)
"""
    elif summary_type == "key_holdings":
        structure = """
1. PRIMARY HOLDING (main legal rule established)
2. SECONDARY HOLDINGS (other legal principles)
3. RATIO DECIDENDI (essential reasoning)
4. OBITER DICTA (non-binding observations)
5. PRACTICAL IMPLICATIONS (how this applies in practice)
"""
    else:
        structure = """
1. CASE SUMMARY
2. KEY LEGAL POINTS
3. COURT'S REASONING
4. IMPACT AND SIGNIFICANCE
"""
    
    # Build final analysis request
    analysis_text = f"""CASE SUMMARY ANALYSIS
{'='*60}

📋 Case: {case_name}
🏛️ Court: {court_name}
📅 Date: {date_filed}
✍️ Author: {author}
📊 Analysis Type: {summary_type.title()}
📄 Text Length: {len(opinion_text):,} characters
🆔 Opinion ID: {opinion_id}

🔗 Full Case: https://www.courtlistener.com/opinion/{opinion_id}/

{'='*60}

ANALYSIS REQUEST:
Please analyze the following case and provide a {summary_type} summary using this structure:
{structure}

FULL CASE TEXT:
{'-'*40}
{opinion_text}
{'-'*40}

Please provide a comprehensive {summary_type} analysis following the structure above.
"""
    
    return analysis_text

@mcp.tool()
def compare_cases(
    case1_identifier: str,
    case2_identifier: str,
    comparison_focus: str = "holdings"
) -> str:
    """
    Compare two cases side by side.
    
    Args:
        case1_identifier: First case (opinion ID, URL, or citation)
        case2_identifier: Second case (opinion ID, URL, or citation)  
        comparison_focus: What to compare (holdings, reasoning, facts, outcomes)
    """
    
    # Get both cases
    case1_summary = get_case_summary(case1_identifier, "overview", "8000")
    case2_summary = get_case_summary(case2_identifier, "overview", "8000")
    
    if "Error:" in case1_summary:
        return f"Case 1 Error: {case1_summary}"
    if "Error:" in case2_summary:
        return f"Case 2 Error: {case2_summary}"
    
    comparison_prompt = f"""
COMPARATIVE CASE ANALYSIS
{'='*60}

🔍 Comparison Focus: {comparison_focus.title()}

CASE 1:
{case1_summary}

{'='*60}

CASE 2:
{case2_summary}

{'='*60}

COMPARATIVE ANALYSIS REQUEST:
Please compare these two cases focusing on {comparison_focus}. Structure your analysis as:

1. SIMILARITIES (how are these cases alike?)
2. DIFFERENCES (key distinctions between the cases)
3. CONFLICTING/CONSISTENT HOLDINGS (do they agree or disagree?)
4. PRECEDENTIAL RELATIONSHIP (does one cite the other? hierarchy?)
5. PRACTICAL IMPLICATIONS (how do these cases work together in practice?)
6. SYNTHESIS (what can we learn from comparing these cases?)

Focus particularly on {comparison_focus} in your analysis.
"""
    
    return comparison_prompt

@mcp.tool()
def extract_case_citations(case_identifier: str, citation_type: str = "all") -> str:
    """
    Extract and analyze citations from a case.
    
    Args:
        case_identifier: Opinion ID, URL, or citation
        citation_type: Type of citations to focus on (all, precedents, statutes, secondary)
    """
    
    # Get opinion ID
    opinion_id = None
    if case_identifier.isdigit():
        opinion_id = case_identifier
    elif "opinion/" in case_identifier:
        parts = case_identifier.split("/opinion/")
        if len(parts) > 1:
            opinion_id = parts[1].split("/")[0]
    
    if not opinion_id:
        return f"Error: Could not determine opinion ID from '{case_identifier}'"
    
    # Get full opinion text
    result = make_api_request(f"opinions/{opinion_id}", {
        'fields': 'id,cluster,plain_text,html'
    })
    
    if "error" in result:
        return result["error"]
    
    cluster = result.get('cluster', {})
    case_name = cluster.get('case_name', 'Unknown Case')
    
    opinion_text = result.get('plain_text', '') or result.get('html', '')
    if not opinion_text:
        return f"Error: No text available for citation analysis in {case_name}"
    
    # Limit text for analysis
    if len(opinion_text) > 15000:
        opinion_text = opinion_text[:15000] + "... [TEXT TRUNCATED FOR CITATION ANALYSIS]"
    
    citation_prompt = f"""
CITATION ANALYSIS REQUEST
{'='*50}

📋 Case: {case_name}
🔍 Citation Type: {citation_type.title()}

CASE TEXT FOR CITATION ANALYSIS:
{'-'*40}
{opinion_text}
{'-'*40}

CITATION ANALYSIS REQUEST:
Please analyze the citations in this case and provide:

1. CASE CITATIONS (other court cases cited)
   - Supreme Court cases
   - Circuit court cases
   - State court cases
   - How each case is used (supporting, distinguishing, etc.)

2. STATUTORY CITATIONS (laws and regulations cited)
   - Federal statutes
   - State statutes  
   - Constitutional provisions
   - Regulations

3. SECONDARY SOURCES (if any)
   - Law review articles
   - Treatises
   - Other scholarly sources

4. CITATION PATTERNS
   - Most frequently cited authorities
   - How citations support the court's reasoning
   - Any notable omissions

Focus on {citation_type} citations and explain how they contribute to the court's analysis.
"""
    
    return citation_prompt

@mcp.tool()
def analyze_case_impact(case_identifier: str, analysis_depth: str = "comprehensive") -> str:
    """
    Analyze the broader impact and significance of a case.
    
    Args:
        case_identifier: Opinion ID, URL, or citation
        analysis_depth: Level of analysis (basic, comprehensive, scholarly)
    """
    
    # First get the case summary
    case_summary = get_case_summary(case_identifier, "legal_analysis", "12000")
    
    if "Error:" in case_summary:
        return case_summary
    
    impact_prompt = f"""
CASE IMPACT ANALYSIS
{'='*50}

📊 Analysis Depth: {analysis_depth.title()}

{case_summary}

{'='*50}

IMPACT ANALYSIS REQUEST:
Based on the case information above, please provide a {analysis_depth} analysis of this case's impact and significance:

1. IMMEDIATE IMPACT
   - Direct effects on the parties
   - Immediate legal consequences

2. PRECEDENTIAL IMPACT  
   - What legal principles does this establish?
   - How does this change existing law?
   - What future cases will cite this?

3. BROADER LEGAL IMPACT
   - Effects on the area of law
   - Impact on legal practice
   - Changes to legal standards or tests

4. SOCIETAL/POLICY IMPACT
   - Real-world consequences
   - Effects on different groups/interests
   - Policy implications

5. HISTORICAL SIGNIFICANCE
   - Place in legal history
   - Relationship to major legal developments
   - Long-term consequences

6. CRITICISMS AND CONTROVERSIES
   - Academic criticism
   - Practical problems
   - Ongoing debates

Please provide specific examples and explain the reasoning behind your impact assessment.
"""
    
    return impact_prompt
    """Check API status and authentication."""
    token = get_api_token()
    
    if not token:
        return "❌ No API token found. Set COURTLISTENER_API_TOKEN environment variable.\n\nTo get a token:\n1. Visit https://www.courtlistener.com/api/\n2. Sign up for a free account\n3. Generate an API token\n4. Set: export COURTLISTENER_API_TOKEN='your_token_here'"
    
    # Test API with a simple request
    result = make_api_request("courts", {"fields": "id", "id": "scotus"})
    
    if "error" in result:
        return f"❌ API Error: {result['error']}\n\nCheck your token and network connection."
    
    return f"""✅ CourtListener API v4 Status: Connected

🔑 Authentication: Valid token found
📊 Rate Limit: 5,000 queries/hour (authenticated)
🌐 Base URL: {COURTLISTENER_BASE_URL}
📚 Available Tools: search_cases, lookup_citation, search_dockets, get_opinion_by_id, search_courts, search_people, search_with_pagination

Common Court Codes:
• scotus - Supreme Court of the United States  
• ca1-ca11 - Circuit Courts of Appeals (1st-11th)
• cadc - D.C. Circuit Court of Appeals
• cafc - Federal Circuit Court of Appeals
• fd - Federal District Courts
• fb - Federal Bankruptcy Courts

Rate Limits:
• General API: 5,000 queries/hour
• Citation Lookup: 60 citations/minute
• Maintenance: Thursdays 21:00-23:59 PT

Ready for legal research! 🏛️"""

# Keep your original greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}! Ready to research legal cases with CourtListener API v4."