from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import pytesseract
import base64
import io
from PIL import Image

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    filename = file.filename
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    
    # Process the image for barcode
    result = process_barcode_image(file_path)
    
    return jsonify(result)

def process_barcode_image(image_path):
    # Read the image
    image = cv2.imread(image_path)
    
    if image is None:
        return {"error": "Unable to load image"}
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Process image to enhance barcode detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive threshold
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Detect barcode
    decoded_objects = decode(gray)
    
    barcode_info = []
    
    # Draw rectangles around barcodes
    processed_img = image.copy()
    
    if decoded_objects:
        for obj in decoded_objects:
            barcode_data = obj.data.decode("utf-8")
            barcode_type = obj.type
            
            # Get barcode coordinates
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                hull = cv2.approxPolyDP(hull, 0.1 * cv2.arcLength(hull, True), True)
                points = hull
            
            # Convert points to numpy array
            pts = np.array([point for point in points], dtype=np.int32)
            
            # Draw polygon around the barcode
            cv2.polylines(processed_img, [pts], True, (0, 255, 0), 3)
            
            # Put barcode data and type on the image
            x = pts[0][0]
            y = pts[0][1]
            cv2.putText(processed_img, f"{barcode_type}: {barcode_data}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            barcode_info.append({
                "type": barcode_type,
                "data": barcode_data
            })
    
    # Save the processed image
    processed_img_path = image_path.replace('.jpg', '_processed.jpg')
    cv2.imwrite(processed_img_path, processed_img)
    
    # Convert processed image to base64 for frontend display
    _, buffer = cv2.imencode('.jpg', processed_img)
    img_str = base64.b64encode(buffer).decode('utf-8')
    
    result = {
        "message": "Image processed successfully",
        "original_path": image_path,
        "processed_path": processed_img_path,
        "processed_image": img_str,
        "barcodes": barcode_info,
        "found": len(barcode_info) > 0
    }
    
    return result

if __name__ == "__main__":
    app.run(debug=True)