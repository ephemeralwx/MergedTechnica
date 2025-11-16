#!/usr/bin/env python3
"""
Agent Server - Flask API bridge for Electron app
Runs the autonomous GUI agent based on commands from the Electron frontend
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import queue
import time
from datetime import datetime
import sys

# Add parent directory to path to import agent modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from main agent system
from main import run_autonomous_agent, VLMModel, LOG_DIR

app = Flask(__name__)
CORS(app)  # Enable CORS for Electron app

# Global state
agent_status = {
    "running": False,
    "goal": None,
    "iteration": 0,
    "last_action": None,
    "error": None,
    "logs_dir": LOG_DIR
}

agent_thread = None
vlm_model = None
stop_requested = False

# Queue for status updates
status_queue = queue.Queue()


def load_model():
    """Load the VLM model once at startup"""
    global vlm_model
    print("🔄 Loading GUI-Actor model...")
    vlm_model = VLMModel()
    if vlm_model.load():
        print("✅ Model loaded successfully!")
        # Add a ready flag since VLMModel doesn't have one
        vlm_model.ready = True
        return True
    else:
        print("❌ Failed to load model")
        vlm_model.ready = False
        return False


def run_agent_background(goal):
    """Run the agent in a background thread"""
    global agent_status, stop_requested
    
    try:
        agent_status["running"] = True
        agent_status["goal"] = goal
        agent_status["error"] = None
        agent_status["iteration"] = 0
        
        print(f"\n🚀 Starting agent with goal: {goal}")
        
        # Run the autonomous agent
        success = run_autonomous_agent(goal, max_iterations=20)
        
        agent_status["running"] = False
        if success:
            print(f"✅ Goal completed: {goal}")
        else:
            print(f"⚠️  Goal incomplete: {goal}")
            
    except Exception as e:
        agent_status["running"] = False
        agent_status["error"] = str(e)
        print(f"❌ Agent error: {e}")
        import traceback
        traceback.print_exc()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": vlm_model is not None and getattr(vlm_model, 'ready', False),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/agent/start', methods=['POST'])
def start_agent():
    """Start the agent with a goal"""
    global agent_thread, agent_status, stop_requested
    
    try:
        data = request.json
        goal = data.get('goal', '').strip()
        
        if not goal:
            return jsonify({"error": "No goal provided"}), 400
        
        if agent_status["running"]:
            return jsonify({"error": "Agent is already running"}), 400
        
        if not vlm_model or not getattr(vlm_model, 'ready', False):
            return jsonify({"error": "Model not loaded or not ready"}), 500
        
        # Reset stop flag
        stop_requested = False
        
        # Start agent in background thread
        agent_thread = threading.Thread(target=run_agent_background, args=(goal,), daemon=True)
        agent_thread.start()
        
        return jsonify({
            "message": "Agent started",
            "goal": goal,
            "status": "running"
        })
    except Exception as e:
        print(f"❌ Error in start_agent: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/agent/stop', methods=['POST'])
def stop_agent():
    """Stop the running agent"""
    global agent_status, stop_requested
    
    if not agent_status["running"]:
        return jsonify({"message": "Agent is not running"}), 200
    
    stop_requested = True
    agent_status["running"] = False
    
    return jsonify({
        "message": "Agent stop requested",
        "status": "stopped"
    })


@app.route('/agent/status', methods=['GET'])
def get_status():
    """Get current agent status"""
    return jsonify(agent_status)


def initialize_server():
    """Initialize the server and load model"""
    print("\n" + "="*70)
    print("🤖 AGENT SERVER - Starting")
    print("="*70 + "\n")
    
    if not load_model():
        print("❌ Failed to initialize server - model loading failed")
        sys.exit(1)
    
    print("\n✅ Server initialized successfully!")
    print("📡 Listening for commands from Electron app...\n")


if __name__ == '__main__':
    # Initialize before starting Flask
    initialize_server()
    
    # Run Flask server
    app.run(
        host='127.0.0.1',
        port=5001,  # Different port from Electron to avoid conflicts
        debug=False,
        threaded=True
    )