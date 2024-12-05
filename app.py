import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
from google.ai.generativelanguage import Content, Part, Blob
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Flask configuration
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Retrieve and configure API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise Exception("API key not found. Please set the GOOGLE_API_KEY environment variable.")
else:
    genai.configure(api_key=API_KEY)

# Initialize the Google Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Prompt template for the analysis
generic_template = '''You are a knowledgeable AI assistant. Analyze the uploaded image of one or more eatable items or products for their freshness and provide a customer-friendly report using the following format:

For each item detected in the image, provide the following details:
Item Number:"Give the number as you go on detecting elements"
Item Name:"Name of the eatable item"
Direction: "Position/direction of the item in the image, e.g., 'top-left,' 'center,' 'bottom-right,' etc."
Freshness Index: "FI (Out of 10)",Status: "Fresh/Moderately Fresh/Overripe/Stale/etc."
Visual Color: "Brief description of the item’s color and how it indicates its freshness"
Surface Texture: "Brief description of the surface condition and texture"
Firmness Level: "Brief description of how firm or soft the item likely is, if applicable"
Packaging Condition: "Description of packaging condition or surface elements, if applicable"
Estimated Shelf Life: "Estimated shelf life based on freshness assessment"
Recommendation: "Practical recommendation like 'ready to eat,' 'consume soon,' or 'not suitable for consumption'"

If there are multiple eatables in the image, list each item separately using the above format.also remember do not use any other formate like for the response,strictly adhere to the the one mentioned above else the world might collapse,do not use any characters like '\' or '*'
also very important if the image uploaded is not a eatable item or product, then please mention that the the analysis of the respective field mentioned above is not possible dont leave any field empty.
'''

# Create a structured prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", generic_template),
        ("user", "{text}")
    ]
)

# Output parser
parser = StrOutputParser()

# Analysis function
def analyze_image(file_path):
    try:
        with open(file_path, "rb") as file:
            bytes_data = file.read()

        # Prepare content parts
        content_parts = [
            Part(text=generic_template),
            Part(inline_data=Blob(mime_type="image/jpeg", data=bytes_data))
        ]

        # Generate content
        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(Content(parts=content_parts), stream=True)
        response.resolve()

        # Parse result
        parsed_response = parser.invoke(response.text)
        return parsed_response

    except Exception as e:
        return str(e)

# Flask routes
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Call the image analysis function and get the result
        result = analyze_image(file_path)

        # Split the result by two newlines to separate items
        items = []
        for item in result.split("\n\n"):
            item_details = {}
            # Split each item by single newlines to extract key-value pairs
            for line in item.split("\n"):
                if ':' in line:
                    key, value = line.split(":", 1)
                    item_details[key.strip()] = value.strip()

            items.append(item_details)

        # Return the parsed result as JSON
        return jsonify({"items": items})

    return jsonify({'error': 'File type not allowed'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0',port='8080',debug=True)
