import time

import requests
import streamlit as st

# === Configuration ===
API_URL = "http://127.0.0.1:8000/api/v1/analyze"
POLL_INTERVAL_SECONDS = 5
MAX_POLL_SECONDS = 900

# === Page Setup ===
st.set_page_config(
    page_title="AI Financial Analyst Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === Custom CSS for polish ===
st.markdown(
    """
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    h1 {
        color: #0066cc;
    }
</style>
""",
    unsafe_allow_html=True,
)

# === Main Header ===
st.title("🤖 AI Agent Financial Analyst")
st.markdown(
    """
    Welcome! This tool leverages a **multi-agent AI team** (powered by CrewAI) to perform
    comprehensive financial research on a given stock ticker.

    The frontend now submits a durable job to the backend and polls for completion while
    a separate worker executes the long-running analysis pipeline.
    """
)
st.divider()

# === Sidebar: Input & Controls ===
with st.sidebar:
    st.header("⚙️ Control Panel")

    ticker_input = st.text_input(
        "Enter Stock Ticker Symbol",
        value="",
        placeholder="e.g., NVDA, MSFT, TSLA",
        max_chars=5,
        help="Enter the standard ticker symbol for the company you want to analyze.",
    ).upper().strip()

    run_button = st.button("🚀 Queue Analysis Job", type="primary")

    st.markdown("---")
    st.info(
        "**Note:** The API now returns immediately with a job id. The UI polls the job"
        " status while a separate worker processes the analysis."
    )


def submit_analysis_job(ticker: str) -> dict:
    response = requests.post(API_URL, json={"ticker": ticker}, timeout=30)
    if response.status_code != 202:
        try:
            error_detail = response.json().get("detail", response.text)
        except Exception:
            error_detail = response.text
        raise RuntimeError(f"Failed to queue analysis job: {error_detail}")
    return response.json()


def fetch_job_status(job_id: str) -> dict:
    response = requests.get(f"{API_URL}/{job_id}", timeout=30)
    if response.status_code != 200:
        try:
            error_detail = response.json().get("detail", response.text)
        except Exception:
            error_detail = response.text
        raise RuntimeError(f"Failed to fetch job status: {error_detail}")
    return response.json()


# === Main App Logic ===
if run_button:
    if not ticker_input:
        st.error("⚠️ Please enter a ticker symbol before running the analysis.")
    else:
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_job", None)

        status_placeholder = st.empty()
        start_time = time.time()

        with st.spinner(f"🧠 Queueing analysis for '{ticker_input}'..."):
            try:
                job = submit_analysis_job(ticker_input)
                st.session_state["analysis_job"] = job
                status_placeholder.info(
                    f"Queued job `{job['job_id']}` for {ticker_input}. Waiting for worker..."
                )

                while True:
                    status_data = fetch_job_status(job["job_id"])
                    st.session_state["analysis_job"] = status_data
                    current_status = status_data["status"].lower()

                    if current_status == "queued":
                        status_placeholder.info(
                            f"Job `{job['job_id']}` is queued. Waiting for a worker to claim it..."
                        )
                    elif current_status == "running":
                        status_placeholder.info(
                            f"Job `{job['job_id']}` is running. The worker is building the report..."
                        )
                    elif current_status == "completed":
                        st.session_state["analysis_result"] = status_data
                        status_placeholder.success(
                            f"✅ Analysis job `{job['job_id']}` for {ticker_input} completed."
                        )
                        break
                    elif current_status == "failed":
                        status_placeholder.error(
                            "❌ Analysis failed: "
                            f"{status_data.get('error_message', 'Unknown error')}"
                        )
                        break
                    else:
                        status_placeholder.warning(
                            f"Job `{job['job_id']}` returned unexpected status '{current_status}'."
                        )

                    if time.time() - start_time > MAX_POLL_SECONDS:
                        status_placeholder.error(
                            "⏰ Timed out while waiting for the analysis job to finish."
                        )
                        break

                    time.sleep(POLL_INTERVAL_SECONDS)

            except requests.exceptions.ConnectionError:
                st.error("🚨 **Connection Error:** Could not connect to the backend API.")
                st.warning("Is the FastAPI server running?")
            except requests.exceptions.Timeout:
                st.error("⏰ **Timeout Error:** The backend request timed out.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


if "analysis_result" in st.session_state:
    data = st.session_state["analysis_result"]
    ticker_name = data.get("ticker", ticker_input)

    tab1, tab2 = st.tabs(["📄 Final Investment Report", "🔍 Job Metadata"])

    with tab1:
        st.subheader(f"Investment Analysis: {ticker_name}")
        report_content = data.get("report_content") or "*No report content found.*"
        st.markdown(report_content)

        st.divider()
        st.download_button(
            label="📥 Download Report as Markdown",
            data=report_content,
            file_name=f"{ticker_name}_Investment_Report.md",
            mime="text/markdown",
        )

    with tab2:
        st.subheader("Backend Job Details")
        st.markdown(f"**Job ID:** `{data.get('job_id')}`")
        st.markdown(f"**Status:** {data.get('status')}")
        st.markdown(f"**Worker ID:** `{data.get('worker_id')}`")
        st.markdown(f"**Created At:** `{data.get('created_at')}`")
        st.markdown(f"**Started At:** `{data.get('started_at')}`")
        st.markdown(f"**Completed At:** `{data.get('completed_at')}`")

        report_url = data.get("report_url")
        if report_url:
            st.markdown(f"**Azure Blob Storage URL:** [Link to File]({report_url})")

        error_message = data.get("error_message")
        if error_message:
            st.error(error_message)

        with st.expander("See Raw Job Response (JSON)"):
            st.json(data)
