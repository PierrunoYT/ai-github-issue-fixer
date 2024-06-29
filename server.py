from flask import Flask, request, jsonify, send_from_directory
from github_claude_integration import process_github_issue, implement_plan
import os
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

@app.route('/generate_fix', methods=['POST'])
@limiter.limit("10 per minute")
def generate_fix():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.json
    if 'issueUrl' not in data:
        return jsonify({"error": "Missing 'issueUrl' in request"}), 400

    issue_url = data['issueUrl']

    try:
        result = process_github_issue(issue_url)
        return jsonify({
            "message": "Plan generated successfully",
            "suggested_plan": result['suggested_plan']
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@app.route('/implement_plan', methods=['POST'])
@limiter.limit("5 per minute")
def implement_fix():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.json
    if 'issueUrl' not in data:
        return jsonify({"error": "Missing 'issueUrl' in request"}), 400

    issue_url = data['issueUrl']

    try:
        result = implement_plan(issue_url)
        return jsonify({
            "message": "Fix implemented and pull request created",
            "pull_request_url": result['pull_request_url']
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True', host='0.0.0.0')