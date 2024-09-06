using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json.Linq;

public class DroneController : MonoBehaviour
{
    public float droneSpeed = 5f;  // Speed of the drone movement
    private Vector3 targetPosition; // Target position from the JSON
    private bool panoramicMode = false; // Is the drone in panoramic mode?
    private bool droneOverride = false; // Should the drone override normal movement?

    private string droneInfoUrl = "http://localhost:8585/drone_info"; // JSON endpoint

    void Start()
    {
        // Start fetching the drone's state from the server
        StartCoroutine(FetchDroneInfo());
    }

    void Update()
    {
        // If the drone is not in override mode and not in panoramic mode, move towards the target
        if (!droneOverride && !panoramicMode)
        {
            MoveToTarget();
        }
    }

    void MoveToTarget()
    {
        // Smoothly move towards the target position
        transform.position = Vector3.MoveTowards(transform.position, targetPosition, droneSpeed * Time.deltaTime);
    }

    IEnumerator FetchDroneInfo()
    {
        while (true)
        {
            UnityWebRequest www = UnityWebRequest.Get(droneInfoUrl);
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                ProcessDroneInfo(www.downloadHandler.text);
            }
            else
            {
                Debug.LogError("Failed to fetch drone info: " + www.error);
            }

            // Fetch new data every second
            yield return new WaitForSeconds(1f);
        }
    }

    void ProcessDroneInfo(string json)
    {
        try
        {
            JObject droneData = JObject.Parse(json);

            // Parse the current position from the array
            if (droneData["current_position"] != null && droneData["current_position"].Type == JTokenType.Array)
            {
                JArray positionArray = (JArray)droneData["current_position"];

                if (positionArray.Count == 3)
                {
                    // Parse the x, y, z values directly from the array
                    float x = positionArray[0].ToObject<float>();
                    float y = positionArray[1].ToObject<float>();
                    float z = positionArray[2].ToObject<float>();

                    targetPosition = new Vector3(x, y, z);
                    Debug.Log("New target position: " + targetPosition);
                }
                else
                {
                    Debug.LogError("current_position array does not contain exactly 3 values.");
                }
            }
            else
            {
                Debug.LogError("current_position field is missing or not an array.");
            }

            // Check if the drone should be in panoramic mode
            if (droneData["panoramic"] != null)
            {
                panoramicMode = droneData["panoramic"].ToObject<bool>();
                Debug.Log("Panoramic mode: " + panoramicMode);
            }

            // Check if the drone is in override mode
            if (droneData["drone_override"] != null)
            {
                droneOverride = droneData["drone_override"].ToObject<bool>();
                Debug.Log("Drone override mode: " + droneOverride);
            }

            // Optionally process detection or other fields
            if (droneData["detection"] != null)
            {
                Debug.Log("Drone detection result: " + droneData["detection"]);
            }

            if (droneData["time_counter"] != null)
            {
                Debug.Log("Drone time counter: " + droneData["time_counter"]);
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogError("Error processing drone info JSON: " + ex.Message);
        }
    }
}