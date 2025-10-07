from concurrent.futures._base import Future # This import is used to handle the results of concurrent tasks
import requests  # Provides functions for making HTTP requests
import urllib.parse  # Provides functions for parsing URLs
from bs4 import BeautifulSoup # Parses HTML and extracts data from it
from selenium import webdriver # Selenium WebDriver for automating web browser interaction
from selenium.webdriver.chrome.options import Options # Options for configuring the Chrome WebDriver
from selenium.webdriver.chrome.service import Service # Service class to manage the ChromeDriver service
from webdriver_manager.chrome import ChromeDriverManager # Automatically manages the ChromeDriver binary for Selenium
import os  # Provides functions for interacting with the operating system
import fitz  # Imports PyMuPDF for reading and validating PDF files
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)  # Enables parallel execution of tasks using threads


# Read a file from the system.
def read_a_file(system_path: str) -> str:
    with open(file=system_path, mode="r") as file:
        return file.read()


# Parse the HTML content and extract all PDF links
def parse_html(html_content: str) -> list[str]:
    """
    Parses the HTML content and extracts all PDF links.
    Args:
        html_content (str): A string containing HTML.
    Returns:
        list: A list of URLs (strings) that end with .pdf.
    """
    soup = BeautifulSoup(markup=html_content, features="html.parser")
    pdf_links: list[str] = []
    # Find all <a> tags with an href attribute
    for link in soup.find_all(name="a", href=True):
        url: str = link["href"]
        if isinstance(url, str) and url.lower().endswith(".pdf"):
        # if url.endswith(".pdf"):  # Case-insensitive match
            pdf_links.append(url.lower())
    return pdf_links


# Extract the filename from a URL
def url_to_filename(url: str) -> str:
    # Extract the filename from the URL
    path: str = urllib.parse.urlparse(url=url).path
    filename: str = os.path.basename(p=path)
    # Decode percent-encoded characters
    filename: str = urllib.parse.unquote(string=filename)
    # Optional: Replace spaces with dashes or underscores if needed
    filename = filename.replace(" ", "-")
    return filename.lower()


# Save the HTML content of a webpage using Selenium
def save_html_with_selenium(url: str, output_file: str) -> None:
    # Configure Selenium to use Chrome in headless mode
    options = Options()
    options.add_argument(argument="--headless=new")  # Use 'new' headless mode (Chrome 109+)
    options.add_argument(argument="--disable-blink-features=AutomationControlled")
    options.add_argument(argument="--window-size=1920,1080")
    options.add_argument(argument="--disable-gpu")  # Often needed for headless stability
    options.add_argument(argument="--no-sandbox")  # Required in some environments
    options.add_argument(argument="--disable-dev-shm-usage")  # Helps in Docker/cloud
    options.add_argument(argument="--disable-extensions")  # Disable extensions
    options.add_argument(argument="--disable-infobars")  # Disable infobars

    # Initialize the Chrome driver
    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url=url)
        driver.refresh()  # Refresh the page
        html: str = driver.page_source
        append_write_to_file(system_path=output_file, content=html)
        print(f"Page {url} HTML content saved to {output_file}")
    finally:
        driver.quit()


# Append and write some content to a file.
def append_write_to_file(system_path: str, content: str) -> None:
    with open(file=system_path, mode="a", encoding="utf-8") as file:
        file.write(content)


