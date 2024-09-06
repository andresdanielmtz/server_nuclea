using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;
using System;

public class CameraStreamer : MonoBehaviour
{
    public Camera cameraToCapture;  // The camera from which to capture frames
    public float interval = 5f;     // Time interval between requests
    public string cameraId = "default_id"; // Unique ID for the camera

    void Start()
    {
        if (cameraToCapture == null)
        {
            cameraToCapture = Camera.main;  // Default to the main camera if none specified
        }

        if (cameraToCapture == null)
        {
            Debug.LogError("No camera assigned and no Main Camera in scene.");
            return;
        }

        StartCoroutine(CaptureAndSendFrames());
    }

    IEnumerator CaptureAndSendFrames()
    {
        while (true)
        {
            yield return new WaitForSeconds(interval);
            yield return SendFrameToServer();
        }
    }

    IEnumerator SendFrameToServer()
    {
        Debug.Log("Starting to capture and send frame...");

        // Ensure the camera and rendering pipeline are properly set up
        if (cameraToCapture == null)
        {
            Debug.LogError("No camera available for capturing.");
            yield break;
        }

        // Render the camera's view to a texture
        RenderTexture renderTexture = new RenderTexture(256, 256, 24);
        cameraToCapture.targetTexture = renderTexture;
        Texture2D texture = new Texture2D(renderTexture.width, renderTexture.height, TextureFormat.RGB24, false);

        cameraToCapture.Render();
        RenderTexture.active = renderTexture;
        texture.ReadPixels(new Rect(0, 0, renderTexture.width, renderTexture.height), 0, 0);
        texture.Apply();

        Debug.Log("Successfully captured the frame from the camera.");

        // Clean up the render texture
        cameraToCapture.targetTexture = null;
        RenderTexture.active = null;
        Destroy(renderTexture);

        // Encode texture to JPG
        byte[] imageData = texture.EncodeToJPG();
        Destroy(texture);

        Debug.Log("Image encoded to JPG format. Size: " + imageData.Length + " bytes");

        // Encode the byte array to Base64
        string base64Image = Convert.ToBase64String(imageData);

        Debug.Log("Image successfully encoded to Base64. Length: " + base64Image.Length);

        // Create a JSON object with the camera ID and the image
        string jsonBody = "{\"id\":\"" + cameraId + "\", \"image\":\"" + base64Image + "\"}";

        Debug.Log("JSON Payload: " + jsonBody);

        // Create a UnityWebRequest to send the image data to the server
        UnityWebRequest www = new UnityWebRequest("http://localhost:8585/vision", "POST");
        byte[] jsonToSend = new UTF8Encoding().GetBytes(jsonBody);
        www.uploadHandler = new UploadHandlerRaw(jsonToSend);
        www.downloadHandler = new DownloadHandlerBuffer();
        www.SetRequestHeader("Content-Type", "application/json");

        Debug.Log("Sending the request to the server...");

        // Send the request and wait for the response
        yield return www.SendWebRequest();

        // Check if there were any networking errors
        if (www.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("Error sending request: " + www.error);
            Debug.LogError("Server response: " + www.downloadHandler.text);

            // Additional debug: log more details about the request
            Debug.LogError("Request URL: " + www.url);
            Debug.LogError("Request Method: POST");
            Debug.LogError("Request Headers: " + www.GetRequestHeader("Content-Type"));
            Debug.LogError("Request Payload: " + jsonBody);
        }
        else
        {
            Debug.Log("Response from server: " + www.downloadHandler.text);
        }
    }
}