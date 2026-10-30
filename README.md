# RegainTravel AI — Prototype Review

RegainTravel AI is a local Windows travel enquiry research and management prototype, intended for a commercial travel advisory workflow.

## Included prototypes
- `version-3/index.html`: browser-only TravelFinder with external Google searches, manually pasted public post text, offline keyword-based relevance scoring and browser-local saved enquiries. Open directly in a browser.
- `international-finder/app.py`: separate Python standard-library local server with public search links, manual lead entry, recruitment and holiday customer pipelines, CSV export and indicative country checks. Run `START_WINDOWS.bat` on Windows with Python 3 installed.

**These are separate prototypes, not one integrated application.** Neither retrieves Reddit posts via an API, scrapes Reddit, automatically messages users, or runs a hosted AI model. The proposed Reddit API integration is **not implemented** and is subject to Reddit's approval and terms.

## Privacy and security
The Python server binds to 127.0.0.1 and stores entered lead information in a local SQLite database (`regaintravel.db`). The HTML version stores entries in the browser's local storage. Do not upload databases, exported lead CSVs, credentials, customer information, or personal notes to GitHub.

## Reddit API access request
Requested use: subject to Reddit's explicit commercial API approval, review permitted public travel discussions and present relevant public links in a private dashboard for human review. Commercial lead discovery is part of the proposed use. No automated unsolicited messages or posts are planned.

## Project status
Early-stage prototype. No Reddit access has been granted or integrated. No affiliation with or endorsement by Reddit, InteleTravel, or PlanNet Marketing is implied.
