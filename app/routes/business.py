"""
LeadForge API - Business Routes
This module handles all business-related endpoints for the LeadForge application.
It provides functionality for:
- Uploading and processing CSV files of businesses
- Filtering and searching businesses
- Finding business websites
- Generating personalized email drafts
"""

import os
import pandas as pd
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
from googleapiclient.discovery import build
# import google.generativeai as genai  # No longer needed for REST API
import json
import uuid

# Initialize Flask Blueprint
bp = Blueprint('business', __name__)

# Constants
ALLOWED_EXTENSIONS = {'csv'}

# In-memory storage for businesses (will be replaced with a database in production)
businesses_list = []

# Define the column mapping
COLUMN_MAPPING = {
    'business_name': {
        'required': True,
        'displayName': 'Business Name'
    },
    'industry': {
        'required': True,
        'displayName': 'Industry'
    },
    'location': {
        'required': True,
        'displayName': 'Location'
    }
}

# --- Helper Functions ---

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def search_business_website(business_name, location):
    """
    Search for a business website using Google Custom Search API.
    
    Args:
        business_name (str): Name of the business
        location (str): Location of the business
        
    Returns:
        str: URL of the business website if found, None otherwise
    """
    try:
        # Get API credentials from environment
        api_key = os.getenv('GOOGLE_API_KEY')
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        print(f"\nSearching for website:")
        print(f"Business: {business_name}")
        print(f"Location: {location}")
        print(f"API Key present: {bool(api_key)}")
        print(f"Search Engine ID present: {bool(search_engine_id)}")
        
        if not api_key or not search_engine_id:
            print("Missing Google API credentials")
            return None
        
        # Initialize the Custom Search API service
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Try different search variations if the first one fails
        search_variations = [
            f'"{business_name}" official website {location}',
            f'"{business_name}" website {location}',
            f'"{business_name}" {location}',
            f'"{business_name}" official website'
        ]
        
        for search_query in search_variations:
            try:
                # Execute the search
                result = service.cse().list(
                    q=search_query,
                    cx=search_engine_id,
                    num=3,  # Get more results to filter through
                    siteSearchFilter='i',  # Only include results from the main site
                    excludeTerms='pdf doc xls ppt',  # Exclude common document types
                    dateRestrict='y[1]'  # Restrict to last year
                ).execute()
                
                # Extract and filter results
                if 'items' in result and result['items']:
                    for item in result['items']:
                        url = item['link']
                        # Skip PDFs, documents, and non-HTML pages
                        if any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
                            continue
                        # Skip social media profiles
                        if any(site in url.lower() for site in ['facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com']):
                            continue
                        # Skip directory listings
                        if any(term in url.lower() for term in ['directory', 'listing', 'yellowpages', 'whitepages']):
                            continue
                        # Skip government and educational sites unless specifically relevant
                        if any(term in url.lower() for term in ['.gov', '.edu']) and not any(term in business_name.lower() for term in ['university', 'college', 'school', 'government']):
                            continue
                        
                        print(f"Found potential website: {url}")
                        return url
                
                print(f"No valid results found for query: {search_query}")
                
            except Exception as e:
                print(f"Error with search query '{search_query}': {str(e)}")
                # If we hit a rate limit, wait and try again
                if 'quota' in str(e).lower():
                    print("Rate limit hit, waiting 2 seconds...")
                    time.sleep(2)
                    continue
                # For other errors, try the next variation
                continue
        
        print("No valid results found for any search variation")
        return None
            
    except Exception as e:
        print(f"Error searching for website: {str(e)}")
        return None

def verify_website(url):
    """
    Verify if a website is valid and accessible.
    
    Args:
        url (str): URL to verify
        
    Returns:
        bool: True if website is accessible, False otherwise
    """
    try:
        print(f"\nVerifying website: {url}")
        
        # Set up headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Try with and without https
        urls_to_try = [url]
        if not url.startswith('http'):
            urls_to_try = [f'https://{url}', f'http://{url}']
        
        for url_to_try in urls_to_try:
            try:
                response = requests.get(url_to_try, headers=headers, timeout=5)
                print(f"Website verification status code: {response.status_code}")
                
                # Check for common blocking patterns
                if response.status_code == 403:
                    print("WARNING: Website returned 403 Forbidden - might be blocking automated access")
                    continue
                    
                if "captcha" in response.text.lower():
                    print("WARNING: Website is showing a CAPTCHA")
                    continue
                    
                if response.status_code == 200:
                    return True
                    
            except Exception as e:
                print(f"Error verifying {url_to_try}: {str(e)}")
                continue
        
        return False
        
    except Exception as e:
        print(f"Website verification error: {str(e)}")
        return False

