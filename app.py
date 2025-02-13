import gradio as gr
from researcher import async_main, read_readme  # Import async_main
import asyncio

print("app.py: Starting app...") # Log app start

async def run_research_ui(query, max_iterations):
    print(f"run_research_ui: started with query: '{query}', max_iterations: {max_iterations}") # Log UI function start
    try:
        max_iterations = int(max_iterations)
        if not query:
            yield "Please enter a research query.", ""
            print("run_research_ui: No query entered") # Log no query
            return

        # Use asyncio.gather to run the async generator
        final_report = ""
        status_updates = ""
        print("run_research_ui: Entering async_main loop...") # Log async_main loop start
        async for status, report_part in async_main(query, max_iterations):
            status_updates += status + "\n"
            if report_part:  # If there's a report part, update final_report
                final_report = report_part
            yield status_updates, final_report # Yield intermediate results
        print("run_research_ui: Async_main loop finished.") # Log async_main loop finish


    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        yield error_message, ""
        print(f"run_research_ui: Exception occurred: {e}") # Log exception
        return

    finally:
        print("run_research_ui: finished") # Log UI function finish


# Create the Gradio interface
iface = gr.Interface(
    fn=run_research_ui,
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter your research query...", label="Research Query"),
        gr.Slider(minimum=1, maximum=20, step=1, value=10, label="Maximum Iterations")
    ],
    outputs=[
        gr.Textbox(label="Status", interactive=False),  # Status output first
        gr.Textbox(lines=10, label="Final Report", interactive=False) # Then report
    ],
    title="Open Deep Researcher",
    description="Enter a research query and the maximum number of iterations to generate a comprehensive report.",
)

print("app.py: Gradio interface created.") # Log UI creation

# Add a button to display the README
with iface:
    readme_text = gr.Textbox(label="README.md", lines=10, interactive=False)
    readme_button = gr.Button("Show README")
    readme_button.click(read_readme, inputs=[], outputs=[readme_text])
    print("app.py: README button added.") # Log README button

print("app.py: Launching Gradio interface...") # Log UI launch
iface.launch()
print("app.py: Gradio interface launched.") # Log UI launched
