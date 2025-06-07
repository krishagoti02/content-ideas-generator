import os
import uuid
import json
import concurrent.futures
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from anthropic import Anthropic
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from PIL import Image
from docx import Document

# Load environment variables
load_dotenv()
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv("SECRET_KEY", "devkey")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
UPLOAD_FOLDER = "uploads"
STORY_FOLDER = "stories"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STORY_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def ask_claude(prompt, max_tokens=1000):
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=max_tokens,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        return ''.join(block.text for block in response.content if hasattr(block, "text"))
    except Exception as e:
        return f"Claude API error: {e}"

def extract_text(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".docx":
        return "\n".join([p.text for p in Document(file_path).paragraphs])
    elif ext in [".png", ".jpg", ".jpeg"]:
        return f"[Image uploaded: {os.path.basename(file_path)}]"
    return ""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Collect all form inputs into a single text
        user_input = request.form.get("user_input", "")
        
        uploaded_files = request.files.getlist("file")
        extra_text = ""

        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                extra_text += "\n\n" + extract_text(path)

        combined_text = user_input + extra_text

        # Create more effective prompts for social media content
        prompts = {
            "linkedin": 
                "You are a LinkedIn content creator specializing in professional storytelling. Based on the user's input, "
                "create an engaging LinkedIn post that would resonate with their professional network.\n\n"
                "Guidelines:\n"
                "1. Write in first person with a professional yet authentic voice\n"
                "2. Include a strong opening hook that captures attention\n"
                "3. Share a meaningful insight, lesson, or story that demonstrates expertise or values\n"
                "4. End with a thought-provoking question or call to action to encourage engagement\n"
                "5. Keep the post between 1200-1500 characters (LinkedIn's sweet spot)\n"
                "6. Format with clear paragraph breaks and use emojis sparingly if appropriate\n\n"
                "The post should feel authentic, valuable, and encourage professional conversation.",
                
            "instagram": 
                "You are an Instagram content strategist. Based on the user's input, "
                "create 5 distinct Instagram post content ideas they could use.\n\n"
                "For each idea, provide:\n"
                "1. A brief description of the visual content (what the image/video should show)\n"
                "2. A compelling caption (1-3 sentences)\n"
                "3. 3-5 relevant hashtags\n"
                "4. A suggestion for the type of post (carousel, single image, video, reel)\n\n"
                "Make each idea different in tone and purpose (inspirational, educational, behind-the-scenes, etc.).\n"
                "Format as a numbered list with clear sections for each post idea.",
                
            "twitter": 
                "You are a Twitter/X content strategist. Based on the user's input, "
                "create 5 diverse tweet ideas they could share.\n\n"
                "For each tweet idea:\n"
                "1. Write the actual tweet text (under 280 characters)\n"
                "2. Suggest if it should include an image, poll, or link\n"
                "3. Note what time of day might be best to post it\n"
                "4. Include 1-2 relevant hashtags where appropriate\n\n"
                "Create a mix of: thought leadership, questions, personal insights, and inspirational content.\n"
                "Format as a numbered list with each tweet idea clearly separated."
        }

        limits = {
            "linkedin": 700, 
            "instagram": 500, 
            "twitter": 500
        }

        prompts = {k: v + f"\n\nUSER INPUT:\n{combined_text}" for k, v in prompts.items()}
        token = str(uuid.uuid4())

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_key = {
                executor.submit(ask_claude, prompts[key], limits[key]): key for key in prompts
            }
            results = {
                future_to_key[future]: future.result() for future in concurrent.futures.as_completed(future_to_key)
            }

        with open(os.path.join(STORY_FOLDER, f"{token}.json"), "w", encoding="utf-8") as f:
            json.dump(results, f)

        return redirect(url_for("view_story", token=token))

    return render_template("index.html")

@app.route("/story/<token>")
def view_story(token):
    path = os.path.join(STORY_FOLDER, f"{token}.json")
    if not os.path.exists(path):
        return "Story not found", 404
    with open(path, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Ordered display keys for structured rendering
    ordered_keys = ["linkedin", "instagram", "twitter"]
    ordered_results = {key: results.get(key, "") for key in ordered_keys if key in results}

    return render_template("book.html", results=ordered_results, token=token, ordered_keys=ordered_keys, center_text=True)

@app.route("/api/story/<token>")
def api_story(token):
    path = os.path.join(STORY_FOLDER, f"{token}.json")
    if not os.path.exists(path):
        return jsonify({"error": "Story not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/download/<token>")
def download_story(token):
    path = os.path.join(STORY_FOLDER, f"{token}.json")
    if not os.path.exists(path):
        return "Story not found", 404
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_path = os.path.join(STORY_FOLDER, f"{token}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for section, content in data.items():
            f.write(f"\n\n=== {section.upper()} ===\n{content}\n")

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5014)
