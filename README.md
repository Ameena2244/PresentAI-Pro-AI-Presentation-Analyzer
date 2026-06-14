SCREENSHOT
<img width="1366" height="720" alt="Screenshot 2026-06-14 210553" src="https://github.com/user-attachments/assets/628d037f-68d4-481b-b9b4-0ed69338d230" />
<img width="1366" height="720" alt="Screenshot 2026-06-14 210625" src="https://github.com/user-attachments/assets/bff43fac-5beb-49dd-a195-24310454607c" />
<img width="1366" height="720" alt="Screenshot 2026-06-14 210639" src="https://github.com/user-attachments/assets/7b4520d3-6d0e-4164-b086-147dbd08a9e3" />
<img width="1366" height="720" alt="Screenshot 2026-06-14 210712" src="https://github.com/user-attachments/assets/4ba8cbcf-bd9b-4f81-8d64-7b82085f4049" />
<img width="1152" height="270" alt="Screenshot 2026-06-14 210818" src="https://github.com/user-attachments/assets/503a62a1-fcca-400d-ae5a-d7a743d10e9e" />
<img width="1366" height="720" alt="Screenshot 2026-06-14 210731" src="https://github.com/user-attachments/assets/4de399e6-6254-4304-a123-b8425c07e6ca" />


# PresentAI Pro

A full Flask-based AI presentation analyzer with real file upload, text extraction, Gemini integration, and fallback analysis.

## Folder structure

```
MICROSOFT HACKATHON/
└── project/
    ├── app.py
    ├── requirements.txt
    ├── templates/
    │   └── index.html
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── main.js
    ├── utils/
    │   ├── docx_parser.py
    │   ├── gemini_analyzer.py
    │   ├── pdf_parser.py
    │   └── report_generator.py
    └── static/uploads/
```

## How to run

1. Open PowerShell.
2. Navigate to the project folder:

```powershell
cd "c:\Users\ELCOT\OneDrive\Desktop\MICROSOFT HACKATHON\project"
```

3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Start the app:

```powershell
python app.py
```

6. Open your browser:

```text
http://127.0.0.1:5000/
```

## Optional Gemini API

To enable real Gemini-powered analysis, set the following before running:

```powershell
set GEMINI_API_URL=https://YOUR_GEMINI_ENDPOINT
set GEMINI_API_KEY=YOUR_API_KEY
set GEMINI_MODEL=your-model-name
```

If these are not set, the app still works via a local fallback analyzer.

## What works

- Upload PDF, DOCX, TXT
- Extract text from uploaded files
- Analyze presentation content
- Render charts with actual output
- Download report as PDF or DOCX

## Notes

- Only one README is maintained at the workspace root.
- The app backend is `project/app.py`.
- The frontend is served from `project/templates/index.html`.
