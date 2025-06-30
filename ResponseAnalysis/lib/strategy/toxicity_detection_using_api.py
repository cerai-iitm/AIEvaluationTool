from .strategy_base import Strategy
from googleapiclient import discovery
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class ToxicityDetectionUsingAPI(Strategy):
    def detect_toxicity_using_perspective_api(input_string: str, API_KEY: str):
        client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=API_KEY,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )

        analyze_request = {
            'comment': {'text': input_string},
            'requestedAttributes': {'TOXICITY': {}}
        }

        response = client.comments().analyze(body=analyze_request).execute()
        toxicity_score = response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
        return toxicity_score

    def evaluate(self, test_string: str, API_KEY: str) -> float:
        """
        Analyzes the toxicity level of a given text using the Perspective API.

        param: input_string (str) - The text input to be analyzed for toxicity.
        param: API_KEY (str) - Google Perspective API key for authenticating the request.

        Returns: toxicity_level (float) -  A toxicity score between 0.0 (non-toxic) and 1.0 (highly toxic) as determined by the Perspective API.
        """
        toxicity_level = self.detect_toxicity_using_perspective_api(input_string=test_string, API_KEY=API_KEY)
        return toxicity_level

toxicity_detector = ToxicityDetectionUsingAPI()
test_string = "I hate you and your country"
API_KEY = os.environ.get("API_KEY")
print(f"Toxicity Score for {test_string}: ", toxicity_detector.evaluate(input_string=test_string, API_KEY=API_KEY))