// import axiosInstance from "../AxiosIntance";

// export const postImages = async (data: FormData) => {
//     try {
//       const response = await axiosInstance.post("/upload", data, {
//         headers: {
//           "Content-Type": "multipart/form-data",
//         },
//       });
//       return response.data;
//     } catch (error) {
//       console.error("Error uploading image:", error);
//       throw error;
//     }
//   };

import axiosInstance from "../AxiosIntance";

export interface BarcodeInfo {
  type: string;
  data: string;
}

export interface ProcessedImageResult {
  message: string;
  processed_image: string;
  barcodes: BarcodeInfo[];
  found: boolean;
}

export const postImages = async (data: FormData): Promise<ProcessedImageResult> => {
  try {
    const response = await axiosInstance.post("/upload", data, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error uploading image:", error);
    throw error;
  }
};  