def call_gemini_api(prompt):
    """
    Call the Gemini API to generate content.
    
    Args:
        prompt (str): The prompt to send to the API
        
    Returns:
        tuple: (generated_text, error_message)
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None, 'GEMINI_API_KEY not set in environment.'
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            # Extract the generated text
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text, None
        else:
            return None, f"Gemini API error: {response.status_code} {response.text}"
    except Exception as e:
        return None, str(e)

def generate_email_prompt(business, user_prompt_template):
    """
    Generate a prompt for the Gemini API based on business details and user template.
    
    Args:
        business (dict): Business details
        user_prompt_template (str): User's custom instructions for email generation
        
    Returns:
        str: Formatted prompt for the Gemini API
    """
    # Extract business details
    business_name = business.get('business_name', '')
    industry = business.get('industry', 'general business')
    location = business.get('location', '')
    has_website = 'has an existing website' if business.get('website') else 'no website found'
    
    # Construct the base prompt
    base_prompt = f"""
    You are a professional web design consultant writing an email to a potential client.
    
    Business Details:
    - Name: {business_name}
    - Industry: {industry}
    - Location: {location}
    - Website Status: {has_website}
    
    User's Custom Instructions:
    {user_prompt_template}
    
    Please generate a concise, friendly, and professional email offering web design services.
    The email should be personalized based on the business details and follow the user's instructions.
    Keep the email under 200 words and focus on value proposition.
    """
    
    return base_prompt

def parse_address(address):
    """Parse address to extract city and state."""
    if not address:
        return None, None
    
    # Common state abbreviations
    state_abbreviations = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    # Split address by commas
    parts = [part.strip() for part in address.split(',')]
    
    # Look for state in the last part
    state = None
    city = None
    
    if len(parts) >= 2:
        # The last part should contain state and zip
        last_part = parts[-1].strip()
        # Split by space to separate state and zip
        state_zip = last_part.split()
        if state_zip and state_zip[0].upper() in state_abbreviations:
            state = state_zip[0].upper()
            # The part before the last should be the city
            city = parts[-2].strip()
    
    return city, state

def process_csv(file_path):
    """Process the CSV file and return the data"""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Validate required columns
        missing_columns = [col for col, config in COLUMN_MAPPING.items() 
                         if config['required'] and col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Process each row
        businesses = []
        for index, row in df.iterrows():
            business = {
                'id': str(uuid.uuid4()),
                'business_name': str(row['business_name']).strip(),
                'industry': str(row['industry']).strip(),
                'industry_display_name': COLUMN_MAPPING['industry'].get('displayName', 'Industry'),
                'location': str(row['location']).strip(),
                'website': None,
                'email': None,
                'city': None,
                'state': None
            }
            
            # Parse address to extract city and state
            if business['location']:
                parsed_address = parse_address(business['location'])
                if parsed_address:
                    business['city'] = parsed_address.get('city')
                    business['state'] = parsed_address.get('state')
            
            businesses.append(business)
        
        return businesses
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise

# --- API Endpoints ---

@bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify API is working."""
    return jsonify({
        'status': 'success',
        'message': 'LeadForge API is working!'
    })

