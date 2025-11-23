# Weibo Scraper

A Python-based Weibo scraper that uses Playwright to scrape posts from specific users with date range filtering.

## Features

- **Automated Login**: Browser-based login with state persistence
- **Date Range Filtering**: Scrape posts within specific date ranges
- **Content Extraction**: Extract full text content, including expanded text
- **Engagement Metrics**: Capture likes, comments, and reposts data
- **Markdown Export**: Save results in organized daily markdown files
- **Smart Pagination**: Handles infinite scroll and dynamic loading
- **Deduplication**: Prevents duplicate scraping of the same posts
- **Anti-Detection**: Human-like scrolling behavior and delays

## Installation

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser

### Setup

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### 1. First Login (One-time setup)

Run the login script to authenticate with Weibo:

```bash
python login.py
```

1. A browser window will automatically open to Weibo login page
2. Manually scan the QR code to login
3. The script will automatically save your login state to `state.json`

### 2. Configure Scraping

Edit the configuration section in `scraper.py`:

```python
TARGET_USER_ID = "1669879400"  # Target user's ID (from profile URL)
START_DATE = "2023-01-01"      # Start date (inclusive)
END_DATE = "2023-12-31"        # End date (inclusive)
```

### 3. Run the Scraper

```bash
python scraper.py
```

### 4. Results

Scraped data will be saved in the `output/` directory as markdown files organized by date (YYYY-MM-DD.md).

## Configuration Options

### Target User ID
Find the user ID from the Weibo profile URL:
- URL format: `https://weibo.com/u/{USER_ID}`
- Example: `https://weibo.com/u/1669879400` → User ID: `1669879400`

### Date Range
- Use ISO format: `YYYY-MM-DD`
- Both start and end dates are inclusive
- Timezone: Local system timezone

## File Structure

```
weibo-scraper/
├── login.py          # Login script with state persistence
├── scraper.py        # Main scraping script
├── utils.py          # Utility functions (time parsing, etc.)
├── requirements.txt  # Python dependencies
├── state.json        # Login state (auto-generated)
├── output/           # Scraped data output directory
│   └── YYYY-MM-DD.md # Daily markdown files
└── README.md         # Documentation
```

## Output Format

Each daily markdown file contains:

```markdown
# YYYY-MM-DD Weibo Archive

## HH:MM:SS

**Engagement:** {likes} likes · {comments} comments · {reposts} reposts

{Full post content}

---
```

## Technical Details

### Time Parsing
The scraper supports various Weibo time formats:
- "Just now" (刚刚)
- "X minutes ago" (X分钟前)
- "X hours ago" (X小时前)
- "Yesterday HH:MM" (昨天 HH:MM)
- "MM-DD HH:MM" (current year)
- "YYYY-MM-DD" (previous years)

### Anti-Detection Features
- Human-like scrolling with variable delays
- Random pause intervals
- Gradual scroll segments instead of instant jumps
- Detection of redirects to hot search page

### Error Handling
- Graceful handling of network timeouts
- Automatic retry for failed requests
- Detection of login state expiration
- Handling of page structure changes

## Limitations & Considerations

### Rate Limiting
- Built-in delays to avoid triggering Weibo's anti-bot measures
- For large scraping volumes, consider increasing delays or batch processing

### Page Structure Changes
- Weibo frequently updates their web interface
- CSS selectors may need updates if scraping fails
- Monitor for changes in article structure, time formats, etc.

### Login Requirements
- Requires periodic re-authentication
- Login state may expire after extended periods
- Use responsibly to avoid account restrictions

## Troubleshooting

### Login Issues
- Ensure QR code scanning is completed within 5 minutes
- Check if `state.json` was properly generated
- Try clearing browser cache and re-running login

### Scraping Failures
- Verify target user ID is correct
- Check date range format (YYYY-MM-DD)
- Ensure `state.json` exists and is valid
- Monitor console output for specific error messages

### Empty Results
- Verify target user has posts in the specified date range
- Check if user profile is public
- Ensure login state is still valid

## Legal & Ethical Considerations

- Use this tool responsibly and in compliance with Weibo's Terms of Service
- Respect rate limits and avoid aggressive scraping
- Only scrape publicly available content
- Consider the privacy and rights of content creators
- Use scraped data for legitimate research or personal purposes only

## Dependencies

- `playwright`: Browser automation
- `pandas`: Data processing
- `openpyxl`: Excel file support

## License

This project is for educational and research purposes. Please ensure compliance with relevant platform terms of service and local regulations.

## Contributing

Feel free to submit issues, feature requests, or improvements to handle Weibo's evolving interface.