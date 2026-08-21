# Kuku TV Video Downloader (kukutv-dl)

A command-line tool to download full shows, episodes, and videos in high-definition from Kuku TV.

### Features
- **Full Video Support:** Downloads full-length video streams in high quality (up to 1080p resolution).
- **Metadata Tagging:** Automatically embeds show title, season number, author, and show cover artwork.
- **Subtitles:** Downloads and saves subtitles/SRT files if available.

---

### Prerequisites
1. **Python 3.8+**
2. **FFmpeg:** Required for merging video and audio streams. Ensure it is installed and added to your system PATH.

---

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Anonymous-Scorpion/kukutv-dl.git
   cd kukutv-dl
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### How to Authenticate (Cookies Setup)
Since premium video shows are protected server-side, you must supply your login session to download them:

1. Open your browser and log in to your premium account on **[kukutv.app](https://kukutv.app)**.
2. Press **F12** (or right-click -> inspect) to open Developer Tools.
3. Go to **Application** -> **Storage** -> **Cookies** (or inspect your browser cookies using a cookie manager extension).
4. Find the cookie named **`jwtToken`** and copy its value (it starts with `eyJhbGciOi...`).
5. Create a file named **`cookies.txt`** in the repository root directory.
6. Paste the token into `cookies.txt` using the Netscape format below:
   ```text
   .kukutv.app	FALSE	/	FALSE	0	jwtToken	YOUR_JWT_TOKEN_HERE
   ```
   *(Note: The script will automatically parse this token, apply it to authorization headers, and securely fetch the CloudFront video streams).*

---

### Usage

Run the downloader by passing the URL of the show you want to download:

```bash
python kuku.py "https://kukutv.app/watch/show-slug-name"
```

---

### Disclaimer
- This project is strictly for **educational purposes** only. 
- The author is not responsible for any misuse, copyright violations, or terms of service breaches. Use at your own discretion.
