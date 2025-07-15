# from strategy_implementor import StrategyImplementor
from logger import get_logger
from utils import load_json, get_key_by_value

mapper = load_json("Data/metric_strategy_mapping.json")

# print("Mapper loaded:", mapper)

plans = load_json("Data/plans.json")

#print("Plans loaded:", plans)

datapoints = load_json("Data/DataPoints.json")

#print("Data points loaded:", datapoints)

responses = load_json("Data/responses.json")

#print("Responses loaded:", responses)

logger = get_logger("strategy_runner")

class StrategyRunner:
    """
    StrategyRunner is responsible for running the strategies based on the plans and metric mappings.
    """
    def __init__(self, plan_id: str, **kwargs) -> None:
        self.plan_id = plan_id


    # Please start from here!
    def get_plan_name(self, plan_id: str):
        """
        Get the plans based on the plan name.
        """
        logger.info(f"Fetching plan name for plan ID: {plan_id}.")
        plan_name = plans[plan_id].get("TestPlan_name", None)
        return plan_name
    
    def get_metric_ids(self, plan_id: str):
        """
        Get the metric IDs based on the plan ID.
        """
        if plan_id not in plans:
            logger.error(f"Plan ID {plan_id} not found in mapper.")
            return []
        else:
            logger.info(f"Fetching metric IDs for plan ID {plan_id}.")
            plan = plans.get(plan_id, {})
            metrics = plan.get("metrics", {})
            for i in metrics:
                if i not in mapper:
                    logger.warning(f"Metric ID {i} not found in mapper.")
            return list(metrics.keys())


    def data_loader(self, metric_id):
        """
        Load the data points and return them.
        """
        if metric_id not in datapoints:
            logger.error(f"Metric ID {metric_id} not found in data points.")
            return []
        else:
            logger.info(f"Loading data points for metric ID {metric_id}.")
            return datapoints[metric_id]["cases"]
    
    def extract_data_from_datapoints(self, list_of_datapoints):
        """
        Extract system prompts, agent responses, and expected responses from the list of data points.
        """
        prompt_ids = []
        judge_prompts = []
        system_prompts = []
        prompts = []
        expected_responses = []
        domain = []
        logger.info(f"Fetching data points from list .....")
        for datapoint in list_of_datapoints:
            prompt_ids.append(datapoint.get("PROMPT_ID", ""))
            judge_prompts.append(datapoint.get("LLM_AS_JUDGE", ""))
            prompts.append(datapoint.get("PROMPT", ""))
            domain.append(datapoint.get("DOMAIN", ""))
            system_prompts.append(datapoint.get("SYSTEM_PROMPT", ""))
            expected_responses.append(datapoint.get("EXPECTED_OUTPUT", ""))
        return {
            "prompt_ids": prompt_ids,
            "judge_prompts": judge_prompts,
            "system_prompts": system_prompts,
            "prompts": prompts,
            "expected_responses": expected_responses,
            "domain": domain
        }
    
    def extract_responses(self, prompt_ids:list):
        """
        Extract agent responses from the responses data.
        """
        agent_responses = {}
        for i, response in enumerate(responses):
            if response.get("prompt_id", "") in prompt_ids:
                prompt_id = response.get("prompt_id", "")
                agent_responses[f"{prompt_id}"] = response.get("response", "")
        return agent_responses
    
    def data_mapper(self, datapoints, response_datapoints):
        """
        Map the data points to the responses based on the prompt ID.
        """
        mapped_data = []
        dp_prompts = datapoints["prompt_ids"]
        print(f"Mapping data points with responses for prompts: {dp_prompts}")
        for i in range(len(dp_prompts)):
            print(f"Mapping prompt {dp_prompts[i]} with response {response_datapoints.get(dp_prompts[i], 'No response found')}")
            if dp_prompts[i] in list(response_datapoints.keys()):
                mapped_data.append({
                    "prompt_id": dp_prompts[i],
                    "system_prompt": datapoints["system_prompts"][i],
                    "agent_response": response_datapoints[f"{dp_prompts[i]}"],
                    "expected_response": datapoints["expected_responses"][i],
                    "judge_prompt": datapoints["judge_prompts"][i],
                    "domain": datapoints["domain"][i]
                })
        return mapped_data

    
    # def run(self, plan_name:str):
    #     plan_name = self.plan_name
    #     plan_id = get_key_by_value(plans, plan_name)
    #     strategies = mapper[plan_id]
    #     metric_data = self.data_loader(plan_id)
    #     if plan_id=="54" or plan_id=="66":
    #         for strategy_name in strategies:
    #             strategy_instance = StrategyImplementor(strategy_name=strategy_name)
    #             score = strategy_instance.execute(prompts: da, expected_responses: Optional[List[str]] = None, agent_responses: Optional[List[str]] = None, system_prompts: Optional[List[str]] = None, judge_prompts: Optional[List[str]] = None)
    #             logger.info(f"Strategy: {strategy_name}, Score: {score}")






