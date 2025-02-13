import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

# =======================
# Configuration Constants
# =======================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

# Endpoints
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SERPAPI_URL = "https://serpapi.com/search"
JINA_BASE_URL = "https://r.jina.ai/"

# Default LLM model (can be changed if desired)
DEFAULT_MODEL = "anthropic/claude-3.5-haiku"


# ============================
# Asynchronous Helper Functions
# ============================

async def call_openrouter_async(session, messages, model=DEFAULT_MODEL):
    """
    Asynchronously call the OpenRouter chat completion API with the provided messages.
    Returns the content of the assistant’s reply.
    """
    print("call_openrouter_async: started")  # Log start
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-Title": "OpenDeepResearcher, by Matt Shumer",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages
    }
    try:
        async with session.post(OPENROUTER_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                try:
                    print("call_openrouter_async: success response") # Log success
                    return result['choices'][0]['message']['content']
                except (KeyError, IndexError) as e:
                    print("call_openrouter_async: Unexpected OpenRouter response structure:", result)
                    return None
            else:
                text = await resp.text()
                print(f"call_openrouter_async: OpenRouter API error: {resp.status} - {text}")
                return None
    except Exception as e:
        print("call_openrouter_async: Error calling OpenRouter:", e)
        return None
    finally:
        print("call_openrouter_async: finished") # Log finish


async def generate_search_queries_async(session, user_query):
    print("generate_search_queries_async: started") # Log start
    prompt = (
        "You are an expert research assistant. Given the user's query, generate up to four distinct, "
        "precise search queries that would help gather comprehensive information on the topic. "
        "Return only a Python list of strings, for example: ['query1', 'query2', 'query3']."
    )
    messages = [
        {"role": "system", "content": "You are a helpful and precise research assistant."},
        {"role": "user", "content": f"User Query: {user_query}\n\n{prompt}"}
    ]
    response = await call_openrouter_async(session, messages)
    if response:
        try:
            search_queries = eval(response)
            if isinstance(search_queries, list):
                print(f"generate_search_queries_async: generated queries: {search_queries}") # Log queries
                return search_queries
            else:
                print("generate_search_queries_async: LLM did not return a list. Response:", response)
                return []
        except Exception as e:
            print("generate_search_queries_async: Error parsing search queries:", e, "\nResponse:", response)
            return []
    print("generate_search_queries_async: No response or error, returning empty list") # Log no response
    return []
    finally:
        print("generate_search_queries_async: finished") # Log finish


async def perform_search_async(session, query):
    print(f"perform_search_async: started for query: {query}") # Log start
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google"
    }
    try:
        async with session.get(SERPAPI_URL, params=params) as resp:
            if resp.status == 200:
                results = await resp.json()
                if "organic_results" in results:
                    links = [item.get("link") for item in results["organic_results"] if "link" in item]
                    print(f"perform_search_async: found links: {links}") # Log links
                    return links
                else:
                    print("perform_search_async: No organic results in SERPAPI response.")
                    return []
            else:
                text = await resp.text()
                print(f"perform_search_async: SERPAPI error: {resp.status} - {text}")
                return []
    except Exception as e:
        print("perform_search_async: Error performing SERPAPI search:", e)
        return []
    finally:
        print(f"perform_search_async: finished for query: {query}") # Log finish


async def fetch_webpage_text_async(session, url):
    print(f"fetch_webpage_text_async: started for url: {url}") # Log start
    full_url = f"{JINA_BASE_URL}{url}"
    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}"
    }
    try:
        async with session.get(full_url, headers=headers) as resp:
            if resp.status == 200:
                print(f"fetch_webpage_text_async: successfully fetched for url: {url}") # Log success
                return await resp.text()
            else:
                text = await resp.text()
                print(f"fetch_webpage_text_async: Jina fetch error for {url}: {resp.status} - {text}")
                return ""
    except Exception as e:
        print(f"fetch_webpage_text_async: Error fetching webpage text with Jina for url: {url}", e)
        return ""
    finally:
        print(f"fetch_webpage_text_async: finished for url: {url}") # Log finish


