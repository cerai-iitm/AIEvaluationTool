#!/usr/bin/env python3
"""
Standalone Lexical Diversity Test Script
Tests the lexical diversity metric with different parameters on responses.json
"""

import json
import asyncio
import time
from datetime import datetime
from googletrans import Translator
from lexical_diversity import lex_div as ld
from lexicalrichness import LexicalRichness
import pandas as pd
import logging
import sys

# Suppress all logging output
logging.basicConfig(level=logging.CRITICAL)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.getLogger().setLevel(logging.CRITICAL)

MATTR_WINDOW_SIZES = [10, 20, 25, 30, 50, 75, 100]

async def compute_all_metrics_verbose(responses):
    results = []
    translator = Translator()
    for i, response in enumerate(responses):
        row = {}
        try:
            response_language = await translator.detect(response)
            if response_language.lang != "en":
                response_translation = await translator.translate(response, dest='en')
                response_translation = response_translation.text
            else:
                response_translation = response
            flt = ld.flemmatize(response_translation)
            lex = LexicalRichness(response_translation)
            # Compute all MATTR and MSTTR window sizes
            for w in MATTR_WINDOW_SIZES:
                row[f'mattr_{w}'] = ld.mattr(flt, window_length=w)
                row[f'msttr_{w}'] = ld.msttr(flt,window_length=w)
            row['hdd'] = ld.hdd(flt)
            row['ttr'] = ld.ttr(flt)
            row['mtld']= ld.mtld(flt)
            row['response_start'] = ' '.join(response.split()[:10])
            # Print all scores for this response
            print(f"Response {i+1}:")
            for w in MATTR_WINDOW_SIZES:
                print(f"  MATTR (window={w}): {row[f'mattr_{w}']:.4f}")
            for w in MATTR_WINDOW_SIZES:
                print(f"  MSTTR (window={w}): {row[f'msttr_{w}']:.4f}")
            print(f"  HDD:  {row['hdd']:.4f}")
            print(f"  TTR:  {row['ttr']:.4f}")
            print(f"  Start: {row['response_start']}")
            print()
        except Exception as e:
            for w in MATTR_WINDOW_SIZES:
                row[f'mattr_{w}'] = 0.0
                row[f'msttr_{w}'] = 0.0
            row['hdd'] = 0.0
            row['ttr'] = 0.0
            row['response_start'] = 'ERROR: ' + str(e)
            print(f"Response {i+1}: ERROR - {str(e)}")
        results.append(row)
    return results

async def main():
    try:
        responses_file = "Data/responses.json"
        with open(responses_file, 'r', encoding='utf-8') as f:
            responses_data = json.load(f)
        test_responses = [item['response'] for item in responses_data if 'response' in item]
        if not test_responses:
            print("No valid responses found in the file!")
            return
        all_results = await compute_all_metrics_verbose(test_responses)
        df = pd.DataFrame(all_results)
        df.to_csv('prompt_all_scores.csv', index=False)
        print("All scores saved to prompt_all_scores.csv")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 