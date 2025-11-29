from bot import find_sign_link

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route("/sora", methods=["POST","OPTIONS"])
def sora():
    # Parse JSON from request
    if request.method == "OPTIONS":
        response = jsonify({"status": "OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200
    
    data = request.get_json(force=True)  # force=True ignores content type
    if not data:
        return jsonify({"error": "No data received"}), 400
    signedlink = find_sign_link(data['url'])
    return jsonify({"status": "success", "received": signedlink})

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
    
print()
