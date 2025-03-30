from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import cv2
import numpy as np
import base64
from pyzbar.pyzbar import decode
import csv
from datetime import datetime

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CSV file path for barcode tracking
CSV_FILE = "barcode_data.csv"

# Initialize CSV file if it doesn't exist
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Code", "Type", "Number", "LastScanned"])

# Function to read existing barcode data
def read_barcode_data():
    barcode_counts = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 3:
                    barcode, barcode_type, count = row[0], row[1], row[2]
                    last_scanned = row[3] if len(row) > 3 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    barcode_counts[barcode] = (barcode_type, int(count), last_scanned)
    return barcode_counts

# Function to write barcode data to CSV
def write_barcode_data(barcode_data):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Code", "Type", "Number", "LastScanned"])
        for barcode, (barcode_type, count, last_scanned) in barcode_data.items():
            writer.writerow([barcode, barcode_type, count, last_scanned])

# Function to detect barcodes
def detect_barcodes(image_path):
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")
    
    # Detect barcodes
    detected_barcodes = decode(img)
    
    # Read existing barcode data
    barcode_data = read_barcode_data()
    barcode_results = []
    
    # Process detected barcodes
    for barcode in detected_barcodes:
        # Extract barcode info
        barcode_text = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        
        # Draw rectangle around barcode
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Add text above barcode
        cv2.putText(img, f"{barcode_text} ({barcode_type})", (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Update barcode counts
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if barcode_text in barcode_data:
            existing_type, count, _ = barcode_data[barcode_text]
            barcode_data[barcode_text] = (existing_type, count + 1, current_time)
        else:
            barcode_data[barcode_text] = (barcode_type, 1, current_time)
            
        # Add to results
        barcode_results.append({
            "type": barcode_type,
            "data": barcode_text
        })
    
    # Write updated data
    write_barcode_data(barcode_data)
    
    return img, barcode_results

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Ensure CSV file exists
        init_csv()
        
        # Create a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process the image to detect barcodes
        processed_img, barcode_results = detect_barcodes(file_path)
        
        # Convert processed image to base64
        _, buffer = cv2.imencode('.jpg', processed_img)
        img_str = base64.b64encode(buffer).decode('utf-8')
        
        return JSONResponse(content={
            "message": "Image processed successfully",
            "processed_image": img_str,
            "barcodes": barcode_results,
            "found": len(barcode_results) > 0
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if _name_ == "_main_":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)