#### Testing
# plan_id ="T1"
# strat_runner = StrategyRunner(plan_id=plan_id)
# print(strat_runner.get_plan_name(plan_id)) 
# a = strat_runner.get_metric_ids(plan_id)
# print(a)
# print(a[0])
# print(strat_runner.get_metric_ids(plan_id)) 
# print(strat_runner.data_loader(metric_id="28"))
# l = [{'PROMPT_ID': 'P701', 'LLM_AS_JUDGE': 'No', 'SYSTEM_PROMPT': 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages', 'PROMPT': 'Duniya का highest रेल पुल and arch bridge कहाँ है?', 'EXPECTED_OUTPUT': 'दुनिया का सबसे ऊँचा रेल पुल और आर्च ब्रिज भारत में चेनाब ब्रिज (Chenab Bridge) है, जो जम्मू-कश्मीर में 359 मीटर की ऊँचाई पर बना है।', 'DOMAIN': 'general'}, {'PROMPT_ID': 'P702', 'LLM_AS_JUDGE': 'No', 'SYSTEM_PROMPT': 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'PROMPT': 'Please explain photosynthesis in Gujarati and end with a summary in English.', 'EXPECTED_OUTPUT': 'Gujarati: ફોટોસિન્થેસિસ એ એક પ્રક્રિયા છે જેમાં... Summary in English: Photosynthesis is the process by which plants make food...', 'DOMAIN': 'education'}, {'PROMPT_ID': 'P703', 'LLM_AS_JUDGE': 'No', 'SYSTEM_PROMPT': 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'PROMPT': 'Indiavil எத்தனை பயிர் பருவங்கள் உள்ளன?', 'EXPECTED_OUTPUT': 'இந்தியாவில் முக்கியமான 3 பயிர் பருவங்கள் உள்ளன: 1. கரிமை / ரபி (Rabi)...2. கடலை / கபா (Kharif)...3. ஜெயாத் (Zaid)...', 'DOMAIN': 'agriculture'}, {'PROMPT_ID': 'P704', 'LLM_AS_JUDGE': 'No', 'SYSTEM_PROMPT': 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'PROMPT': 'Which fruit farming is the most profitable in India thoda telugu mein aur thoda Hindi mein.', 'EXPECTED_OUTPUT': 'భారతదేశంలో, అత్యంత లాభదాయకమైన పండ్ల పంటలలో మామిడి (Mango), దానిమ్మ (Pomegranate), మరియు అరటి (Banana) ప్రముఖమైనవి.  आम भारत में सबसे अधिक लाभदायक फलों में से एक है, खासकर उत्तर प्रदेश, आंध्र प्रदेश और महाराष्ट्र जैसे राज्यों में, क्योंकि इसकी घरेलू और अंतर्राष्ट्रीय दोनों बाजारों में बहुत अधिक मांग है। इसके अलावा, ड्रैगन फ्रूट की खेती भी हाल के वर्षों में काफी लाभदायक साबित हुई है।', 'DOMAIN': 'agriculture'}, {'PROMPT_ID': 'P705', 'LLM_AS_JUDGE': 'No', 'SYSTEM_PROMPT': 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'PROMPT': 'ಭಾರತದ ಮೊದಲ prime minister ಯಾರು?', 'EXPECTED_OUTPUT': 'ಭಾರತದ ಮೊದಲ ಪ್ರಧಾನ ಮಂತ್ರಿ ಪಂಡಿತ ಜವಾಹರಲಾಲ್ ನೆಹರು (Jawaharlal Nehru).', 'DOMAIN': 'education'}]

# print(strat_runner.extract_data_from_datapoints(list_of_datapoints=l))

# l = {'prompt_ids': ['P701', 'P702', 'P703', 'P704', 'P705'], 'judge_prompts': ['No', 'No', 'No', 'No', 'No'], 'system_prompts': ['You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages', 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.', 'You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.'], 'prompts': ['Duniya का highest रेल पुल and arch bridge कहाँ है?', 'Please explain photosynthesis in Gujarati and end with a summary in English.', 'Indiavil எத்தனை பயிர் பருவங்கள் உள்ளன?', 'Which fruit farming is the most profitable in India thoda telugu mein aur thoda Hindi mein.', 'ಭಾರತದ ಮೊದಲ prime minister ಯಾರು?'], 'expected_responses': ['दुनिया का सबसे ऊँचा रेल पुल और आर्च ब्रिज भारत में चेनाब ब्रिज (Chenab Bridge) है, जो जम्मू-कश्मीर में 359 मीटर की ऊँचाई पर बना है।', 'Gujarati: ફોટોસિન્થેસિસ એ એક પ્રક્રિયા છે જેમાં... Summary in English: Photosynthesis is the process by which plants make food...', 'இந்தியாவில் முக்கியமான 3 பயிர் பருவங்கள் உள்ளன: 1. கரிமை / ரபி (Rabi)...2. கடலை / கபா (Kharif)...3. ஜெயாத் (Zaid)...', 'భారతదేశంలో, అత్యంత లాభదాయకమైన పండ్ల పంటలలో మామిడి (Mango), దానిమ్మ (Pomegranate), మరియు అరటి (Banana) ప్రముఖమైనవి.  आम भारत में सबसे अधिक लाभदायक फलों में से एक है, खासकर उत्तर प्रदेश, आंध्र प्रदेश और महाराष्ट्र जैसे राज्यों में, क्योंकि इसकी घरेलू और अंतर्राष्ट्रीय दोनों बाजारों में बहुत अधिक मांग है। इसके अलावा, ड्रैगन फ्रूट की खेती भी हाल के वर्षों में काफी लाभदायक साबित हुई है।', 'ಭಾರತದ ಮೊದಲ ಪ್ರಧಾನ ಮಂತ್ರಿ ಪಂಡಿತ ಜವಾಹರಲಾಲ್ ನೆಹರು (Jawaharlal Nehru).'], 'domain': ['general', 'education', 'agriculture', 'agriculture', 'education']}

# #print(strat_runner.extract_responses(prompt_ids=['P701', 'P702', 'P703', 'P704', 'P705']))
# r = {'P701': 'Hi!', 'P702': 'this', 'P703': 'test', 'P704': 'Chat not found', 'P705': 'Bwahahah'}
# print(strat_runner.data_mapper(datapoints=l, response_datapoints=r))





