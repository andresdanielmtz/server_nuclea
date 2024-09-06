using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;
using System;

public class CameraStreamer : MonoBehaviour
{
    public Camera cameraToCapture;  // The camera from which to capture frames
    public float interval = 5f;     // Time interval between requests

    void Start()
    {
        if (cameraToCapture == null)
        {
            cameraToCapture = Camera.main;  // Default to the main camera if none specified
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
        // Render the camera's view to a texture
        RenderTexture renderTexture = new RenderTexture(256, 256, 24);
        cameraToCapture.targetTexture = renderTexture;
        Texture2D texture = new Texture2D(renderTexture.width, renderTexture.height, TextureFormat.RGB24, false);

        cameraToCapture.Render();
        RenderTexture.active = renderTexture;
        texture.ReadPixels(new Rect(0, 0, renderTexture.width, renderTexture.height), 0, 0);
        texture.Apply();
        cameraToCapture.targetTexture = null;
        RenderTexture.active = null;
        Destroy(renderTexture);

        // Encode texture to JPG
        byte[] imageData = texture.EncodeToJPG();
        Destroy(texture);

        // Encode the byte array to Base64
        string base64Image = Convert.ToBase64String(imageData);

        // Create a JSON object
        string jsonBody = "{\"image\":\"" + base64Image + "\"}";

        // Create a UnityWebRequest to send the image data to the server
        UnityWebRequest www = new UnityWebRequest("http://localhost:5001/process", "POST");
        byte[] jsonToSend = new UTF8Encoding().GetBytes(jsonBody);
        www.uploadHandler = new UploadHandlerRaw(jsonToSend);
        www.downloadHandler = new DownloadHandlerBuffer();
        www.SetRequestHeader("Content-Type", "application/json");

        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
        {
            Debug.Log("Error sending request: " + www.error);
        }
        else
        {
            Debug.Log("Response from server: " + www.downloadHandler.text);
        }
    }
}