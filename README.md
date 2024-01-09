# Connecting the Pieces
In this assignment, you will integrate the individual self-driving lab components from prior modules to orchestrate the full "Hello World" workflow. This requires use of a microcontroller to control an LED light and acquire sensor data, an orchestrator to manage a Bayesian optimization campaign, an internet-of-things protocol to communicate between the orchestrator and the microcontroller, and a database for storing and retrieving the results.

## The assignment
The tests are failing right now because the appropriate credentials haven't been added and the microcontroller ([`microcontroller.py`](microcontroller.py)) and orchestrator ([`orchestrator.py`](orchestrator.py)) scripts haven't been updated. Adding the secrets and implementing these scripts will make the tests green. Note that the tests assume you are actively running `microcontroller.py` on your Pico W microcontroller.

Refer back to this module's tutorial on the main course website for quick access to resources from prior modules.

### MongoDB Setup and GitHub Secrets

For this assignment, you will need to add the [GitHub repository secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) listed below both as GitHub Actions secrets and Codespaces secrets, so that both you and the autograding scripts can access them. Please also keep a backup copy of these secrets in a secure location.

**The secrets to be added to GitHub Actions and Codespaces are:**

| Variable Name       | Description |
|---------------------|-------------|
| `COURSE_ID`         | Your student identifier for the course |
| `HIVEMQ_HOST`       | The HiveMQ cluster host URL |
| `HIVEMQ_USERNAME`   | The HiveMQ username |
| `HIVEMQ_PASSWORD`   | The HiveMQ password |
| `CLUSTER_NAME`      | The name of your MongoDB cluster |
| `DATABASE_NAME`     | The name of your database within the cluster |
| `COLLECTION_NAME`   | The name of the collection from your database |
| `ENDPOINT_BASE_URL` | The base URL of the Data API endpoint for the microcontroller to use |
| `DATA_API_KEY`      | The Data API key for the microcontroller to access the cluster's data |
| `CONNECTION_STRING` | The connection string for the Python orchestrator to connect to MongoDB |

Navigate to your GitHub assignment repository. The link will be of the form `https://github.com/ACC-HelloWorld/6-connecting-the-pieces-GITHUB_USERNAME`, where `GITHUB_USERNAME` is replaced with your own (e.g., `sgbaird`).

Refer to previous tutorials and assignments for details on creating, accessing, and adding each of these credentials. While tedious, this approach is a one-time setup that simplifies the development and autograding process while adhering to security best practices. Your `COURSE_ID` can be accessed from the main course website by referencing the corresponding quiz response from the orientation module.

### Orchestrator

The orchestrator is responsible for communicating with the microcontroller, setting up and running the optimization campaign, and summarizing the database results.

#### Hardware/software communication

For this assignment, payload dictionaries refer to the dictionaries that are being passed back-and-forth between the microcontroller and orchestrator. In this case, the orchestrator passes a payload dictionary *to* the microcontroller (after converting to a JSON string). Here is an example dictionary:

```python
command = {"R": 255, "G": 0, "B": 0}
experiment_id = "a1b2c3"
session_id = "d4e5f6"

payload_dict = {
    "command": command,
    "experiment_id": experiment_id,
    "session_id": session_id,
}
print(payload_dict)
# {'command': {'R': 255, 'G': 0, 'B': 0}, 'experiment_id': 'a1b2c3', 'session_id': 'd4e5f6'}
```

In this assignment, a results dictionary refers to the payload that the orchestrator receives from the microcontroller which includes both the original payload and the sensor data. Here is an example of this dictionary:

```python
command = {"R": 255, "G": 0, "B": 0}
experiment_id = "a1b2c3"
session_id = "d4e5f6"
sensor_data = {'ch410': 25.5, 'ch440': 51.0, 'ch470': 76.5, 'ch510': 102.0, 'ch550': 127.5, 'ch583': 153.0, 'ch620': 229.5, 'ch670': 255.0}

results_dict = {
    "command": command,
    "experiment_id": experiment_id,
    "session_id": session_id,
    "sensor_data": sensor_data,
}
print(results_dict)
# {'command': {'R': 255, 'G': 0, 'B': 0}, 'experiment_id': 'a1b2c3', 'session_id': 'd4e5f6', 'sensor_data': {'ch410': 25.5, 'ch440': 51.0, 'ch470': 76.5, 'ch510': 102.0, 'ch550': 127.5, 'ch583': 153.0, 'ch620': 229.5, 'ch670': 255.0}}
```


