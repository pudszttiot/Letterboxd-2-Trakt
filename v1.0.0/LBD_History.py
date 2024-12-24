#------------------------------------------------------------------------
#
# Letterboxd History Exporter Tool
#
# Created by:  pudszTTIOT  23/12/2024  <pudszttiot9@proton.me>
#
# Website:  https://github.com/pudszttiot/Letterboxd-2-Trakt
#
#------------------------------------------------------------------------
#
# Purpose:  Export Movies & TV Shows History from Letterboxd
#
#------------------------------------------------------------------------


import requests
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm  # Import tqdm for the progress bar
import pyTextColor

# Define the length for the separator (e.g., 30 '=' symbols)
separator = '▒▒▒▒' * 30  # Adjusted length for better appearance

# Define the header for the output CSV files
csv_file = "Watched_Movies_LBD.csv"
watchlist_csv_file = "Watchlist_LBD.csv"
csv_header = ["Date", "Name", "Year", "Letterboxd URI", "Rating"]  # Add "Rating" column for ratings data

# Initialize pyTextColor
pytext = pyTextColor.pyTextColor()

# Function to apply color to text using pyTextColor
def colored_text(text, hex_code, bg_color="#000000"):
    try:
        return pytext.format_text(text=text, color=hex_code, bgcolor=bg_color)
    except Exception as e:
        print(f"Error applying color: {e}")
        return text


