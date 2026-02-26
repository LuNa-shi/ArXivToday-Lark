# Main Process Documentation

This document explains the core runtime flow of the project, centered on `main.py`.

## 1) Entry Point

- Script entry: `python main.py`
- `main.py` loads configuration from `config.yaml` via `utils.load_config()`.
- If `use_llm_for_filtering` is enabled, it also loads the prompt from `paper_to_hunt.md`.

## 2) Main Pipeline (`task()`)

The `task()` function performs the full pipeline in this order:

1. Build today date and print task header.
2. Fetch latest papers per configured arXiv category.
3. Deduplicate papers across categories.
4. Apply keyword filtering (if `keyword_list` is non-empty).
5. Apply LLM filtering (if `use_llm_for_filtering: true`).
6. Deduplicate against history in `papers.json`.
7. Translate abstracts with LLM (if `use_llm_for_translation: true`).
8. Prepend new papers to `papers.json`.
9. Post result to Lark webhook using interactive card template.

## 3) Detailed Module Responsibilities

### `arxiv_paper.py`

- `get_latest_papers(category, max_results=100)`
  - Queries arXiv by category (`cat:<category>`), sorted by submitted date.
  - Normalizes each paper to:
    - `title`
    - `id` (version suffix like `v2` removed)
    - `abstract`
    - `url`
    - `published` (ISO date)
- `deduplicate_papers_across_categories(papers)`
  - Removes duplicates by `id` while keeping original order.
- `filter_papers_by_keyword(papers, keyword_list)`
  - Lowercase word-level intersection between abstract tokens and keyword list.
- `filter_papers_using_llm(papers, paper_to_hunt, config)`
  - Calls LLM classifier per paper through `llm.is_paper_match(...)`.
- `deduplicate_papers(papers, file_path)`
  - Removes papers whose IDs already exist in historical `papers.json`.
- `translate_abstracts(papers, config)`
  - Calls LLM translator per paper and stores result in `zh_abstract`.
- `prepend_to_json_file(file_path, data)`
  - Writes `data + old_content` to keep newest results at the top.

### `llm.py`

- `is_paper_match(...)`
  - Sends paper title + abstract and `paper_to_hunt` to LLM.
  - Returns `True` if response contains `"yes"` (case-insensitive).
  - If LLM request fails, it defaults to `True` (fail-open behavior).
- `translate_abstract(...)`
  - Sends translation prompt to LLM and returns translated text or `None`.
- Both methods remove optional `<think>...</think>` segments if present.

### `utils.py`

- `load_config()`: loads `config.yaml`.
- `validate_llm_server_config(config)`: validates `model`, `base_url`, `api_key`.
- `get_llm_response(prompt, config)`: sends OpenAI-compatible chat completion request.

### `lark_post.py`

- `post_to_lark_webhook(tag, papers, config)`
  - Builds template variables (`today_date`, `tag`, `table_rows`, `paper_list`).
  - Sends interactive card payload to `webhook_url`.

## 4) Input / Output Files

### Inputs

- `config.yaml`: runtime configuration.
- `paper_to_hunt.md`: LLM filtering description prompt (only when enabled).

### Outputs

- `papers.json`:
  - Stores historical papers.
  - Updated each run by prepending newly selected papers.

## 5) Key Configuration Switches

- `category_list`: arXiv categories to fetch.
- `keyword_list`: keyword filter list (empty list disables keyword filtering).
- `use_llm_for_filtering`: enable semantic filtering with LLM.
- `use_llm_for_translation`: enable abstract translation.
- `model`, `base_url`, `api_key`: OpenAI SDK-compatible LLM endpoint settings.
- `webhook_url`, `template_id`, `template_version_name`: Lark delivery settings.

## 6) Behavioral Notes

- A paper can appear in multiple categories; cross-category dedup handles this.
- Historical dedup prevents repeated notifications across runs.
- If LLM filtering request fails for a paper, that paper is kept (fail-open).
- Translation is optional and only affects `zh_abstract` field.
- If no papers remain after filtering, the system still posts with `total_paper = 0`.

## 7) Minimal Runtime Sequence Diagram (Conceptual)

1. `main.py` -> load config/prompt.
2. `main.py` -> `arxiv_paper.get_latest_papers()` for each category.
3. `main.py` -> dedup + filter (keyword / LLM).
4. `main.py` -> dedup against `papers.json`.
5. `main.py` -> optional translation.
6. `main.py` -> write `papers.json`.
7. `main.py` -> `lark_post.post_to_lark_webhook()` to push card.