async def is_page_useful_async(session, user_query, page_text):
    print("is_page_useful_async: started") # Log start
    prompt = (
        "You are a critical research evaluator. Given the user's query and the content of a webpage, "
        "determine if the webpage contains information relevant and useful for addressing the query. "
        "Respond with exactly one word: 'Yes' if the page is useful, or 'No' if it is not. Do not include any extra text."
    )
    messages = [
        {"role": "system", "content": "You are a strict and concise evaluator of research relevance."},
        {"role": "user", "content": f"User Query: {user_query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
    ]
    response = await call_openrouter_async(session, messages)
    if response:
        answer = response.strip()
        if answer in ["Yes", "No"]:
            print(f"is_page_useful_async: LLM judged page as: {answer}") # Log judgment
            return answer
        else:
            if "Yes" in answer:
                print("is_page_useful_async: LLM judged page as: Yes (fallback)") # Log fallback yes
                return "Yes"
            elif "No" in answer:
                print("is_page_useful_async: LLM judged page as: No (fallback)") # Log fallback no
                return "No"
    print("is_page_useful_async: No valid response from LLM, defaulting to No") # Log no response
    return "No"
    finally:
        print("is_page_useful_async: finished") # Log finish


async def extract_relevant_context_async(session, user_query, search_query, page_text):
    print("extract_relevant_context_async: started") # Log start
    prompt = (
        "You are an expert information extractor. Given the user's query, the search query that led to this page, "
        "and the webpage content, extract all pieces of information that are relevant to answering the user's query. "
        "Return only the relevant context as plain text without commentary."
    )
    messages = [
        {"role": "system", "content": "You are an expert in extracting and summarizing relevant information."},
        {"role": "user", "content": f"User Query: {user_query}\nSearch Query: {search_query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
    ]
    response = await call_openrouter_async(session, messages)
    if response:
        context = response.strip()
        print(f"extract_relevant_context_async: extracted context (first 200 chars): {context[:200]}") # Log context
        return context
    print("extract_relevant_context_async: No context extracted") # Log no context
    return ""
    finally:
        print("extract_relevant_context_async: finished") # Log finish


async def get_new_search_queries_async(session, user_query, previous_search_queries, all_contexts):
    print("get_new_search_queries_async: started") # Log start
    context_combined = "\n".join(all_contexts)
    prompt = (
        "You are an analytical research assistant. Based on the original query, the search queries performed so far, "
        "and the extracted contexts from webpages, determine if further research is needed. "
        "If further research is needed, provide up to four new search queries as a Python list (for example, "
        "['new query1', 'new query2']). If you believe no further research is needed, respond with exactly <done>.\n"
        "Output only a Python list or the token <done> without any additional text."
    )
    messages = [
        {"role": "system", "content": "You are a systematic research planner."},
        {"role": "user", "content": f"User Query: {user_query}\nPrevious Search Queries: {previous_search_queries}\n\nExtracted Relevant Contexts:\n{context_combined}\n\n{prompt}"}
    ]
    response = await call_openrouter_async(session, messages)
    if response:
        cleaned = response.strip()
        if cleaned == "<done>":
            print("get_new_search_queries_async: LLM responded with <done>") # Log done
            return "<done>"
        try:
            new_queries = eval(cleaned)
            if isinstance(new_queries, list):
                print(f"get_new_search_queries_async: LLM provided new queries: {new_queries}") # Log new queries
                return new_queries
            else:
                print("get_new_search_queries_async: LLM did not return a list for new search queries. Response:", response)
                return []
        except Exception as e:
            print("get_new_search_queries_async: Error parsing new search queries:", e, "\nResponse:", response)
            return []
    print("get_new_search_queries_async: No response or error, returning empty list") # Log no response
    return []
    finally:
        print("get_new_search_queries_async: finished") # Log finish


async def generate_final_report_async(session, user_query, all_contexts):
    print("generate_final_report_async: started") # Log start
    context_combined = "\n".join(all_contexts)
    prompt = (
        "You are an expert researcher and report writer. Based on the gathered contexts below and the original query, "
        "write a comprehensive, well-structured, and detailed report that addresses the query thoroughly. "
        "Include all relevant insights and conclusions without extraneous commentary."
    )
    messages = [
        {"role": "system", "content": "You are a skilled report writer."},
        {"role": "user", "content": f"User Query: {user_query}\n\nGathered Relevant Contexts:\n{context_combined}\n\n{prompt}"}
    ]
    report = await call_openrouter_async(session, messages)
    if report:
        print("generate_final_report_async: report generated (first 200 chars):", report[:200]) # Log report start
        return report
    else:
        print("generate_final_report_async: Failed to generate report") # Log report failure
        return "Could not generate a final report."
    finally:
        print("generate_final_report_async: finished") # Log finish


async def process_link(session, link, user_query, search_query):
    print(f"process_link: started for link: {link}") # Log start
    page_text = await fetch_webpage_text_async(session, link)
    if not page_text:
        print(f"process_link: No page text fetched for link: {link}") # Log no page text
        return None
    usefulness = await is_page_useful_async(session, user_query, page_text)
    print(f"process_link: Page usefulness for {link}: {usefulness}") # Log usefulness
    if usefulness == "Yes":
        context = await extract_relevant_context_async(session, user_query, search_query, page_text)
        if context:
            print(f"process_link: Extracted context from {link} (first 200 chars): {context[:200]}") # Log extracted context
            return context
    print(f"process_link: No useful context from link: {link}") # Log no useful context
    return None
    finally:
        print(f"process_link: finished for link: {link}") # Log finish


# =========================
# Main Asynchronous Routine
# =========================
# Modified to yield status updates

async def async_main(user_query, iteration_limit):
    print("async_main: started") # Log main start
    aggregated_contexts = []
    all_search_queries = []
    iteration = 0

    async with aiohttp.ClientSession() as session:
        yield "Generating initial search queries...", ""  # Initial status update
        print("async_main: Generating initial search queries...") # Log status

        new_search_queries = await generate_search_queries_async(session, user_query)
        if not new_search_queries:
            yield "No search queries were generated by the LLM. Exiting.", ""
            print("async_main: No initial search queries generated, exiting") # Log no initial queries
            return

        all_search_queries.extend(new_search_queries)
        yield f"Initial search queries: {new_search_queries}", ""
        print(f"async_main: Initial search queries: {new_search_queries}") # Log initial queries

        while iteration < iteration_limit:
            yield f"Iteration {iteration + 1}: Starting...", ""
            print(f"async_main: Iteration {iteration + 1}: Starting...") # Log iteration start
            iteration_contexts = []

            search_tasks = [perform_search_async(session, query) for query in new_search_queries]
            search_results = await asyncio.gather(*search_tasks)

            unique_links = {}
            for idx, links in enumerate(search_results):
                query_used = new_search_queries[idx]
                for link in links:
                    if link not in unique_links:
                        unique_links[link] = query_used

            yield f"Iteration {iteration + 1}: Found {len(unique_links)} unique links.", ""
            print(f"async_main: Iteration {iteration + 1}: Found {len(unique_links)} unique links.") # Log unique links count

            link_tasks = [
                process_link(session, link, user_query, unique_links[link])
                for link in unique_links
            ]
            link_results = await asyncio.gather(*link_tasks)

            for res in link_results:
                if res:
                    iteration_contexts.append(res)

            if iteration_contexts:
                aggregated_contexts.extend(iteration_contexts)
                yield f"Iteration {iteration + 1}: Found {len(iteration_contexts)} useful contexts.", ""
                print(f"async_main: Iteration {iteration + 1}: Found {len(iteration_contexts)} useful contexts.") # Log useful contexts count
            else:
                yield f"Iteration {iteration + 1}: No useful contexts found.", ""
                print(f"async_main: Iteration {iteration + 1}: No useful contexts found.") # Log no useful contexts

            new_search_queries = await get_new_search_queries_async(session, user_query, all_search_queries, aggregated_contexts)

            if new_search_queries == "<done>":
                yield "LLM indicated that no further research is needed.", ""
                print("async_main: LLM indicated research is done") # Log research done
                break
            elif new_search_queries:
                yield f"LLM provided new search queries: {new_search_queries}", ""
                print(f"async_main: LLM provided new queries: {new_search_queries}") # Log new queries
                all_search_queries.extend(new_search_queries)
            else:
                yield "LLM did not provide any new search queries. Ending the loop.", ""
                print("async_main: LLM provided no new queries, ending loop") # Log no new queries, loop end
                break

            iteration += 1

        yield "Generating final report...", ""
        print("async_main: Generating final report...") # Log report generation

        final_report = await generate_final_report_async(session, user_query, aggregated_contexts)
        if final_report:
            yield "Research completed successfully.", final_report
            print("async_main: Research completed successfully") # Log research success
        else:
            yield "Could not generate a final report.", ""
            print("async_main: Could not generate final report") # Log report generation failure
    finally:
        print("async_main: finished") # Log main finish


def read_readme():
    try:
        with open("README.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "README.md not found."
