# -*- coding: utf-8 -*-
import argparse
import os
import sys
import logging
from rcp_core import run_rcp_process

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    This script is a command-line wrapper for the core RCP logic.
    It parses arguments from the command line or environment variables
    and then calls the main processing function from rcp_core.
    """
    logging.info(f"--- rcp.py wrapper script started ---")
    
    parser = argparse.ArgumentParser(description="RCP Wrapper - A command-line interface for the Remote Torrent Copy process.")
    parser.add_argument("tor_path", nargs='?', default=None, help="The local file path of the torrent content.")
    parser.add_argument("--torhash", "-t", help="The HASH of the torrent.")
    parser.add_argument("--torname", "-n", help="The name of the torrent.")
    parser.add_argument("--dl_uuid", "-u", help="The UUID of the download task (optional).")
    
    args = parser.parse_args()

    # Prioritize command-line arguments
    tor_path = args.tor_path
    torhash = args.torhash
    dl_uuid = args.dl_uuid
    torname = args.torname

    # Fallback to environment variables if arguments are not provided
    if not all([tor_path, torhash]):
        logging.info("Path or hash not provided via command line, attempting to load from environment variables.")
        tor_path = tor_path or os.environ.get('RCP_TOR_PATH')
        torhash = torhash or os.environ.get('RCP_TOR_HASH')
        dl_uuid = dl_uuid or os.environ.get('RCP_DL_UUID')
        torname = torname or os.environ.get('RCP_TOR_NAME')
        
        logging.info(f"Values from environment: Path={tor_path}, Hash={torhash}, UUID={dl_uuid}, Name={torname}")

    # Final check for required parameters
    if not tor_path or not torhash:
        logging.error("Error: tor_path and torhash must be provided either via command-line arguments or environment variables.")
        parser.print_help()
        sys.exit(1)

    try:
        run_rcp_process(
            tor_path=tor_path,
            torhash=torhash,
            dl_uuid=dl_uuid,
            torname=torname
        )
        logging.info("--- rcp.py wrapper script finished successfully. ---")
    except Exception as e:
        logging.error(f"An error occurred during the RCP process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()