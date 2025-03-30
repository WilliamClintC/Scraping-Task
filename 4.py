import os
import pandas as pd
import glob
import time

# Define the CSV file path
csv_file_path = r"C:\Users\clint\Desktop\Scraping Task\df_6.csv"

# Load the dataframe
data = pd.read_csv(csv_file_path)

# Convert date column to datetime format
data['date'] = pd.to_datetime(data['date'])

# Sort the dataframe by date from earliest to latest
data = data.sort_values(by='date')

# Define directories
pdf_directory = r"C:\Users\clint\Desktop\Scraping Task\pdfs"
image_directory = r"C:\Users\clint\Desktop\Scraping Task\pdfs\Images"

# Function to save dataframe to CSV
def save_dataframe():
    new_csv_file_path = r"C:\Users\clint\Desktop\Scraping Task\df_7.csv"
    data.to_csv(new_csv_file_path, index=False)
    print(f"CSV file updated at: {new_csv_file_path}")

# Function to open a file with default Windows application
def open_file(file_path):
    if os.path.exists(file_path):
        os.startfile(file_path)
        print(f"Opening: {file_path}")
        # Allow time for application to open
        time.sleep(1.5)
        return True
    else:
        print(f"File not found: {file_path}")
        return False

# Function to update note column preserving existing content
def update_note(index, message):
    if pd.isna(data.loc[index, 'note']):
        data.loc[index, 'note'] = message
    else:
        data.loc[index, 'note'] = f"{data.loc[index, 'note']}; {message}"
    
    # Save the changes immediately to CSV
    save_dataframe()
    
    return data.loc[index, 'note']


# Iterate through each row in the dataframe (sorted by date)
for index, row in data.iterrows():
    # Get the PDF filename from the pdf_file_name column
    pdf_filename = row['pdf_filename']
    pdf_basename = os.path.splitext(pdf_filename)[0]
    
    # Display date for reference
    print(f"\nProcessing: {pdf_basename} - Date: {row['date'].strftime('%Y-%m-%d')}")
    
    # Build the full path to the PDF
    pdf_path = os.path.join(pdf_directory, pdf_filename)
    
    # Open the PDF
    if open_file(pdf_path):
        input(f"Opened {pdf_filename}. Press Enter to continue to associated images...")
        
        # Try multiple patterns to find associated images
        # Pattern 1: Exact prefix match (e.g., "01_2018_*.png")
        image_pattern = os.path.join(image_directory, f"{pdf_basename}_*.png")
        matching_images = glob.glob(image_pattern)
        
        # Pattern 2: Try with dashes instead of underscores in case of naming inconsistency
        if not matching_images:
            alt_basename = pdf_basename.replace('_', '-')
            image_pattern = os.path.join(image_directory, f"{alt_basename}*.png")
            matching_images.extend(glob.glob(image_pattern))
        
        # Pattern 3: Try more lenient matching (any file containing the basename)
        if not matching_images:
            # Get all image files
            all_image_files = glob.glob(os.path.join(image_directory, "*.png"))
            # Filter those containing the basename
            matching_images = [img for img in all_image_files if pdf_basename.lower() in os.path.basename(img).lower()]
        
        # Debug info
        print(f"Using pattern: {image_pattern}")
        print(f"Found {len(matching_images)} matching images")
        
        delete_count = 0
        skip_to_next_pdf = False
        
        if matching_images:
            print(f"Found {len(matching_images)} images associated with {pdf_filename}")
            
            # Process each associated image
            for img_path in matching_images:
                if skip_to_next_pdf:
                    break
                    
                img_filename = os.path.basename(img_path)
                
                # Open the image using Windows default viewer (likely Windows Photo app)
                if open_file(img_path):
                    # Ask whether to keep or delete
                    while True:
                        decision = input(f"Image: {img_filename} - Keep, Delete, or Skip to next PDF? (k/d/s): ").lower()
                        
                        if decision == 'd' or decision == 'delete':
                            try:
                                os.remove(img_path)
                                delete_count += 1
                                print(f"Deleted: {img_filename}")
                                break
                            except Exception as e:
                                print(f"Error deleting image: {e}")
                                continue
                        elif decision == 'k' or decision == 'keep':
                            print(f"Keeping: {img_filename}")
                            break
                        elif decision == 's' or decision == 'skip':
                            print(f"Skipping to next PDF...")
                            skip_to_next_pdf = True
                            break
                        else:
                            print("Invalid input. Please enter 'k' for keep, 'd' for delete, or 's' to skip to next PDF.")
            
            # Update the note column in the dataframe even when skipping
            if delete_count > 0:
                deletion_message = f"Manually deleted {delete_count} images"
                if skip_to_next_pdf:
                    deletion_message += " before skipping"
                
                # Update note preserving existing content and save immediately
                updated_note = update_note(index, deletion_message)
                print(f"Updated note for {pdf_filename}: {updated_note}")
        else:
            print(f"No images found for {pdf_filename}")
    
    # Wait for user confirmation before proceeding to next PDF, unless we're skipping
    if not skip_to_next_pdf:
        input(f"Finished processing {pdf_filename}. Press Enter to continue to next PDF...")

# Final save of the dataframe as a safeguard
save_dataframe()
print("Process complete. All changes have been saved.")