@bp.route('/column_mapping', methods=['GET'])
def get_column_mapping():
    """
    Get the current column mapping configuration.
    
    Returns:
        JSON response with the column mapping
    """
    try:
        return jsonify({
            'mapping': COLUMN_MAPPING
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error getting column mapping: {str(e)}'}), 500

@bp.route('/upload', methods=['POST'])
def upload_csv():
    """
    Upload and process a CSV file containing business data.
    
    Expected request format:
    {
        "file": CSV file,
        "column_mapping": {
            "business_name": {
                "column": "name",  # Column name in CSV
                "displayName": "Company Name"  # How to display it in UI
            },
            "industry": {
                "column": "phone",
                "displayName": "Phone Number"
            },
            "location": {
                "column": "address",
                "displayName": "Business Address"
            }
        }
    }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Debug: Print request form data
        print("Request form data:", request.form)
        
        # Read CSV file
        df = pd.read_csv(file)
        print("CSV columns:", df.columns.tolist())
        
        # Get column mapping from request
        column_mapping = json.loads(request.form.get('column_mapping', '{}'))
        print("Received column mapping:", column_mapping)
        
        # Update the global column mapping with display names
        global COLUMN_MAPPING
        for field, config in column_mapping.items():
            if field in COLUMN_MAPPING:
                COLUMN_MAPPING[field]['displayName'] = config.get('displayName', COLUMN_MAPPING[field]['displayName'])
        
        # Validate required fields are mapped
        required_fields = ['business_name', 'industry', 'location']
        missing_fields = [field for field in required_fields if field not in column_mapping]
        if missing_fields:
            return jsonify({
                'error': f'Missing required field mappings: {", ".join(missing_fields)}'
            }), 400
        
        # Create mapping from CSV columns to internal fields
        csv_to_internal = {config['column']: field for field, config in column_mapping.items()}
        
        # Validate mapped columns exist in CSV
        invalid_columns = [config['column'] for config in column_mapping.values() if config['column'] not in df.columns]
        if invalid_columns:
            return jsonify({
                'error': f'Invalid column mappings: {", ".join(invalid_columns)}'
            }), 400
        
        # Rename columns according to mapping
        df = df.rename(columns=csv_to_internal)
        print("Columns after renaming:", df.columns.tolist())
        
        # Clean and validate data
        df = df.dropna(subset=['business_name', 'industry', 'location'])
        df = df[['business_name', 'industry', 'location']]
        
        # Convert to list of dictionaries
        businesses = df.to_dict('records')
        
        # Add website field and ID
        for i, business in enumerate(businesses):
            business['website'] = None
            business['id'] = str(uuid.uuid4())  # Use UUID instead of index
        
        # Store in memory
        global businesses_list
        businesses_list = businesses
        
        return jsonify({
            'message': 'File uploaded successfully',
            'records_count': len(businesses),
            'preview': businesses[:5],
            'column_mapping': COLUMN_MAPPING
        })
        
    except Exception as e:
        print("Error during upload:", str(e))
        return jsonify({'error': str(e)}), 500

@bp.route('/businesses', methods=['GET'])
def filter_businesses():
    """
    Filter businesses based on various criteria.
    
    Query Parameters:
    - business_name (optional): Filter by business name
    - industry (optional): Filter by industry
    - location (optional): Filter by location
    - page (optional): Page number for pagination (default: 1)
    - per_page (optional): Items per page (default: 10)
    
    Returns:
        JSON response with filtered businesses and pagination info
    """
    try:
        # Get filter parameters
        business_name = request.args.get('business_name', '').lower()
        industry = request.args.get('industry', '').lower()
        location = request.args.get('location', '').lower()
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Filter businesses
        filtered = businesses_list
        if business_name:
            filtered = [b for b in filtered if business_name in b['business_name'].lower()]
        if industry:
            filtered = [b for b in filtered if industry in b['industry'].lower()]
        if location:
            filtered = [b for b in filtered if location in b['location'].lower()]
        
        # Calculate pagination
        total = len(filtered)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = filtered[start_idx:end_idx]
        
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'businesses': paginated
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error filtering businesses: {str(e)}'}), 500

@bp.route('/businesses/<string:business_id>/website', methods=['GET'])
def identify_website(business_id):
    """
    Find and verify a website for a specific business.
    
    Args:
        business_id (str): UUID of the business
        
    Returns:
        JSON response with website information
    """
    try:
        # Find the business
        business = next((b for b in businesses_list if b['id'] == business_id), None)
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        
        # Check if website is already identified
        if 'website' in business and business['website']:
            return jsonify({
                'message': 'Website already identified',
                'business': business
            }), 200
        
        # Search for website
        website = search_business_website(business['business_name'], business['location'])
        
        if website and verify_website(website):
            # Update business with website
            business['website'] = website
            return jsonify({
                'message': 'Website identified successfully',
                'business': business
            }), 200
        else:
            return jsonify({
                'message': 'No valid website found',
                'business': business
            }), 404
            
    except Exception as e:
        return jsonify({'error': f'Error identifying website: {str(e)}'}), 500

@bp.route('/businesses/websites', methods=['POST'])
def identify_websites_batch():
    """
    Find and verify websites for multiple businesses in batch.
    
    Request Body:
    {
        "business_ids": [0, 1, 2]  # Array of business IDs
    }
    
    Returns:
        JSON response with website identification results for each business
    """
    try:
        # Get business IDs from request
        business_ids = request.json.get('business_ids', [])
        
        if not business_ids:
            return jsonify({'error': 'No business IDs provided'}), 400
        
        results = []
        for business_id in business_ids:
            if business_id < 0 or business_id >= len(businesses_list):
                results.append({
                    'business_id': business_id,
                    'status': 'error',
                    'message': 'Business not found'
                })
                continue
            
            business = businesses_list[business_id]
            
            # Skip if website already identified
            if 'website' in business and business['website']:
                results.append({
                    'business_id': business_id,
                    'status': 'skipped',
                    'message': 'Website already identified',
                    'business': business
                })
                continue
            
            # Search for website
            website = search_business_website(business['business_name'], business['location'])
            
            if website and verify_website(website):
                # Update business with website
                business['website'] = website
                results.append({
                    'business_id': business_id,
                    'status': 'success',
                    'message': 'Website identified successfully',
                    'business': business
                })
            else:
                results.append({
                    'business_id': business_id,
                    'status': 'error',
                    'message': 'No valid website found',
                    'business': business
                })
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        return jsonify({
            'message': 'Batch website identification completed',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error in batch website identification: {str(e)}'}), 500

@bp.route('/generate_email', methods=['POST'])
def generate_email():
    """
    Generate a personalized email draft for a business using Gemini API.
    
    Request Body:
    {
        "business_id": 0,  # ID of the business
        "user_prompt_template": "Custom instructions for email generation"
    }
    
    Returns:
        JSON response with generated email and business details
    """
    try:
        # Get request data
        data = request.json
        print("\nReceived email generation request:")
        print("Request data:", data)
        
        if not data:
            print("Error: No data provided")
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract required fields
        business_id = data.get('business_id')
        user_prompt_template = data.get('user_prompt_template', '')
        
        print(f"Business ID: {business_id}")
        print(f"User prompt template: {user_prompt_template}")
        
        if business_id is None:
            print("Error: Business ID is required")
            return jsonify({'error': 'Business ID is required'}), 400
            
        # Find the business
        if business_id < 0 or business_id >= len(businesses_list):
            print(f"Error: Business not found with ID {business_id}")
            return jsonify({'error': 'Business not found'}), 404
            
        business = businesses_list[business_id]
        print(f"Found business: {business}")
        
        # Generate the prompt
        prompt = generate_email_prompt(business, user_prompt_template)
        print(f"Generated prompt: {prompt}")
        
        # Generate email using Gemini REST API
        email_text, error = call_gemini_api(prompt)
        if error:
            print(f"Error from Gemini API: {error}")
            return jsonify({
                'error': 'Error generating email',
                'details': error
            }), 500
        
        print(f"Generated email: {email_text}")
        
        return jsonify({
            'message': 'Email generated successfully',
            'email': email_text,
            'business': business
        }), 200
        
    except Exception as e:
        print(f"Unexpected error in email generation: {str(e)}")
        return jsonify({'error': f'Error in email generation: {str(e)}'}), 500

@bp.route('/clear', methods=['POST'])
def clear_data():
    """
    Clear all business data from memory.
    
    Returns:
        JSON response confirming data was cleared
    """
    try:
        global businesses_list
        businesses_list = []
        return jsonify({
            'message': 'All business data cleared successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error clearing data: {str(e)}'}), 500 