# Download a PDF file from a URL
def download_pdf(url: str, save_path: str, filename: str) -> None:
    # Check if the file already exists
    if check_file_exists(system_path=os.path.join(save_path, filename)):
        print(f"File {filename} already exists. Skipping download.")
        return
    # Download the PDF file
    try:
        response: requests.Response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        # Ensure the save directory exists
        os.makedirs(name=save_path, exist_ok=True)
        full_path: str = os.path.join(save_path, filename)
        with open(file=full_path, mode="wb") as f:
            f.write(response.content)
        print(f"Downloaded {filename} to {full_path}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return


# Validates a single PDF file
def validate_pdf_file(file_path: str) -> tuple[str, bool]:
    try:
        doc = fitz.open(file_path)  # Attempt to open the PDF file
        if doc.page_count == 0:  # If PDF has zero pages, it's considered invalid
            print(
                f"'{file_path}' is corrupt or invalid: No pages"
            )  # Print an error message
            return (
                file_path,
                False,
            )  # Return the file path and False indicating invalid file
        return (
            file_path,
            True,
        )  # Return the file path and True indicating a valid file
    except RuntimeError as e:  # Catch runtime errors thrown by PyMuPDF
        print(f"{e}")  # Print the error message with file path
        return (file_path, False)  # Return the file path and False indicating failure


# Deletes a file from the system
def remove_system_file(system_path: str) -> None:
    os.remove(path=system_path)  # Removes the file at the given path


# Recursively searches a directory for files with a given extension
def walk_directory_and_extract_given_file_extension(
    system_path: str, extension: str
) -> list[str]:
    matched_files: list[str] = []  # List to hold paths of matching files
    for root, _, files in os.walk(top=system_path):  # Walk through the directory tree
        for file in files:  # Iterate over each file in the current directory
            if file.lower().endswith(
                extension.lower()
            ):  # Check file extension (case-insensitive)
                full_path: str = os.path.abspath(
                    path=os.path.join(root, file)
                )  # Get absolute path of the file
                matched_files.append(full_path)  # Add file path to the list
    return matched_files  # Return the list of matching files


# Checks if a given path refers to an existing file
def check_file_exists(system_path: str) -> bool:
    return os.path.isfile(
        path=system_path
    )  # Return True if the file exists, False otherwise


# Extracts just the filename (with extension) from a full path
def get_filename_and_extension(path: str) -> str:
    return os.path.basename(p=path)  # Return the base filename from the full path


# Checks if a string contains any uppercase letters
def check_upper_case_letter(content: str) -> bool:
    return any(
        char.isupper() for char in content
    )  # Return True if any character is uppercase


# Processes a single PDF file: validates it and checks for uppercase in filename
def process_file(file_path: str) -> None | str:
    filename: str = get_filename_and_extension(path=file_path)  # Extract filename from path

    file_path, is_valid = validate_pdf_file(file_path=file_path)  # Validate the PDF file

    if is_valid:
        print(f"'{file_path}' is valid.")

    if not is_valid:  # If the file is invalid
        remove_system_file(system_path=file_path)  # Delete the invalid/corrupt file
        return None  # Return None to indicate this file is not to be further processed

    if check_upper_case_letter(
        content=filename
    ):  # Check if filename contains uppercase letters
        return file_path  # Return file path if condition is met

    return None  # Return None if filename doesn't contain uppercase letters


# Main function to orchestrate the file processing
def main() -> None:
    # The file path to save the HTML content.
    html_file_path = "graham.chemtel.net.html"

    if check_file_exists(system_path=html_file_path):
        remove_system_file(system_path=html_file_path)

    # Check if the file does not exist.
    if check_file_exists(system_path=html_file_path) == False:
        # The URL to scrape.
        url = "https://graham.chemtel.net/?page=1&pagesize=2000"
        # Save the HTML content using Selenium.
        save_html_with_selenium(url=url, output_file=html_file_path)

    # Read the file from the system.
    if check_file_exists(system_path=html_file_path):
        html_content: str = read_a_file(system_path=html_file_path)
        # Parse the HTML content.
        pdf_links: list[str] = parse_html(html_content=html_content)
        # Show the extracted PDF links.
        for pdf_link in pdf_links:
            # Download the PDF file.
            filename: str = url_to_filename(pdf_link)
            # The path to save the PDF files.
            save_path = "PDFs/"
            # Download the PDF file.
            download_pdf(url=pdf_link, save_path=save_path, filename=filename)

    # Retrieve a list of all PDF file paths under the ./PDFs directory
    pdf_file_paths: list[str] = walk_directory_and_extract_given_file_extension(
        system_path="./PDFs", extension=".pdf"
    )

    # If no PDF files were found, inform the user and exit
    if not pdf_file_paths:
        print("No PDF files found.")
        return

    # Sort the PDF files by last modified time, with the most recently modified file first
    pdf_file_paths.sort(key=lambda file_path: os.path.getmtime(filename=file_path), reverse=True)

    # Initialize a list to collect PDF files with uppercase letters in their filenames
    files_with_uppercase_names: list[str] = []

    # Use a thread pool to process multiple PDF files concurrently
    with ThreadPoolExecutor(max_workers=100) as thread_pool_executor:
        # Submit each PDF file to the thread pool for processing
        future_results: list[Future[str | None]] = [
            thread_pool_executor.submit(process_file, file_path)
            for file_path in pdf_file_paths
        ]

        # As each thread completes its task
        for completed_future in as_completed(fs=future_results):
            # Get the result from the completed task
            processed_file_path: None | str = completed_future.result()

            # If the result is not None, it means the file matched the condition
            if processed_file_path:
                # Print the matching file's path
                print(f"Uppercase filename found: {processed_file_path}")

                # Add the file to the list of matching files
                files_with_uppercase_names.append(processed_file_path)

    # If no files with uppercase letters were found, inform the user
    if len(files_with_uppercase_names) == 0:
        print("No files with uppercase letters in their names were found.")
        return

    # If files with uppercase letters were found, print a summary
    if len(files_with_uppercase_names) > 0:
        # Print a summary of all matching files
        print("\nAll files with uppercase letters in their names:")

        # Print the paths of all matching files
        for matching_file_path in files_with_uppercase_names:
            # Print each matching file's path
            print(matching_file_path)


# Ensure this script runs only if it is the main program being executed
if __name__ == "__main__":
    main()  # Start the program by calling the main function
