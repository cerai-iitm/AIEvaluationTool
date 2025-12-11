import numpy as np
import requests
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
from .utils_new import FileLoader, OllamaConnect
import warnings
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
import math

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("fluency_score")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="fluency_score")

class IndianLanguageFluencyScorer(Strategy):
    def __init__(self, name:str="fluency_score", **kwargs):
        super().__init__(name, kwargs=kwargs)
        self.name__ = name #self.name is a property of the base class, so the naming should be different
        self.gpu_url=os.getenv("GPU_URL")
        self.ex_dir = os.getenv("EXAMPLES_DIR")
        self.dist_file = dflt_vals.dist_file
        self.epsilon = dflt_vals.epsilon

    def run_examples(self):
        if(not FileLoader._check_if_present(__file__, self.ex_dir, f"{self.dist_file}_{dflt_vals.type}.json")):
            examples = FileLoader._load_file_content(__file__, self.ex_dir, strategy_name=self.name__)
            score_dist = {}
            for k, v in examples.items():
                if(isinstance(v, list)):                        
                    for para in v:
                        if k in score_dist:
                            score_dist[k].append(self.get_score(para["agent_response"], type=dflt_vals.type))
                        else:
                            score_dist[k] = [self.get_score(para["agent_response"], dflt_vals.type)]
            FileLoader._save_values(__file__, score_dist, self.ex_dir, f"{self.dist_file}_{dflt_vals.type}.json")
        else:
            score_dist = FileLoader._load_file_content(__file__, self.ex_dir, f"{self.dist_file}_{dflt_vals.type}.json")
        return score_dist

    def get_score(self, text:str, type:str):
        if type == "perplexity":
            response = requests.post(f"{self.gpu_url}/perplexity", params={"text" : text})
            score = json.loads(response.content.decode('utf-8'))["perplexity"]
        else:
            response = requests.post(f"{self.gpu_url}/slor", params={"text" : text})
            score = json.loads(response.content.decode('utf-8'))["SLOR"]
        return score
    
    def save_res_as_img(self, results:dict, path:str):
        for k , v in results.items():
            sns.kdeplot(v, label=k, fill=True)
        plt.title("Perplexity for fluent and non fluent indic language paragraphs.")
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.legend()
        plt.savefig(path)
        plt.clf()
    
    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response:str): #testcase:TestCase, conversation:Conversation):
        score = self.get_score(conversation.agent_response, dflt_vals.type) #agent_response)#conversation.agent_response)
        ex_results = self.run_examples()
        probs = {}
        for k, v in ex_results.items():
            dist = gaussian_kde(v)
            interval = np.linspace(score-self.epsilon, score+self.epsilon, 500)
            dist_int = dist(interval) # kde applied to the interval
            probs[k] = np.trapezoid(dist_int, interval)

        self.save_res_as_img(ex_results, os.path.join(os.path.dirname(__file__), f"{os.getenv('IMAGES_DIR')}/{dflt_vals.type}_dist.png"))
        
        probs_as_lst = list(probs.values())
        # if the differnce is positive the value is closer to fluent dist than non fluent
        log_ratio = math.log(max(probs_as_lst[0], 1e-40)) - math.log(max(probs_as_lst[1], 1e-40))
        final_score = 1 / (1 + math.exp(-log_ratio)) # sigmoid function for the difference in log values
        logger.info(f"Fluency Score: {final_score}") # for : {conversation.agent_response}")
        return round(final_score, 3) , OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), final_score)
    
    # def translate(self, agent_response:str):
    #     return json.loads(requests.post(f"{self.gpu_url}/translate", params={"input_text" : agent_response, "target_language" : "English"}).content.decode('utf-8'))

