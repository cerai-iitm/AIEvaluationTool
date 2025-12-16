#!/usr/bin/env python3
#@author Sudarsun S
#@date 24/10/2025
# Helper script to fix the language field of the prompts and responses in the database.

import argparse
import sys
import os
import json
from rich.table import Table
from rich.console import Console

sys.path.append(os.path.dirname(__file__) + "/../../")  # Adjust the path to include the "lib" directory

from lib.orm import DB  # Import the DB class from the ORM module
from lib.data import Target, Run, RunDetail, Conversation
from lib.utils import get_logger, get_logger_verbosity, lang_detect, iso639_to_language_name, language_name_to_iso639

def main():
    parser = argparse.ArgumentParser(description="Fix language fields in prompts and responses.")
    parser.add_argument("--config", "-c", dest="config", required=True, type=str, help="Path to the configuration file containing database connection and target application details.")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, choices=[0,1,2,3,4,5], help="Enable verbose output", default=5)
    parser.add_argument("--stats", "-s", dest="stats", action="store_true", help="Show statistics of language distribution.")
    parser.add_argument("--force", "-f", dest="force", action="store_true", help="Force update the language fields even if they are already set.")
    args = parser.parse_args()

    # Set up logging
    logger = get_logger(__name__)

    # Set the logging level based on the verbosity argument
    loglevel = get_logger_verbosity(args.verbosity)
    logger.setLevel(loglevel)

    # Load configuration from the specified file if provided
    if args.config:
        if not os.path.exists(args.config):
            logger.error(f"Configuration file '{args.config}' does not exist.")
            return
        with open(args.config, 'r') as config_file:
            try:
                config = json.load(config_file)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing configuration file: {e}")
                return
    else:
        logger.error("No configuration file provided.")
        return

    # setting up the database connection
    # db_url = f"mariadb+mariadbconnector://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"

    # Build DB URL based on engine type
    engine = config['db'].get('engine', 'sqlite').lower()

    if engine == "sqlite":
        sqlite_file = config['db'].get('file', 'AIEvaluationData.db')

        # project_root = src/app/importer/../../../
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

        # Put DB in project_root/data
        db_folder = os.path.join(base_dir, "data")
        os.makedirs(db_folder, exist_ok=True)

        db_path = os.path.join(db_folder, sqlite_file)
        db_url = f"sqlite:///{db_path}"

    elif engine == "mariadb":
        db_url = (
            "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}"
            .format(
                user=config['db']['user'],
                password=config['db']['password'],
                host=config['db']['host'],
                port=config['db']['port'],
                database=config['db']['database']
            )
        )

    else:
        raise ValueError(f"Unsupported database engine: {engine}")

    try:
        logger.info(f"Database URL: {db_url}")
        db = DB(db_url=db_url, debug=False, loglevel=loglevel)
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        return

    lang_fwd = { lang.code: lang.name for lang in db.languages }
    lang_rev = { lang.name: lang.code for lang in db.languages }

    # Show statistics of language distribution
    if args.stats:
        prompt_lang_stats = db.get_prompt_language_statistics()
        logger.info("Prompt Language Distribution Statistics:")
        table = Table(title="Prompt Language Distribution Statistics")
        table.add_column("Language", justify="left")
        table.add_column("ID", justify="right")
        table.add_column("Count", justify="right")
        for lang_id, count in prompt_lang_stats.items():
            lang_name = lang_fwd.get(lang_id, "Unknown")
            table.add_row(lang_name, str(lang_id), str(count))
        Console().print(table)

        response_lang_stats = db.get_response_language_statistics()
        logger.info("Response Language Distribution Statistics:")
        table = Table(title="Response Language Distribution Statistics")
        table.add_column("Language", justify="left")
        table.add_column("ID", justify="right")
        table.add_column("Count", justify="right")
        for lang_id, count in response_lang_stats.items():
            lang_name = lang_fwd.get(lang_id, "Unknown")
            table.add_row(lang_name, str(lang_id), str(count))
        Console().print(table)

        llm_judge_prompt_lang_stats = db.get_llm_judge_prompt_language_statistics()
        logger.info("LLM Judge Prompt Language Distribution Statistics:")
        table = Table(title="LLM Judge Prompt Language Distribution Statistics")
        table.add_column("Language", justify="left")
        table.add_column("ID", justify="right")
        table.add_column("Count", justify="right")
        for lang_id, count in llm_judge_prompt_lang_stats.items():
            lang_name = lang_fwd.get(lang_id, "Unknown")
            table.add_row(lang_name, str(lang_id), str(count))
        Console().print(table)

        return

    logger.info("Fixing language fields for prompts ...")
    for prompt in db.prompts:
        # if the language is already set and not 'auto', skip when not forced.
        if prompt.lang_id is not None and prompt.lang_id != lang_rev["auto"] and not args.force:
            continue

        # Determine the language from the prompt text
        lang_iso639 = lang_detect(prompt.user_prompt)
        lang_name = iso639_to_language_name(lang_iso639)
        if lang_name is None:
            logger.warning(f"Could not determine language for prompt ID {prompt.prompt_id}. Skipping.")
            continue

        # is the language known in the database?
        lang_id = lang_rev.get(lang_name)
        if lang_id is None:
            logger.warning(f"Detected language '{lang_name}' for prompt ID {prompt.prompt_id} is not known in the database. Adding...")
            # let's add the language to the database
            lang_id = db.add_or_get_language_id(lang_name)
            if lang_id is None:
                logger.error(f"Failed to add detected language '{lang_name}' for prompt ID {prompt.prompt_id}. Skipping.")
                continue
            # add the new language to lookup dictionaries
            lang_fwd[lang_id] = lang_name
            lang_rev[lang_name] = lang_id

       # If the detected language is different from the current one, update it
        if lang_id != prompt.lang_id:
           logger.info(f"Updating language for prompt ID {prompt.prompt_id} from '{lang_fwd.get(prompt.lang_id, 'unknown')}' to '{lang_name}'")
           prompt.lang_id = lang_id
           p_id = db.add_or_update_prompt(prompt)
           if p_id is None:
               logger.error(f"Failed to update language for prompt ID {prompt.prompt_id}.")
               continue

if __name__ == "__main__":
    main()


