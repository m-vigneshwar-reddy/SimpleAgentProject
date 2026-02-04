# 🧳 AI Travel Planning Agent

A comprehensive AI-powered travel planner that creates personalized itineraries with hotel recommendations, transportation options, dining suggestions, and essential travel tips.

## ✨ Features

### 🎯 Complete Travel Planning
- **📅 Day-by-Day Itinerary** - Personalized activities for morning, afternoon, and evening
- **🏨 Hotel Recommendations** - 3 options based on your budget and travel purpose
- **🚌 Transportation Options** - Local transport, airport transfers, and day trip options
- **🍽️ Restaurant Suggestions** - Breakfast, lunch, and dinner recommendations
- **💰 Budget Breakdown** - Detailed cost allocation across accommodation, food, activities, and transport
- **💡 Travel Tips** - Essential tips for local customs, safety, and must-have items

### 🎨 Customization Options
- **Travel Purpose**: Leisure, Business, Adventure, Cultural, Romantic, Family, Solo
- **Travel Style**: Relaxed, Balanced, or Packed
- **Budget Range**: From €100 to unlimited
- **Duration**: 1 to 30 days

### 🔄 Smart Features
- **Memory System** - Remembers your previous trips and preferences
- **Feedback System** - Refine itineraries with natural language feedback
- **Cost Tracking** - Real-time budget calculations for each activity

## 🚀 Setup Instructions

### Prerequisites
1. **Python 3.8+** installed
2. **Ollama** installed and running with llama3 model
3. **Internet connection** for external access

### Step 1: Install Ollama
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the llama3 model
ollama pull llama3

# Start Ollama (if not running)
ollama serve
```

### Step 2: Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt
```

### Step 3: Run the Application

#### Option A: Using the startup script (Recommended)
```bash
# Make the script executable
chmod +x start.sh

# Run the app
./start.sh
```

#### Option B: Direct Streamlit command
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

#### Option C: Just run locally
```bash
streamlit run app.py
```

## 🌐 Accessing from Outside

### Local Network Access
1. Find your machine's IP address:
   ```bash
   # Linux/Mac
   ifconfig | grep "inet "
   
   # Windows
   ipconfig
   ```

2. Access from other devices on the same network:
   ```
   http://YOUR_IP_ADDRESS:8501
   ```

### Firewall Configuration

#### Linux (UFW)
```bash
sudo ufw allow 8501
```

#### Linux (Firewalld)
```bash
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

#### Windows
Open Windows Firewall → Allow an app → Add port 8501

### Internet Access (Production)

For public internet access, use one of these options:

1. **Streamlit Cloud** (Easiest - Free)
   - Push code to GitHub
   - Deploy at https://share.streamlit.io

2. **Reverse Proxy with Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

3. **VPS Deployment**
   - Deploy on AWS, DigitalOcean, or similar
   - Configure security groups to allow port 8501

## 📖 Usage Guide

### Creating Your First Travel Plan

1. **Enter Trip Details**
   - Destination (e.g., "Paris", "Tokyo")
   - Number of days (1-30)
   - Total budget in Euros
   - Travel purpose (Leisure, Business, etc.)
   - Travel style (Relaxed, Balanced, Packed)

2. **Click "Generate Complete Travel Plan"**
   - The AI will create a comprehensive plan
   - This may take 30-60 seconds depending on trip duration

3. **Review Your Plan**
   - Budget breakdown
   - Hotel options
   - Transportation recommendations
   - Restaurant suggestions
   - Day-by-day itinerary
   - Important travel tips

4. **Refine if Needed**
   - Provide feedback like:
     - "Day 2 is too busy"
     - "Add more cultural activities to Day 3"
     - "Make Day 1 cheaper"
   - Click "Update Itinerary"

### Example Feedback Commands

- **Reduce Activities**: "Day 2 is too busy" or "Too much walking on Day 3"
- **Add More**: "Add more activities to Day 1"
- **Budget Adjustments**: "Make Day 2 cheaper" or "Upgrade Day 3 to luxury"
- **Activity Changes**: "More cultural activities" or "Less shopping"

## 🏗️ Architecture

### Files Structure
```
.
├── app.py              # Main Streamlit application
├── agent.py            # TravelPlannerAgent class
├── tool.py             # AI functions for suggestions
├── memory.py           # Database operations
├── requirements.txt    # Python dependencies
├── start.sh           # Startup script
├── .streamlit/
│   └── config.toml    # Streamlit configuration
└── travel.db          # SQLite database (created on first run)
```

### How It Works

1. **User Input** → Streamlit form collects trip details
2. **Agent Creation** → TravelPlannerAgent initialized with user preferences
3. **Budget Calculation** → Smart allocation across categories
4. **AI Suggestions** → Ollama generates personalized recommendations for:
   - Hotels (3 options)
   - Transport (3 modes)
   - Restaurants (3 meal types)
   - Activities (3 per day)
   - Travel tips (5 essential tips)
5. **Memory Storage** → Trip saved to SQLite database
6. **Display** → Beautiful UI shows complete plan
7. **Refinement** → Feedback loop for adjustments

## 🔧 Configuration

### Changing the AI Model

Edit `tool.py`:
```python
MODEL = "llama3"  # Change to "mistral", "llama2", etc.
```

### Adjusting Budget Allocation

Edit `tool.py` in `calculate_budget_breakdown()`:
```python
accommodation_pct = 0.35  # 35% for hotels
food_pct = 0.25           # 25% for food
activities_pct = 0.25     # 25% for activities
transport_pct = 0.10      # 10% for transport
misc_pct = 0.05           # 5% for miscellaneous
```

### Customizing Port

Edit `.streamlit/config.toml`:
```toml
[server]
port = 8501  # Change to your desired port
```

## 🐛 Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/generate

# If not running, start it
ollama serve

# Test with a simple prompt
ollama run llama3 "Hello"
```

### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use a different port
streamlit run app.py --server.port 8502
```

### Database Errors
```bash
# Remove the database file
rm travel.db

# Restart the app (it will recreate the database)
streamlit run app.py
```

### Slow Response Times
- Check Ollama is using GPU (if available)
- Reduce the number of days in the trip
- Use a smaller/faster model like `llama3:8b`

## 🔐 Security Considerations

⚠️ **Important**: This app has no built-in authentication!

For production use:
- Use HTTPS with SSL certificate
- Add authentication (Basic Auth, OAuth, etc.)
- Implement rate limiting
- Use environment variables for sensitive config
- Deploy behind a firewall or VPN

## 📝 Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Export to PDF/Calendar
- [ ] Integration with booking APIs
- [ ] Real-time pricing from hotels/flights
- [ ] Map visualization of itinerary
- [ ] Weather integration
- [ ] Multi-language support
- [ ] Image generation for destinations
- [ ] Share itineraries with friends

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available for personal and commercial use.

---

**Happy Travels! 🌍✈️🧳**
