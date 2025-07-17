import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv
from openai import AzureOpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()
azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
azure_oai_key = os.getenv("AZURE_OAI_KEY")
azure_oai_deployment = os.getenv("AZURE_OAI_DEPLOYMENT")
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX")


# Initialize Azure OpenAI client
client = AzureOpenAI(
    base_url=f"{azure_oai_endpoint}/openai/deployments/{azure_oai_deployment}/extensions",
    api_key=azure_oai_key,
    api_version="2023-09-01-preview"
)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        user_input = request.json.get('message', '')

        if not user_input:
            return jsonify({"error": "No question provided"}), 400
        
        # Configure data source
        extension_config = {
            "dataSources": [
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": {
                        "endpoint": azure_search_endpoint,
                        "key": azure_search_key,
                        "indexName": azure_search_index,
                    }
                }
            ]
        }

        # Send request to Azure OpenAI
        response = client.chat.completions.create(
            model=azure_oai_deployment,
            temperature=0.5,
            max_tokens=1000,
            messages=[{"role": "system", "content": "You are an athlete recovery chatbot. When you cite something, use the name title of the document you retrieved the information from. also, if you site something with [doc1] write Sauna.pdf before it"},
                     {"role": "user", "content": 'Use the data from the extra body and cite the metadata you used in your response'+user_input}],
            extra_body=extension_config
        )

        return jsonify({"response": response.choices[0].message.content})

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
