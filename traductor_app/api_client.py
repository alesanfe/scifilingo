from dataclasses import dataclass
from typing import Union, Dict, Any

import requests

@dataclass
class APIFunTranslation:
    endpoint: str = 'https://api.funtranslations.com/translate/'

    def translate(self, language: str, text: str) -> Union[dict[str, Union[bool, Any]], str]:
        """
        Translates the given text to the specified language using the translation API.

        Args:
            language (str): The language code of the desired translation.
            text (str): The text to be translated.

        Returns:
            str: The translated text.

        Raises:
            requests.exceptions.RequestException: If there was an error making the API request.
        """
        # Construct the URL for the translation API
        url = f"{self.endpoint}{language}.json"

        # Prepare the data to be sent in the API request
        data = {"text": text}
        headers = {"Content-Type": "application/json"}

        try:
            # Send the API request
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            # Parse the response and return the translated text
            return response.json()["contents"]["translated"]
        except requests.exceptions.RequestException:
            # Return an error message if there was an error making the API request
            return "Error"