# fluency = IndianLanguageFluencyScorer()
# fluent = ["आज ऑफिस में दिन काफ़ी लंबा था। सुबह एक मीटिंग थी जो उम्मीद से ज़्यादा चल गई, और उसके बाद लगातार ईमेल्स और कॉल्स में टाइम निकल गया। लंच करने का भी वक़्त नहीं मिला। शाम तक थोड़ा थकान महसूस हुई, लेकिन जब काम पूरा हो गया तो थोड़ा सुकून भी मिला। अब बस घर पहुँचकर आराम करने का मन है।",
#           "पिछले हफ़्ते हम सब दोस्तों ने अचानक प्लान बनाया और पास के कैफ़े चले गए। बहुत दिनों बाद सब मिले थे, तो बातें ख़त्म ही नहीं हो रही थीं। किसी ने कॉफ़ी ली, किसी ने मोमोज़, और सब अपने-अपने कॉलेज के पुराने किस्से सुना रहे थे। वक्त पता ही नहीं चला कब निकल गया। आख़िर में सबने कहा कि अगली बार थोड़ा बड़ा ट्रिप प्लान करेंगे।",
#           "रविवार को घर पर माहौल हमेशा थोड़ा हल्का रहता है। सब लोग देर तक सोते हैं और फिर साथ में नाश्ता करते हैं। माँ आमतौर पर कुछ स्पेशल बनाती हैं — कभी आलू के परांठे, कभी पोहा। उसके बाद पापा न्यूज़ देखते हैं, और हम लोग कभी-कभी मूवी लगा लेते हैं। ये छोटा-सा रूटीन पूरे हफ़्ते की थकान मिटा देता है।",
#           "आज सुबह से ही आसमान में बादल थे, और दोपहर तक तेज़ बारिश शुरू हो गई। सड़कें भीग गईं और हवा में मिट्टी की ख़ुशबू फैल गई। मैंने खिड़की से बाहर देखा तो बच्चे बारिश में खेल रहे थे। बारिश का मौसम मुझे हमेशा थोड़ा रिलैक्स कर देता है — बस एक कप चाय और थोड़ा म्यूज़िक, और सब कुछ परफेक्ट लगता है।",
#           "कभी-कभी लगता है कि हम मोबाइल पर ज़रूरत से ज़्यादा समय बिताने लगे हैं। सुबह उठते ही सबसे पहले नोटिफ़िकेशन चेक करते हैं, और फिर पता ही नहीं चलता कब आधा घंटा निकल गया। सोशल मीडिया अच्छी चीज़ है, लेकिन अगर कंट्रोल में रहे तो ही फ़ायदेमंद है। अब मैं कोशिश करता हूँ कि रात को फोन थोड़ा दूर रखकर सोऊँ।",
#         ]

# non_fluent = ["आज ऑफिस बहुत काम था मैं गया जल्दी लेकिन मीटिंग देर हो गया और खाना नहीं टाइम। बॉस बोलता बहुत काम करो जल्दी जल्दी और मैं थक गया पूरा। फिर ईमेल भेजना था लेकिन इंटरनेट नहीं चल रहा सही तो मैं गुस्सा आया। अब घर जाना बस सोना करना चाहिए मैं।",
#               "हम सब दोस्त गया कैफ़े खाना और बात बहुत करता। कोई कॉफ़ी पीता मैं मोमो खाया बहुत। फोटो लिया सब हँसता बिना वजह। फिर बिल आया बड़ा और सबने देखता एक-दूसरा कौन देगा। टाइम जल्दी गया और सब चला घर देर में।",
#               "रविवार दिन घर में सब लोग देर उठता और माँ बोलती खाना बनाओ कोई नहीं मदद करता। पापा टीवी देखता और मैं मोबाइल खेलना। फिर हम खाना खाया और चाय पीता लेकिन बात नहीं ज़्यादा। दिन गया जल्दी और मैं नींद किया दोपहर।",
#               "सुबह आसमान काला और फिर पानी बहुत गिरा तेज़। सड़क गीला और लोग भागता कार अंदर। मैं खिड़की से देखता बाहर बच्चा कूदता पानी। मैं भी जाना चाहता लेकिन जूते खराब नहीं करना था इसलिए बस देखा।",
#               "आजकल लोग मोबाइल बहुत चलाता दिन रात। सुबह उठते फोन देखना पहले और फिर खाना भूल जाता। मैं भी करता वैसे और बाद में सोचता टाइम गया सब बेकार। सोशल मीडिया अच्छा नहीं जब ज़्यादा करना। मैं कोशिश अब नहीं लेकिन नहीं होता बंद।",
#             ]

# for f in zip(fluent):
#     print(fluency.evaluate(f))
# for f in zip(non_fluent):
#     print(fluency.evaluate(f))
        