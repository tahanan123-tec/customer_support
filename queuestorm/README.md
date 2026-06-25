# QueueStorm — bKash CRM Ticket Classifier

QueueStorm is a production-ready, asynchronous CRM ticket classification service designed for bKash digital mobile financial services in Bangladesh. It handles English, Bangla, and mixed language inputs to classify support requests, direct them to the appropriate department, verify safety filters, and maintain real-time telemetry metrics.

## Endpoints

| Method | Path | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Simple liveness and health status check. |
| `POST` | `/sort-ticket` | Classifies support tickets using fast path keyword check and LLM analysis. |
| `GET` | `/stats` | Fetches JSON-serializable in-memory system performance metrics. |
| `GET` | `/tickets` | Retrieves an audit log of the 50 most recently processed classification events. |

---

## Unique features

* **Bangla + English mixed message support**: Tailored to recognize and parse bKash client queries written in pure English, phonetic Bangla, native Bangla script, or a hybrid (mixed) format.
* **Rule-based fast path (no LLM for obvious cases)**: Instantly intercepts and classifies common request patterns (like credential leaks, wrong recipient transfers, and payment failures) before making LLM requests, saving API costs and latency.
* **OTP/PIN safety guard on every response**: A strict guardrail scanner that detects password, PIN, or OTP terms in output summaries and automatically replaces the content with a secure fraud review flag.
* **Live stats at GET /stats**: Thread-safe telemetry tracking total counts, case-type frequencies, severity allocations, and human review tags.
* **Audit log at GET /tickets**: A rolling log of the last 50 processed queries with full request-response details and ISO timestamps.

---

## Local setup

To run the application locally, follow these steps:

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone <repository-url>
   cd customer_support/queuestorm
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate

   # On Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the environment variables:**
   Create a `.env` file in the `queuestorm/` directory:
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. **Start the local development server:**
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

6. **Verify with a cURL test:**
   Submit a test request using cURL to classify a ticket:
   ```bash
   curl -X POST http://127.0.0.1:8000/sort-ticket \
     -H "Content-Type: application/json" \
     -d '{
       "ticket_id": "T-001",
       "channel": "app",
       "locale": "bn",
       "message": "ভাই ভুল নাম্বারে টাকা চলে গেছে উদ্ধার করে দেন"
     }'
   ```

---

## Deploy on Render

Follow these steps to deploy QueueStorm to Render:

1. **Create a new Web Service**:
   - Log into the [Render Dashboard](https://dashboard.render.com/) and click **New > Web Service**.
   - Connect your GitHub repository containing the project.

2. **Configure Service Details**:
   - **Name**: `queuestorm`
   - **Environment**: `Python`
   - **Root Directory**: `queuestorm` (if the FastAPI files are inside the `queuestorm` directory in your repo)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables**:
   Under the **Environment** tab, click **Add Environment Variable**:
   - **Key**: `ANTHROPIC_API_KEY`
   - **Value**: *Your Anthropic Claude API Key*

4. **Deploy**:
   - Click **Create Web Service** at the bottom of the page. Render will build and launch the service.

---

## LLM

QueueStorm leverages the **`claude-sonnet-4-6`** model via the official **Anthropic Python SDK** to classify complex or ambiguous user tickets. A system instruction enforces Bangladesh-specific bKash CRM domain logic, department alignment, and structural JSON parsing. 

For high-confidence cases matching predefined regex or substring rules, the **Rule-based fast path** completely skips the LLM request, reducing costs and providing sub-millisecond response latency.
