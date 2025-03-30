import cv2
import numpy as np
import csv
import os
from pyzbar.pyzbar import decode

# CSV file path
csv_file = "barcode_data.csv"

# Function to read existing barcode data and track occurrences
def read_barcode_data():
    barcode_counts = {}
    if os.path.exists(csv_file):
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 3:
                    barcode, barcode_type, count = row
                    barcode_counts[barcode] = (barcode_type, int(count))  # Ensure correct structure
    return barcode_counts

# Function to write barcode data to CSV
def write_barcode_data(barcode_data):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Code", "Type", "Number"])
        for barcode, (barcode_type, count) in barcode_data.items():
            writer.writerow([barcode, barcode_type, count])

# Function to detect barcodes and draw bounding boxes
def detect_barcodes(image_path):
    image = cv2.imread(image_path)
    try:
        barcodes = decode(image)
        barcode_data = read_barcode_data()
        
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            barcode_number = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            
            # Increment barcode count if it exists, otherwise default to 1
            if barcode_number in barcode_data:
                existing_type, count = barcode_data[barcode_number]
                barcode_data[barcode_number] = (existing_type, count + 1)
            else:
                barcode_data[barcode_number] = (barcode_type, 1)
            
            text = f"{barcode_number} ({barcode_type})"
            cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Write updated barcode data to CSV
        write_barcode_data(barcode_data)
        
        return image
    except:
        print(f"Warning: Barcode decoding error - {e}")
        return image

# Set image path directly in the code
image_path = "product2.jpg"  # Change this to the actual image path

# Process image
result_image = detect_barcodes(image_path)
# cv2.imshow("Barcode Detection", result_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
