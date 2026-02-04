#!/bin/bash

echo "🚀 Starting AI Travel Planner..."
echo "================================"
echo ""
echo "✅ Make sure Ollama is running on port 11434"
echo "   Check with: curl http://localhost:11434/api/generate"
echo ""
echo "📡 The app will be accessible from external networks"
echo ""

# Run Streamlit with external access
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
