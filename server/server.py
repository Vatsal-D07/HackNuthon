from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import cv2
import numpy as np
import base64
from pyzbar.pyzbar import decode
import json
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
JSON_FILE = "barcode_data.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize JSON file if it doesn't exist
def init_json():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as file:
            json.dump({}, file)

# Read barcode data from JSON
def read_barcode_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

# Write barcode data to JSON
def write_barcode_data(barcode_data):
    with open(JSON_FILE, "w") as file:
        json.dump(barcode_data, file, indent=4)

# Validate file type
def is_valid_image(file: UploadFile):
    allowed_types = {"image/png", "image/jpeg", "image/jpg"}
    if file.content_type not in allowed_types:
        return False
    return True

# Detect barcodes in an image
def detect_barcodes(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")

    detected_barcodes = decode(img)
    barcode_data = read_barcode_data()
    barcode_results = []

    for barcode in detected_barcodes:
        barcode_text = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(img, f"{barcode_text} ({barcode_type})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if barcode_text in barcode_data:
            barcode_data[barcode_text]["count"] += 1
            barcode_data[barcode_text]["last_scanned"] = current_time
        else:
            barcode_data[barcode_text] = {"type": barcode_type, "count": 1, "last_scanned": current_time}

        barcode_results.append({"type": barcode_type, "data": barcode_text})

    write_barcode_data(barcode_data)
    return img, barcode_results

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        if not is_valid_image(file):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PNG, JPEG, and JPG are allowed.")

        init_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        processed_img, barcode_results = detect_barcodes(file_path)
        _, buffer = cv2.imencode('.jpg', processed_img)
        img_str = base64.b64encode(buffer).decode('utf-8')

        return JSONResponse(content={
            "message": "Image processed successfully",
            "processed_image": img_str,
            "barcodes": barcode_results,
            "found": len(barcode_results) > 0
        })

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/barcodes")
def get_all_barcodes():
    try:
        barcode_data = read_barcode_data()
        return JSONResponse(content={"barcodes": barcode_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
