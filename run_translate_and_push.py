"""
Test script: Load papers from papers.json -> Translate abstracts -> Push to Lark
"""

import os
import json
from utils import load_config
from arxiv_paper import translate_abstracts
from lark_post import post_to_lark_webhook


def main():
    config = load_config()
    paper_file = os.path.join(os.path.dirname(__file__), 'papers.json')

    with open(paper_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    print('Loaded {} papers from papers.json'.format(len(papers)))

    if config.get('use_llm_for_translation', False):
        papers = translate_abstracts(papers, config)
        print('Translated Abstracts into Chinese')
    else:
        print('Translation disabled, skipping.')

    post_to_lark_webhook(config['tag'], papers, config)


if __name__ == '__main__':
    main()
