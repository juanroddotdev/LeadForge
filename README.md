# LeadForge

LeadForge is a powerful lead generation and management tool that helps businesses find and connect with potential clients. It provides features for:

- Uploading and processing business data from CSV files
- Customizable column mapping for flexible data import
- Intelligent website discovery for businesses
- Email template generation for outreach
- Advanced filtering and search capabilities

## Features

- **CSV Import**: Upload business data with customizable column mapping
- **Website Discovery**: Automatically find and verify business websites
- **Email Generation**: Generate personalized email templates using AI
- **Advanced Filtering**: Search and filter businesses by name, industry, and location
- **Modern UI**: Clean and intuitive user interface built with Vue.js

## Tech Stack

- **Frontend**: Vue.js, TailwindCSS
- **Backend**: Python, Flask
- **AI Integration**: Google Gemini API
- **Search**: Google Custom Search API

## Setup

1. Clone the repository:
```bash
git clone https://github.com/juanroddotdev/LeadForge.git
cd LeadForge
```

2. Set up the Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the development server:
```bash
# Backend
python app.py

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file with the following variables:

```
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
GEMINI_API_KEY=your_gemini_api_key
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Getting API Keys

1. **Google API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Custom Search API
   - Create credentials (API key)

2. **Google Custom Search Engine ID**:
   - Visit [Google Programmable Search Engine](https://programmablesearchengine.google.com)
   - Create a new search engine
   - Get your Search Engine ID (cx)

3. **Google Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key

## Running the Application

1. Start the Flask server:
```bash
python run.py
```

The server will start on `http://localhost:5001`

## API Endpoints

### 1. Test API
```bash
curl http://localhost:5001/api/test
```

### 2. Upload CSV
```bash
curl -X POST -F "file=@your_file.csv" http://localhost:5001/api/upload
```

Required CSV columns:
- business_name
- industry
- location

### 3. Filter Businesses
```bash
curl "http://localhost:5001/api/businesses?business_name=example&industry=tech&location=ny&page=1&per_page=10"
```

### 4. Find Business Website
```bash
curl http://localhost:5001/api/businesses/0/website
```

### 5. Batch Website Search
```bash
curl -X POST -H "Content-Type: application/json" -d '{"business_ids":[0,1,2]}' http://localhost:5001/api/businesses/websites
```

### 6. Generate Email
```bash
curl -X POST -H "Content-Type: application/json" -d '{"business_id":0,"user_prompt_template":"Focus on modern web design and mobile responsiveness"}' http://localhost:5001/api/generate_email
```

## Project Structure

```
LeadForge/
├── app/
│   ├── routes/
│   │   └── business.py    # Business-related endpoints
│   └── __init__.py       # Flask app initialization
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── run.py               # Application entry point
└── README.md            # This file
```

## Development Notes

- The application currently uses in-memory storage for the MVP
- Future versions will implement a proper database
- Rate limiting is implemented for website verification
- Error handling is in place for API failures

## Additional Examples

### Sample CSV Format
```csv
business_name,industry,location
Acme Corp,Technology,New York
Best Bakery,Food & Beverage,Los Angeles
City Dental,Healthcare,Chicago
```

### Example Email Generation Prompts

1. **Modern Design Focus**:
```json
{
    "business_id": 0,
    "user_prompt_template": "Focus on modern, minimalist design and mobile-first approach. Mention our expertise in creating responsive websites that work seamlessly across all devices."
}
```

2. **E-commerce Focus**:
```json
{
    "business_id": 1,
    "user_prompt_template": "Emphasize our e-commerce solutions and online store capabilities. Highlight our experience with payment gateways and inventory management systems."
}
```

3. **Local Business Focus**:
```json
{
    "business_id": 2,
    "user_prompt_template": "Focus on local SEO and Google Business Profile optimization. Mention our experience helping local businesses increase their online visibility."
}
```

### Batch Operations

1. **Upload and Process Multiple Files**:
```bash
# Upload first file
curl -X POST -F "file=@businesses_ny.csv" http://localhost:5001/api/upload

# Upload second file
curl -X POST -F "file=@businesses_la.csv" http://localhost:5001/api/upload
```

2. **Find Websites for Multiple Businesses**:
```bash
# Find websites for businesses with IDs 0-4
curl -X POST -H "Content-Type: application/json" \
     -d '{"business_ids":[0,1,2,3,4]}' \
     http://localhost:5001/api/businesses/websites
```

## Troubleshooting

### Common Issues and Solutions

1. **API Connection Issues**
   - **Error**: "Connection refused" when accessing endpoints
   - **Solution**: 
     - Ensure Flask server is running (`python run.py`)
     - Check if port 5001 is available
     - Verify no firewall is blocking the connection

2. **CSV Upload Problems**
   - **Error**: "Missing required columns"
   - **Solution**:
     - Verify CSV has required columns: business_name, industry, location
     - Check for typos in column names
     - Ensure CSV is properly formatted (no BOM characters)

3. **Website Search Issues**
   - **Error**: "Missing Google API credentials"
   - **Solution**:
     - Verify `.env` file exists and contains correct API keys
     - Check if API keys are valid and have proper permissions
     - Ensure Custom Search API is enabled in Google Cloud Console

4. **Email Generation Failures**
   - **Error**: "GEMINI_API_KEY not set in environment"
   - **Solution**:
     - Check if Gemini API key is set in `.env`
     - Verify API key is valid
     - Check API usage limits

### Debug Mode

To run the application in debug mode for detailed error messages:

```bash
export FLASK_DEBUG=1
python run.py
```

## Testing

### Running Tests

1. **Install Test Dependencies**:
```bash
pip install pytest pytest-cov
```

2. **Run Tests**:
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app tests/

# Run specific test file
pytest tests/test_business_routes.py
```

### Test Files Structure
```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── test_business_routes.py  # Business endpoint tests
├── test_website_search.py   # Website search tests
└── test_email_gen.py       # Email generation tests
```

### Example Test Cases

1. **Testing CSV Upload**:
```python
def test_upload_csv_success(client):
    data = {
        'file': (BytesIO(b'business_name,industry,location\nTest Corp,Tech,NY'), 'test.csv')
    }
    response = client.post('/api/upload', data=data)
    assert response.status_code == 200
    assert 'File uploaded successfully' in response.json['message']
```

2. **Testing Website Search**:
```python
def test_website_search_success(client, mock_google_api):
    response = client.get('/api/businesses/0/website')
    assert response.status_code == 200
    assert 'website' in response.json['business']
```

3. **Testing Email Generation**:
```python
def test_email_generation_success(client, mock_gemini_api):
    data = {
        'business_id': 0,
        'user_prompt_template': 'Test template'
    }
    response = client.post('/api/generate_email', json=data)
    assert response.status_code == 200
    assert 'email' in response.json
```

### Mocking External Services

For testing endpoints that use external services (Google API, Gemini API), use the following fixtures in `conftest.py`:

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_google_api():
    with patch('app.routes.business.build') as mock:
        mock.return_value.cse().list().execute.return_value = {
            'items': [{'link': 'https://example.com'}]
        }
        yield mock

@pytest.fixture
def mock_gemini_api():
    with patch('app.routes.business.requests.post') as mock:
        mock.return_value.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Test email'}]}}]
        }
        mock.return_value.status_code = 200
        yield mock
``` 