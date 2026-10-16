# Crop Disease Recognition

Every season, a farmer notices spots on a leaf and wonders: is this something, or nothing? Asking an expert every time is slow and expensive. This is the app that takes the first look.

It's a small website with one job. You open it, upload a clear photo of a crop leaf, and it writes back a short, careful summary — what crop it thinks it sees, what symptoms are actually visible, how confident it is, and what you might do next. The way a cautious friend would, not the way a confident salesman would.

Nobody has to squint at a leaf alone anymore for the first check.

## Why it's built this way

It never pretends to be sure when it isn't. If the photo is blurry, dark, or not a crop at all, it says "Uncertain" or "Unknown" instead of inventing a disease. It describes what it can see and keeps guesses clearly labeled as guesses.

It never plays doctor with chemicals. It won't recommend a specific pesticide or dosage off one photo. It sticks to general, practical next steps — like checking other leaves or asking a local extension officer — and always lists its own limitations.

Nothing about you is kept. There are no accounts, no history, no database. You upload a photo, you get an answer, and the app forgets you were there. Each visit starts fresh.

## What's in the box

File | What it does
--- | ---
`app/main.py` | The front door — serves the homepage and wires everything together
`app/routes/analysis.py` | The intake desk — takes your photo, checks it, asks the AI, returns the answer
`app/services/image_service.py` | The bouncer — rejects empty, oversized, or unreadable files before they go further
`app/services/Gen_service.py` | The phone call — sends the photo to Gemini and makes sure the reply is valid
`app/services/assessment_schema.py` | The rulebook — the exact shape every answer must follow, no exceptions
`templates/index.html` | The page you see
`static/css/style.css`, `static/js/app.js` | How it looks and the upload/validation in your browser
`tests/test_analysis.py` | The rehearsal — four fake runs so we know the plumbing works without calling the real AI
`images/` | A couple of sample leaves to try

## Want to run your own?

You'll need Python and a free Google Gemini API key.

Get the code and install what it needs:

```bash
python3 -m venv vene
source vene/bin/activate
python -m pip install -r requirements.txt
python -m pip install httpx
```

Tell it your key (the app reads this from a `.env` file it never commits):

```bash
GEMINI_API_KEY=your_key_here
```

Start it:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`, pick a clear leaf photo (JPEG, PNG, or WebP, under about 5 MB), and hit Analyze Image.

Prefer the shortcut? `python -m pytest -q` runs the four rehearsal tests — they use a fake answer, so they pass even without an api token
