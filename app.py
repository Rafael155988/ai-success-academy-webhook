#!/usr/bin/env python3
from flask import Flask
app = Flask(__name__)

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/test")
def test():
    return {"message": "Flask is working!"}, 200

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
