# distraction-beaker-
# Productivity Chrome Extension with Flask Backend

This project is a browser productivity tracker and website blocker built using a Chrome extension and a Python Flask backend. It tracks time spent on websites, classifies it as productive or unproductive, and dynamically adjusts website blocking rules based on productivity levels.

---

## ✨ Features

* ⏰ Tracks active time spent on websites
* ✅ Logs productivity and timestamps per domain
* ⛔ Blocks distracting websites (e.g., YouTube, Reddit, Twitter)
* 🌟 Whitelist productive domains like `pw.live`
* ⚙ Flask server for managing logs and productivity logic
* 🔒 Local `log.json` stores time usage with productivity score
* ⚠️ Automatically disables blocking based on productivity goals

---

## 📖 How It Works

1. **Chrome Extension** tracks active tab URLs
2. It sends a POST request every minute to a local Flask server with:

   * domain
   * time spent
   * timestamp
3. The Flask server updates `log.json` and calculates productivity
4. Based on your productivity score, it decides whether to keep or lift website blocking rules

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/productivity-extension.git
cd productivity-extension
```

### 2. Install Python Requirements

Make sure Python 3 is installed.

```bash
pip install flask flask-cors
```

### 3. Run the Flask Server

```bash
python pyserver/main.py
```

This will start a server on `http://localhost:5000`

### 4. Load the Chrome Extension

1. Go to `chrome://extensions`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select the `extension/` directory

### 5. Start Using

* Visit `pw.live` or other productive sites
* Open YouTube, Reddit, etc. to test blocking
* Track your time and view `log.json` for logs

---

## 🔐 Advanced Security (Optional)

* Use `chattr +i log.json` to prevent tampering:

  ```bash
  sudo chattr +i log.json
  ```
* Disable `chrome://extensions` with kiosk mode or custom policies

---

## 🎓 Ideal Use Case

This tool is perfect for:

* Students studying online (e.g., PW\.Live users)
* Anyone looking to track web usage
* People trying to cut down time on distractions

---

## 📊 Output Example (log.json)

```json
{
  "productive": 3600,
  "unproductive": 1800,
  "domains": {
    "www.pw.live": 3600,
    "www.youtube.com": 1800
  },
  "history": {
    "www.pw.live": [
      {"timestamp": "2025-05-22T12:00:00", "seconds": 60},
      {"timestamp": "2025-05-22T12:01:00", "seconds": 60}
    ]
  }
}
```

---

##

---

## ✨ Contribute

Pull requests are welcome! For major changes, open an issue first to discuss what you would like to change.

---

## 😊 Created by \[Your Name] - Built for better focus and productivity!
