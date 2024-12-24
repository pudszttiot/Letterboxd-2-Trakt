#------------------------------------------------------------------------
#
# Letterboxd to Trakt Importer Tool
#
# Created by:  pudszTTIOT  23/12/2024  <pudszttiot9@proton.me>
#
# Website:  https://github.com/pudszttiot/Letterboxd-2-Trakt
#
#------------------------------------------------------------------------
#
# Purpose:  Import Movies & TV Shows History from Letterboxd to Trakt.tv
#
#------------------------------------------------------------------------


import pyTextColor
import csv
import requests
import logging
import argparse
import os
from dotenv import load_dotenv
from tqdm import tqdm

# Define the length for the separator (e.g., 30 '=' symbols)
separator = '▒▒▒▒' * 30  # Adjusted length for better appearance

# Load API credentials from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Trakt API credentials from .env file
API_URL = "https://api.trakt.tv"
CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'trakt-api-version': '2',
    'trakt-api-key': CLIENT_ID,
}

# Initialize pyTextColor
pytext = pyTextColor.pyTextColor()

# Function to apply color to text using pyTextColor
def colored_text(text, hex_code, bg_color="#000000"):
    try:
        return pytext.format_text(text=text, color=hex_code, bgcolor=bg_color)
    except Exception as e:
        logging.error(f"Error applying color: {e}")
        return text


# Function to read Letterboxd watch history from a CSV file
def read_letterboxd_csv(file_path):
    logging.info(colored_text(f"Reading Letterboxd watch history from {file_path}...", "#00FF00"))
    watched_movies = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Extract relevant columns
                title = row.get('Name')
                year = row.get('Year')
                letterboxd_url = row.get('Letterboxd URI')

                # Skip if critical data is missing
                if not title or not letterboxd_url:
                    logging.warning(colored_text(f"Skipping row with missing critical data: {row}", "#FFFF00"))
                    continue

                # Add the entry to the watched_movies list
                watched_movies.append({
                    'title': title,
                    'year': year,
                    'letterboxd_url': letterboxd_url,
                })
    except FileNotFoundError:
        logging.error(colored_text(f"File not found: {file_path}", "#FF0000"))
    except Exception as e:
        logging.error(colored_text(f"Error reading CSV file: {e}", "#FF0000"))

    return watched_movies

# Function to process Letterboxd watch history
def process_letterboxd_history(file_path, dry_run):
    watched_movies = read_letterboxd_csv(file_path)

    for entry in watched_movies:
        title = entry['title']
        letterboxd_url = entry['letterboxd_url']
        
        # Ensure title and URL exist
        if not title or not letterboxd_url:
            logging.warning(colored_text(f"Skipping entry with missing title or URL: {entry}", "#FFA500"))
            continue

        logging.info(colored_text(f"Processing: {title} (URL: {letterboxd_url})", "#00CED1"))
        
        if dry_run:
            print(colored_text(f"Dry Run: Would add {title} from {letterboxd_url} to Trakt history.", "#1E90FF"))
        else:
            # Placeholder for adding to Trakt
            pass

def interactive_mode():
    separator = '▒▒▒▒' * 30  # Adjusted length for appearance
    print("\n")
    print(colored_text(separator, "#B43297"))  # Red text on yellow background
    print(colored_text(separator, "#F8EDF7"))
    print(colored_text(separator, "#EA0D27"))
    print(colored_text(separator, "#C072CF"))
    print(colored_text(separator, "#E49CAC"))
    print(colored_text("\n╔═════════════════════════════════════════════╗", "#C072CF", "#000000"))
    print(colored_text("  Welcome to the Letterboxd to Trakt Importer! ", "#EA0D27", "#000000"))  # Green text on black
    print(colored_text("╚═════════════════════════════════════════════╝\n", "#C072CF", "#000000"))
    file_path = input(colored_text("Enter the path to your Letterboxd CSV file: ", "#FFD700")).strip()
    dry_run_input = input(colored_text("Enable dry-run mode [no changes made]? (y/n): ", "#FFD700")).strip().lower()

    dry_run = dry_run_input in ['yes', 'y']
    logging.info("Starting interactive mode...")
    process_letterboxd_history(file_path=file_path, dry_run=dry_run)

# Command-line interface
def main():
    parser = argparse.ArgumentParser(description="Import Letterboxd watch history into Trakt.")
    parser.add_argument("--file", type=str, help="Path to the Letterboxd CSV file.")
    parser.add_argument("--dry-run", action="store_true", help="If set, won't modify your Trakt history.")
    args = parser.parse_args()

    if args.file:
        process_letterboxd_history(file_path=args.file, dry_run=args.dry_run)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
