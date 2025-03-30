
import axiosInstance from "../AxiosIntance";

export const postImages = async (data: FormData) => {
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