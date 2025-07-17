import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv
from openai import AzureOpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Get environment variables
azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
azure_oai_key = os.getenv("AZURE_OAI_KEY")
azure_oai_deployment = os.getenv("AZURE_OAI_DEPLOYMENT")
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX")

# Debug: Print environment variables (remove in production)
print("=== Environment Variables Debug ===")
print(f"AZURE_OAI_ENDPOINT: {azure_oai_endpoint}")
print(f"AZURE_OAI_DEPLOYMENT: {azure_oai_deployment}")
print(f"AZURE_SEARCH_ENDPOINT: {azure_search_endpoint}")
print(f"AZURE_SEARCH_INDEX: {azure_search_index}")
print(f"Keys present: OAI={bool(azure_oai_key)}, Search={bool(azure_search_key)}")

# Check if all required environment variables are present
missing_vars = []
if not azure_oai_endpoint:
    missing_vars.append("AZURE_OAI_ENDPOINT")
if not azure_oai_key:
    missing_vars.append("AZURE_OAI_KEY")
if not azure_oai_deployment:
    missing_vars.append("AZURE_OAI_DEPLOYMENT")
if not azure_search_endpoint:
    missing_vars.append("AZURE_SEARCH_ENDPOINT")
if not azure_search_key:
    missing_vars.append("AZURE_SEARCH_KEY")
if not azure_search_index:
    missing_vars.append("AZURE_SEARCH_INDEX")

if missing_vars:
    print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file")

try:
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=azure_oai_endpoint,
        api_key=azure_oai_key,
        api_version="2024-02-15-preview"
    )
    print("Azure OpenAI client initialized successfully")
except Exception as e:
    print(f"ERROR initializing Azure OpenAI client: {str(e)}")
    client = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        print("=== New Request ===")
        
        # Check if client is initialized
        if client is None:
            print("ERROR: Azure OpenAI client not initialized")
            return jsonify({"error": "Server configuration error"}), 500
        
        # Get user input
        if not request.json:
            print("ERROR: No JSON data received")
            return jsonify({"error": "No JSON data provided"}), 400
            
        user_input = request.json.get('message', '')
        print(f"User input: '{user_input}'")
        
        if not user_input:
            print("ERROR: Empty user input")
            return jsonify({"error": "No question provided"}), 400
        
        # Configure data source for Azure AI Search
        extension_config = {
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": azure_search_endpoint,
                        "index_name": azure_search_index,
                        "authentication": {
                            "type": "api_key",
                            "key": azure_search_key
                        }
                    }
                }
            ]
        }
        
        print("Sending request to Azure OpenAI...")
        
        # Send request to Azure OpenAI
        response = client.chat.completions.create(
            model=azure_oai_deployment,
            temperature=0.5,
            max_tokens=1000,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an athlete recovery chatbot. When you cite something, use the name title of the document you retrieved the information from. Also, if you cite something with [doc1] write Sauna.pdf before it"
                },
                {
                    "role": "user", 
                    "content": f'Use the data from the search results and cite the metadata you used in your response: {user_input}'
                }
            ],
            extra_body=extension_config
        )
        
        print("Response received from Azure OpenAI")
        response_content = response.choices[0].message.content
        print(f"Response content: {response_content[:200]}...")  # Print first 200 chars
        
        return jsonify({"response": response_content})
        
    except Exception as ex:
        print(f"ERROR in /ask route: {str(ex)}")
        print(f"Error type: {type(ex).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(ex)}"}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "client_initialized": client is not None,
        "missing_env_vars": missing_vars if 'missing_vars' in globals() else []
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)