# Function to extract movie URLs and (optional) ratings from the ratings page
def extract_ratings(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    ratings_data = {}
    
    # Get all rated movie containers (list items)
    movie_items = soup.find_all('li', class_='poster-container')
    
    for li in movie_items:
        lazy_load_div = li.find('div', class_='really-lazy-load')
        if lazy_load_div and lazy_load_div.get('data-target-link'):
            movie_url = "https://letterboxd.com" + lazy_load_div['data-target-link']
            rating_tag = li.find('span', class_='rating')
            if rating_tag:
                # Find the class that contains 'rated-' and extract the rating value
                rating_class = next((cls for cls in rating_tag['class'] if 'rated-' in cls), None)
                if rating_class:
                    # Convert rating by stripping 'rated-' and dividing by 2 to map to the 10-point scale
                    letterboxd_rating = float(rating_class.replace('rated-', '')) / 2
                    ratings_data[movie_url] = letterboxd_rating
    
    return ratings_data


# Function to extract movie URLs from the main list page
def extract_movie_urls(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    movie_data = []
    
    # Get all movie containers (list items)
    movie_items = soup.find_all('li', class_='poster-container')
    
    for li in movie_items:
        lazy_load_div = li.find('div', class_='really-lazy-load')
        
        if lazy_load_div and lazy_load_div.get('data-target-link'):
            movie_url = "https://letterboxd.com" + lazy_load_div['data-target-link']
            movie_data.append(movie_url)
    
    return movie_data

# Function to extract TMDb info from the detailed movie page
def extract_tmdb_info(movie_url):
    response = requests.get(movie_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the TMDb button by class and text content
    tmdb_button = soup.find('a', class_='micro-button track-event', string='TMDb')
    
    if tmdb_button:
        tmdb_link = tmdb_button.get('href')
        
        # Extract TMDB ID and type (movie or tv)
        if "/movie/" in tmdb_link:
            tmdb_id = tmdb_link.split("/movie/")[1].strip("/")
            media_type = "movie"
        elif "/tv/" in tmdb_link:
            tmdb_id = tmdb_link.split("/tv/")[1].strip("/")
            media_type = "show"
        else:
            tmdb_id = None
            media_type = None
        
        return movie_url, tmdb_id, media_type
    else:
        return movie_url, None, None

# Function to find the last page number by parsing pagination
def get_last_page(base_url):
    first_page_url = base_url + "/page/1/"
    response = requests.get(first_page_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find pagination container
    pagination = soup.find('div', class_='paginate-pages')
    
    if pagination:
        # Find the last page number by looking for the last link in the pagination
        last_page_link = pagination.find_all('a')[-1].get('href')
        last_page_number = int(last_page_link.split('/page/')[-1].strip('/'))
    else:
        # If no pagination is found, we assume there's only one page
        last_page_number = 1

    return last_page_number

# Function to crawl multiple pages using ThreadPoolExecutor
def crawl_movies(last_page, base_url):
    all_movie_urls = []
    
    # Use tqdm for the progress bar during the crawling process
    with tqdm(total=last_page, desc="Crawling Movie Pages", unit="page") as pbar:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for page in range(1, last_page + 1):
                page_url = base_url + f"/page/{page}/"
                futures.append(executor.submit(extract_movie_urls, page_url))
            
            # Collect the results as they are completed
            for future in as_completed(futures):
                all_movie_urls.extend(future.result())
                pbar.update(1)  # Update progress bar
    
    return all_movie_urls

# Function to crawl detailed movie pages for TMDb links
def crawl_detailed_movie_pages(movie_urls):
    all_movie_data = []
    
    # Use tqdm for the progress bar during the crawling process
    with tqdm(total=len(movie_urls), desc="Scanning Watched Movies", unit="movie") as pbar:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for movie_url in movie_urls:
                futures.append(executor.submit(extract_tmdb_info, movie_url))
            
            # Collect the results as they are completed
            for future in as_completed(futures):
                all_movie_data.append(future.result())
                pbar.update(1)  # Update progress bar
    
    return all_movie_data

# Function to save the extracted data to a CSV file
def save_to_csv(movie_data, ratings_data=None, csv_file=csv_file):
    # Calculate the total number of rows to write (movies + ratings)
    total_rows = len(movie_data)
    
    # Use tqdm to create a progress bar while writing to the CSV
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:  # Ensure UTF-8 encoding
        writer = csv.writer(file)
        writer.writerow(csv_header)  # Write the header
        
        # Create the progress bar for writing rows
        with tqdm(total=total_rows, desc="Creating Watched Movies CSV File", unit="movie") as pbar:
            for movie in movie_data:
                movie_url, tmdb_id, media_type = movie
                name, year = extract_movie_details(movie_url)
                date_today = datetime.today().strftime('%Y-%m-%d')  # Get today's date
                row = [date_today, name, year, movie_url]
                writer.writerow(row)
                pbar.update(1)  # Update the progress bar after each row is written
    
    # Feedback after saving with color
    print(colored_text("Movies and TV Shows saved to " + csv_file, "#87CEFA"))  # Use hex code for green


# Function to extract movie name and year from Letterboxd movie page
def extract_movie_details(movie_url):
    response = requests.get(movie_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract movie name
    title = soup.find('h1', class_='headline-1')
    if title:
        title = title.text.strip()
    else:
        title = "Unknown"  # Handle missing title

    # Extract movie year (added error handling)
    year_tag = soup.find('span', class_='year')
    if year_tag:
        year = year_tag.text.strip()
    else:
        year = "Unknown"  # Handle missing year
    
    return title, year


# Function to get the Letterboxd username and validate the input URL
def get_letterboxd_url():
    while True:
        print("\n")
        print(colored_text(separator, "#232B33"))  # Red text on yellow background
        print(colored_text(separator, "#FF7F00"))
        print(colored_text(separator, "#00E054"))
        print(colored_text(separator, "#3FBCF4"))
        print(colored_text(separator, "#FFFFFF"))
        print(colored_text("\n╔═════════════════════════════════════════════╗", "#90EE90", "#2C3440"))
        print(colored_text("  Welcome to the Letterboxd History Exporter!  ", "#40BCF4", "#000000"))  # Green text on black
        print(colored_text("╚═════════════════════════════════════════════╝\n", "#90EE90", "#2C3440"))
        print(colored_text("Enter your Letterboxd username: ", "#FFD700"))
        username = input()
        base_url = f"https://letterboxd.com/{username}/films"

        # Validate the URL by trying to access the first page
        try:
            response = requests.get(base_url)
            if response.status_code == 200:
                return base_url, username
            else:
                print(f"Invalid username or the page doesn't exist. Please try again.")
        except requests.RequestException:
            print(f"Error accessing the page. Please check your internet connection and try again.")


# Main function to run the script
if __name__ == "__main__":
    base_url, username = get_letterboxd_url()
    last_page = get_last_page(base_url)
    
    movie_urls = crawl_movies(last_page, base_url)
    movie_data = crawl_detailed_movie_pages(movie_urls)
    
    save_to_csv(movie_data)

    print(colored_text("Letterboxd Watched History Export Finished.", "#32CD32"))
