# OpenDeepResearcher

This notebook implements an **AI researcher** that continuously searches for information based on a user query until the system is confident that it has gathered all the necessary details. It makes use of several services to do so:

- **Google Custom Search API**: To perform Google searches (100 free queries per day).
- **Jina**: To fetch and extract webpage content.
- **OpenRouter** (default model: `anthropic/claude-3.5-haiku`): To interact with a LLM for generating search queries, evaluating page relevance, and extracting context.

## Features

- **Iterative Research Loop:** The system refines its search queries iteratively until no further queries are required.
- **Asynchronous Processing:** Searches, webpage fetching, evaluation, and context extraction are performed concurrently to improve speed.
- **Duplicate Filtering:** Aggregates and deduplicates links within each round, ensuring that the same link isn't processed twice.
- **LLM-Powered Decision Making:** Uses the LLM to generate new search queries, decide on page usefulness, extract relevant context, and produce a final comprehensive report.
- **Gradio Interface:** Use the `open-deep-researcher - gradio` notebook if you want to use this in a functional UI

## Requirements

- API access and keys for:
  - **OpenRouter API**
  - **Google Custom Search API** and Custom Search Engine ID
  - **Jina API**

## Setup

1. **Clone or Open the Notebook:**
   - Download the notebook file or open it directly in [Google Colab](https://colab.research.google.com/github/mshumer/OpenDeepResearcher/blob/main/open_deep_researcher.ipynb).

2. **Install `nest_asyncio`:**

   Run the first cell to set up `nest_asyncio`.

3. **Configure API Keys:**
   - Replace the placeholder values in the notebook for:
     - `OPENROUTER_API_KEY`
     - `GOOGLE_CSE_API_KEY` (Google Custom Search API key)
     - `GOOGLE_CSE_ID` (Google Custom Search Engine ID)
     - `JINA_API_KEY`

## Usage

1. **Run the Notebook Cells:**
   Execute all cells in order. The notebook will prompt you for:
   - A research query/topic.
   - An optional maximum number of iterations (default is 10).

2. **Follow the Research Process:**
   - **Initial Query & Search Generation:** The notebook uses the LLM to generate initial search queries.
   - **Asynchronous Searches & Extraction:** It performs SERPAPI searches for all queries concurrently, aggregates unique links, and processes each link in parallel to determine page usefulness and extract relevant context.
   - **Iterative Refinement:** After each round, the aggregated context is analyzed by the LLM to determine if further search queries are needed.
   - **Final Report:** Once the LLM indicates that no further research is needed (or the iteration limit is reached), a final report is generated based on all gathered context.

3. **View the Final Report:**
   The final comprehensive report will be printed in the output.

## How It Works

1. **Input & Query Generation:**  
   The user enters a research topic, and the LLM generates up to four distinct search queries.

2. **Concurrent Search & Processing:**  
   - **SERPAPI:** Each search query is sent to SERPAPI concurrently.
   - **Deduplication:** All retrieved links are aggregated and deduplicated within the current iteration.
   - **Jina & LLM:** Each unique link is processed concurrently to fetch webpage content via Jina, evaluate its usefulness with the LLM, and extract relevant information if the page is deemed useful.

3. **Iterative Refinement:**  
   The system passes the aggregated context to the LLM to determine if further search queries are needed. New queries are generated if required; otherwise, the loop terminates.

4. **Final Report Generation:**  
   All gathered context is compiled and sent to the LLM to produce a final, comprehensive report addressing the original query.

## Troubleshooting

- **RuntimeError with asyncio:**  
  If you encounter an error like:
  ```
  RuntimeError: asyncio.run() cannot be called from a running event loop
  ```
  Ensure you have applied `nest_asyncio` as shown in the setup section.

- **API Issues:**  
  Verify that your API keys are correct and that you are not exceeding any rate limits.

## Running in Production with tmux

To run the app persistently in a production environment using tmux:

1. **Attach to tmux session:**
   ```bash
   tmux attach -t bots_session
   ```
   If the session doesn't exist, create it with:
   ```bash
   tmux new-session -s bots_session
   ```

2. **Create a new window for the app:**
   ```bash
   tmux new-window -t bots_session:18 -n "deep-research" "cd ~/Projects/web/deep-research && python3 app.py"
   ```
   This creates a new window named "deep-research" and starts the app.

3. **Managing the app:**
   - View all windows: Press `Ctrl+b` then `w`
   - Switch to window: Click on window number or use `Ctrl+b` then window number
   - Stop the app: Switch to its window, press `Ctrl+C`
   - Close window: After stopping the app, type `exit` or press `Ctrl+b` then `&`
   - Detach from tmux: Press `Ctrl+b` then `d`

4. **Accessing the app:**
   - Local URL: http://0.0.0.0:7860
   - Remote URL: http://your-server-ip:7860

Note: If port 7860 is already in use, either free the port by stopping the existing process or use a different port by modifying the `server_port` parameter in `app.py`.

---

Follow me on [X](https://x.com/mattshumer_) for updates on this and other AI things I'm working on.

OpenDeepResearcher is released under the MIT License. See the LICENSE file for more details.
