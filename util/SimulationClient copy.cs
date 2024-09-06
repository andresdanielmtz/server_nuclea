using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

public class CameraRotator : MonoBehaviour
{
    public float rotationSpeed = 1f;  // Speed of oscillation
    public float rotationRange = 30f; // Max angle to rotate from center (so -30 to +30 degrees)
    private float initialYRotation;   // Store the initial rotation of the camera
    private bool isLocked = false;    // Whether the camera is locked or not

    void Start()
    {
        // Store the initial Y rotation of the camera so we can rotate around it
        initialYRotation = transform.eulerAngles.y;
    }

    void Update()
    {
        // Only rotate the camera if it is not locked
        if (!isLocked)
        {
            // Calculate the oscillation angle using a sine wave for smooth movement
            float oscillationAngle = Mathf.Sin(Time.time * rotationSpeed) * rotationRange;

            // Apply the new rotation to the camera's Y-axis (side-to-side)
            transform.rotation = Quaternion.Euler(0, initialYRotation + oscillationAngle, 0);
        }
    }

    // Public function to enable or disable rotation
    public void SetLocked(bool locked)
    {
        isLocked = locked;

        if (locked)
        {
            // If locked, reset rotation to the initial position
            transform.rotation = Quaternion.Euler(0, initialYRotation, 0);
        }
    }
}

public class SimulationClient : MonoBehaviour
{
    private const string baseUrl = "http://localhost:8585";

    // Prefabs for the objects to instantiate
    public GameObject dronePrefab;
    public GameObject guardPrefab;
    public GameObject policeCarPrefab;

    // Reference to the hardcoded cameras in the scene
    public List<GameObject> cameras;  // Assign camera GameObjects in the Inspector

    // Instances of the prefabs
    private GameObject drone;
    private GameObject guard;
    private GameObject policeCar;
    private bool policeCarCalled = false;

    void Start()
    {
        // Initialize the drone and guard only once
        InitializeSimulationObjects();

        // Start fetching the simulation state from the server
        StartCoroutine(GetSimulationState());
    }

    void InitializeSimulationObjects()
    {
        // Initialize drone - instantiate once
        if (drone == null && dronePrefab != null)
        {
            drone = Instantiate(dronePrefab, new Vector3(0, 40, 0), Quaternion.identity);
            Debug.Log("Drone instantiated.");
        }

        // Initialize guard - instantiate once
        if (guard == null && guardPrefab != null)
        {
            guard = Instantiate(guardPrefab, new Vector3(-58, 0, -42), Quaternion.identity);
            Debug.Log("Guard instantiated.");
        }
    }

    IEnumerator GetSimulationState()
    {
        while (true)
        {
            UnityWebRequest www = UnityWebRequest.Get(baseUrl + "/agents_info");
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                ProcessSimulationState(www.downloadHandler.text);
            }
            else
            {
                Debug.LogError("Failed to fetch simulation state: " + www.error);
            }

            yield return new WaitForSeconds(1f); // Fetch new data every second
        }
    }

    void ProcessSimulationState(string json)
    {
        try
        {
            JObject state = JObject.Parse(json);

            if (state == null)
            {
                Debug.LogError("Invalid JSON data received.");
                return;
            }

            // Update cameras - no new instantiation, just update their states
            if (state["cameras"] != null && state["cameras"].Type == JTokenType.Array)
            {
                JArray cameraArray = (JArray)state["cameras"];
                Debug.Log("Updating camera array with count: " + cameraArray.Count);

                // Loop through the hardcoded cameras and update their states
                for (int i = 0; i < cameraArray.Count && i < cameras.Count; i++)
                {
                    JObject cameraData = (JObject)cameraArray[i];

                    // Update camera state (e.g., rotation) if needed
                    GameObject camera = cameras[i];  // Hardcoded camera references
                    if (camera != null)
                    {
                        // Example: Rotate the camera based on some logic
                        // You can modify this based on the data in cameraData
                        camera.transform.rotation = Quaternion.Euler(0, Mathf.Sin(Time.time) * 45f, 0);
                        Debug.Log("Updated camera with ID: " + i);
                    }
                }
            }




            if (state["cameras"] != null && state["cameras"].Type == JTokenType.Array)
            {
                JArray cameraArray = (JArray)state["cameras"];
                Debug.Log("Updating camera array with count: " + cameraArray.Count);

                for (int i = 0; i < cameraArray.Count && i < cameras.Count; i++)
                {
                    JObject cameraData = (JObject)cameraArray[i];

                    if (cameraData["locked"] != null)
                    {
                        bool isLocked = (bool)cameraData["locked"];
                        GameObject camera = cameras[i];  // Get the camera from the hardcoded list

                        if (camera != null)
                        {
                            CameraRotator rotator = camera.GetComponent<CameraRotator>();
                            if (rotator != null)
                            {
                                rotator.SetLocked(isLocked);  // Lock or unlock the camera's rotation
                                Debug.Log("Camera " + i + " lock status: " + isLocked);
                            }
                        }
                    }
                }

                // Update the drone's position or behavior, no new instantiation
                if (state["drone"] != null)
                {
                    JObject droneData = (JObject)state["drone"];
                    Debug.Log("Drone data found.");

                    if (drone != null)
                    {
                        // Example: Move drone instance to a new position based on the state
                        drone.transform.position = new Vector3(50, 150, 50);  // Example of updating the instance
                        Debug.Log("Drone updated.");
                    }
                }

                // Update the guard's position or behavior, no new instantiation
                if (state["guard"] != null)
                {
                    JObject guardData = (JObject)state["guard"];
                    Debug.Log("Guard data found.");

                    if (guard != null)
                    {
                        // Update guard state or behavior if needed
                        Debug.Log("Guard updated.");
                    }

                    // Call the police if needed, no re-instantiation
                    if (guardData["callTheCops"] != null && guardData["callTheCops"].Type == JTokenType.Boolean && (bool)guardData["callTheCops"] && !policeCarCalled)
                    {
                        CallThePolice();
                    }
                }
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogError("Error processing simulation state: " + ex.Message);
        }
    }

    void CallThePolice()
    {
        if (policeCarPrefab != null && !policeCarCalled)
        {
            Vector3 spawnPosition = new Vector3(-20, 0, -20);  // Police car spawn position
            policeCar = Instantiate(policeCarPrefab, spawnPosition, Quaternion.identity);
            policeCarCalled = true;
            Debug.Log("Police car has been called and instantiated.");
        }
        else
        {
            Debug.LogError("Police car prefab not assigned or already called!");
        }
    }
}