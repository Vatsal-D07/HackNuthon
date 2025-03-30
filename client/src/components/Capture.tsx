"use client";

import React, { useRef, useState, useEffect } from "react";
import { Camera, Download, RefreshCw, Trash2, BarChart4 } from "lucide-react";
import { postImages, ProcessedImageResult } from "@/services/api/capture.service";

interface CapturedImage {
  file: File;
  result?: ProcessedImageResult;
}

export default function Capture() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImages, setCapturedImages] = useState<CapturedImage[]>([]);
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
    formData.append("file", tempImage);
  
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

  const startCamera = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (navigator.mediaDevices) {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "environment",
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

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");

      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `barcode-capture-${Date.now()}.jpg`, { type: "image/jpeg" });
            setTempImage(file);
            setProcessedResult(null);
          }
        }, "image/jpeg", 0.9);
      }
    }
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <h1 className="text-2xl font-bold mb-4">Barcode Scanner</h1>
      {error && <p className="text-red-600">{error}</p>}
      <div className="relative w-80 h-60 bg-black rounded-lg overflow-hidden">
        {!tempImage ? (
          <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
        ) : (
          <img src={URL.createObjectURL(tempImage)} alt="Captured" className="w-full h-full object-cover" />
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>
      <button
        onClick={capturePhoto}
        className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        <Camera className="inline-block mr-2" /> Capture
      </button>
    </div>
  );
}