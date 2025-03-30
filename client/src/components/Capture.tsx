"use client";

import React, { useRef, useState, useEffect } from "react";
import { Camera, Download, RefreshCw, Trash2, BarChart4 } from "lucide-react";
import { postImages } from "@/services/api/capture.service";

interface BarcodeInfo {
  type: string;
  data: string;
}

interface ProcessedImageResult {
  message: string;
  processed_image: string;
  barcodes: BarcodeInfo[];
  found: boolean;
}

export default function Capture() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImages, setCapturedImages] = useState<File[]>([]);
  const [tempImage, setTempImage] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [processedResult, setProcessedResult] = useState<ProcessedImageResult | null>(null);
  
  useEffect(() => {
    if (tempImage) {
      postImageApi();
    }
  }, [tempImage]);

  const postImageApi = async () => {
    if (!tempImage) return;
    
    setIsLoading(true);
    
    const formData = new FormData();
    formData.append("file", tempImage);  // Append the captured image file
  
    try {
      const response = await postImages(formData);
      console.log("Upload Success:", response);
      setProcessedResult(response);
    } catch (error) {
      console.error("Upload Failed:", error);
      setError("Failed to process the image. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Start camera
  const startCamera = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (navigator.mediaDevices) {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "environment",  // Use rear camera for better barcode scanning
            width: { ideal: 1280 },
            height: { ideal: 720 },
            aspectRatio: { ideal: 16 / 9 },
          },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }

        setStream(mediaStream);
      }
    } catch (err) {
      console.error("Error accessing webcam:", err);
      setError("Unable to access camera. Please grant camera permissions.");
    } finally {
      setIsLoading(false);
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  // Capture photo and store as File
  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");

      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // For rear camera, don't flip the image
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `barcode-capture-${Date.now()}.jpg`, {
              type: "image/jpeg",
            });
            setTempImage(file);
            setProcessedResult(null);  // Clear previous results
          }
        }, "image/jpeg", 0.9);
      }
    }
  };

  // Save captured image to array
  const saveImage = () => {
    if (tempImage) {
      setCapturedImages((prevImages) => [...prevImages, tempImage]);
      setTempImage(null);
      setProcessedResult(null);
    }
  };

  // Retake image
  const retakeImage = () => {
    setTempImage(null);
    setProcessedResult(null);
  };

  // Delete specific image
  const deleteImage = (index: number) => {
    setCapturedImages((prevImages) => prevImages.filter((_, i) => i !== index));
  };

  // Download captured image
  const downloadImage = (file: File) => {
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");
    link.href = url;
    link.download = file.name;
    link.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [tempImage]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="max-w-3xl mx-auto p-6">
        <h1 className="text-3xl font-bold text-gray-900 text-center mb-4">
          Barcode Scanner
        </h1>

        {error && <div className="text-red-600 text-center mb-4">{error}</div>}

        <div className="bg-white rounded-2xl shadow-xl p-6">
          <div className="relative mb-6 rounded-xl overflow-hidden bg-black">
            <div className="aspect-[4/3] w-full max-w-2xl mx-auto">
              {!tempImage ? (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full h-full object-cover"
                />
              ) : processedResult ? (
                <img
                  src={`data:image/jpeg;base64,${processedResult.processed_image}`}
                  alt="Processed"
                  className="w-full h-full object-cover"
                />
              ) : (
                <img
                  src={URL.createObjectURL(tempImage)}
                  alt="Captured"
                  className="w-full h-full object-cover"
                />
              )}
            </div>
            <canvas ref={canvasRef} className="hidden" />
          </div>

          {isLoading && (
            <div className="text-center py-3">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2">Processing image...</p>
            </div>
          )}

          {processedResult && processedResult.barcodes.length > 0 && (
            <div className="mb-4 bg-green-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-green-800 flex items-center">
                <BarChart4 className="w-5 h-5 mr-2" /> Barcode Detected
              </h3>
              {processedResult.barcodes.map((barcode, idx) => (
                <div key={idx} className="mt-2">
                  <p><span className="font-medium">Type:</span> {barcode.type}</p>
                  <p><span className="font-medium">Data:</span> {barcode.data}</p>
                  <p><span className="font-medium">Expiry-Date:</span> {}</p>
                </div>
              ))}
            </div>
          )}

          {processedResult && processedResult.barcodes.length === 0 && (
            <div className="mb-4 bg-yellow-50 p-4 rounded-lg">
              <p className="text-yellow-800">No barcode detected in this image. Try again with a clearer image.</p>
            </div>
          )}

          <div className="flex justify-center gap-4">
            {!tempImage ? (
              <button
                onClick={capturePhoto}
                className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-lg"
                disabled={isLoading}
              >
                <Camera className="w-5 h-5" /> Capture Photo
              </button>
            ) : (
              <>
                <button
                  onClick={retakeImage}
                  className="flex items-center gap-2 px-8 py-3 bg-gray-600 text-white rounded-lg"
                  disabled={isLoading}
                >
                  <RefreshCw className="w-5 h-5" /> Retake
                </button>
                <button
                  onClick={saveImage}
                  className="flex items-center gap-2 px-8 py-3 bg-green-600 text-white rounded-lg"
                  disabled={isLoading}
                >
                  <Download className="w-5 h-5" /> Save Image
                </button>
              </>
            )}
          </div>
        </div>

        {capturedImages.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Captured Images</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {capturedImages.map((image, index) => (
                <div key={index} className="relative group">
                  <img
                    src={URL.createObjectURL(image)}
                    alt={`Captured ${index + 1}`}
                    className="w-full h-40 object-cover rounded-lg"
                  />
                  <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100">
                    <button onClick={() => downloadImage(image)} className="bg-blue-600 p-1 rounded-lg">
                      <Download className="w-5 h-5 text-white" />
                    </button>
                    <button onClick={() => deleteImage(index)} className="bg-red-600 p-1 rounded-lg">
                      <Trash2 className="w-5 h-5 text-white" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}