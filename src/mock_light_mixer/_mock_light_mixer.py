import numpy as np
from sklearn.metrics import mean_absolute_error


class LightMixer:
    """
    A class to simulate a light mixer that combines red, green, and blue LEDs at
    different power levels to produce different colors.

    The class can run a color experiment, which calculates sensor intensity
    values for different wavelengths based on the power levels of the LEDs. It
    can also calculate an objective function value for a given sensor data,
    defined as the mean absolute error between the given sensor data and the
    target sensor data.

    Attributes
    ----------
    noise : float
        The level of noise to add to the sensor data. This simulates real-world
        inaccuracies in the sensor readings.
    rng : numpy.random.Generator
        A random number generator instance from numpy.
    wavelengths : list of int
        The wavelengths at which the sensor intensity is calculated.
    red_coefficients : list of float
        Coefficients for how the red LED affects the sensor intensity at each
        wavelength.
    green_coefficients : list of float
        Coefficients for how the green LED affects the sensor intensity at each
        wavelength.
    blue_coefficients : list of float
        Coefficients for how the blue LED affects the sensor intensity at each
        wavelength.
    target_color : dict
        The target color, defined as a dictionary with keys 'R', 'G', 'B' and
        values as the power levels of the LEDs.
    target_sensor_data : dict
        The sensor intensity values at different wavelengths for the target
        color.

    Methods
    -------
    run_color_experiment(R, G, B):
        Calculate sensor intensity values for different wavelengths based on the
        power levels of red, green, and blue LEDs.
    calculate_objective(sensor_data):
        Calculates the objective function value for a given sensor data.
    calculate_rgb_mismatch(R, G, B):
        Calculate the mismatch between the target color and the actual color
        based on the power levels of red, green, and blue LEDs.
    """

    def __init__(self, noise=0.1):
        self._history = []  # for testing
        self.noise = noise
        self.rng = np.random.default_rng(42)

        # Define the wavelengths
        self.wavelengths = [410, 440, 470, 510, 550, 583, 620, 670]
        self.wavelength_names = [f"ch{wavelength}" for wavelength in self.wavelengths]

        # Coefficients for how each LED affects the sensor intensity at each wavelength, adjusted for typical color wavelengths

        # Stronger influence at longer wavelengths (red)
        self.red_coefficients = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.9, 1.0]

        # Stronger influence in the middle wavelengths (green)
        self.green_coefficients = [0.2, 0.4, 0.6, 0.8, 1.0, 0.8, 0.4, 0.2]

        # Stronger influence at shorter wavelengths (blue)
        self.blue_coefficients = [0.9, 1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.0]

        self.target_color = {"R": 255, "G": 127, "B": 63}

        self.target_sensor_data = self.run_color_experiment(**self.target_color)

        # needs to be after target_sensor_data is defined, to check more than
        # just object instantiation
        self._run_color_experiment_called = False  # for testing

        self._calculate_objective_called = False  # for testing

    def run_color_experiment(self, R, G, B):
        """
        Calculate sensor intensity values for different wavelengths based on the
        power levels of red, green, and blue LEDs, taking into account the
        typical wavelengths of red, green, and blue light.

        Parameters
        ----------
        R : int
            Power level of the red LED (0-255).
        G : int
            Power level of the green LED (0-255).
        B : int
            Power level of the blue LED (0-255).

        Returns
        -------
        dict
            Sensor intensity values at different wavelengths. The keys are
            strings of the form 'ch{wavelength}', and the values are the
            calculated intensities.

        Examples
        --------
        >>> mixer = LightMixer()
        >>> mixer.run_color_experiment(255, 127, 63)
        {
            "ch410": 102.2,
            "ch440": 220.4,
            "ch470": 225.6,
            "ch510": 178.8,
            "ch550": 191.6,
            "ch583": 204.4,
            "ch620": 217.2,
            "ch670": 230.0,
        }
        """
        # Calculate sensor intensity for each wavelength
        sensor_data = {}
        for i, wavelength_name in enumerate(self.wavelength_names):
            intensity = (
                self.red_coefficients[i] * R
                + self.green_coefficients[i] * G
                + self.blue_coefficients[i] * B
            )
            # Add noise
            intensity = self.rng.normal(intensity, self.noise * intensity)
            sensor_data[wavelength_name] = intensity

        self._history.append({"R": R, "G": G, "B": B, **sensor_data})

        self._run_color_experiment_called = True  # for testing

        return sensor_data

    def calculate_objective(self, sensor_data):
        """
        Calculates the objective function value for a given sensor data. The
        objective function is defined as the mean absolute error between the
        given sensor data and the target sensor data.

        Parameters
        ----------
        sensor_data : dict
            A dictionary containing the sensor intensity values at different
            wavelengths. The keys are strings of the form 'ch{wavelength}', and
            the values are the calculated intensities.

        Returns
        -------
        float
            The mean absolute error between the given sensor data and the target
            sensor data.

        Examples
        --------
        >>> sensor_data = {
        ...     "ch410": 102.2,
        ...     "ch440": 220.4,
        ...     "ch470": 225.6,
        ...     "ch510": 178.8,
        ...     "ch550": 191.6,
        ...     "ch583": 204.4,
        ...     "ch620": 217.2,
        ...     "ch670": 230.0,
        ... }
        >>> mixer.calculate_objective(sensor_data)
        15.8  # hypothetical output
        """
        score = mean_absolute_error(
            list(sensor_data.values()), list(self.target_sensor_data.values())
        )
        self._calculate_objective_called = True  # for testing
        return score

    def calculate_rgb_mismatch(self, R, G, B):
        """
        Calculate the mismatch between the target color and the actual color
        based on the power levels of red, green, and blue LEDs.

        Parameters
        ----------
        R : int
            Power level of the red LED (0-255).
        G : int
            Power level of the green LED (0-255).
        B : int
            Power level of the blue LED (0-255).

        Returns
        -------
        float
            A score to be minimized that represents the mismatch between the
            desired color and the actual color.

        Examples
        --------
        >>> mixer = LightMixer()
        >>> mixer.calculate_rgb_mismatch(255, 127, 63)
        12345.67
        """
        return mean_absolute_error(list(self.target_color.values()), [R, G, B])