#### Bayesian optimization

The Bayesian optimization (BO) client will use a model-based approach to suggest new colors to try based on the results of previous experiments with the goal of minimizing the mismatch between the measured spectrum and the target spectrum (see below). Once the optimization budget has been exhausted, in our case by completing a fixed number of iterations, the BO client will return the best parameters as determined by the BO model. A visualization of the optimization process will show the lowest mismatch so far as a function of the number of iterations.

##### Mean absolute error 

<!-- This probably should have been in Bayesian optimization module - best to move this portion out of the LightMixer class -->

The Bayesian optimization objective is the mean absolute error (MAE) between the target sensor data and the observed sensor data. The MAE between the values in two dictionaries with identical keys can be computed as shown below. Note that the keys from `dict1` are used to index the values for both `dict1` and `dict2`.

```python
from sklearn.metrics import mean_absolute_error

dict1 = {'a': 1, 'b': 2, 'c': 3}
dict2 = {'a': 1, 'b': 4, 'c': 7}

keys = dict1.keys()
dict1_values = [dict1[key] for key in keys]
dict2_values = [dict2[key] for key in keys]

mae = mean_absolute_error(dict1_values, dict2_values)
print(mae)
# 2.0
```

NOTE: the code above assumes the values are all numeric.

#### Data logging

After the optimization is complete, the orchestrator should pull all results from the MongoDB database, read it into a pandas DataFrame, and save the data to a CSV file.

### Microcontroller

The microcontroller is responsible for setting the LED color, acquiring sensor data, communicating with the orchestrator, and logging results to the MongoDB database. **To achieve full points on the autograded tests, you are expected to upload your latest microcontroller script to the Pico W microcontroller and actively run it while the tests are running.**

#### Blink and read

The microcontroller should blink the LED with the color specified in the payload dictionary, read the sensor data, and then clear the LED color once finished.

#### Hardware/software communication

The microcontroller will receive a payload dictionary from the orchestrator, which includes the LED color to set and the experiment and session IDs. The microcontroller will then send a results dictionary back to the orchestrator, which includes the original payload and the sensor data that was acquired.

##### Payload dictionary

For this assignment, payload dictionaries refer to dictionaries that are being passed *to* something. In this case, the microcontroller passes a payload dictionary *to* the orchestrator (after converting to a JSON string), which includes both the original payload and the sensor data that was acquired by the microcontroller. From the orchestrator's perspective, this is a "results dictionary" (see the Orchestrator section above for more details). Here is an example of a payload dictionary that the microcontroller would send to the orchestrator:

```python
command = {"R": 255, "G": 0, "B": 0}
experiment_id = "a1b2c3"
session_id = "d4e5f6"
sensor_data = {'ch410': 25.5, 'ch440': 51.0, 'ch470': 76.5, 'ch510': 102.0, 'ch550': 127.5, 'ch583': 153.0, 'ch620': 229.5, 'ch670': 255.0}

payload_dict = {
    "command": command,
    "experiment_id": experiment_id,
    "session_id": session_id,
    "sensor_data": sensor_data,
}
print(payload_dict)
# {'command': {'R': 255, 'G': 0, 'B': 0}, 'experiment_id': 'a1b2c3', 'session_id': 'd4e5f6', 'sensor_data': {'ch410': 25.5, 'ch440': 51.0, 'ch470': 76.5, 'ch510': 102.0, 'ch550': 127.5, 'ch583': 153.0, 'ch620': 229.5, 'ch670': 255.0}}
```

#### Data logging

The microcontroller should log the results at the end of each experiment to the MongoDB database. The results dictionary should include the original payload and the sensor data that was acquired.

## Setup command

See `postCreateCommand` from [`devcontainer.json`](.devcontainer/devcontainer.json).

## Run command
`pytest`

You can also use the "Testing" sidebar extension to easily run individual tests.