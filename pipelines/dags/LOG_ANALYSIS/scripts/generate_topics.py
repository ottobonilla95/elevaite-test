from airflow.models import Variable
import json
from typing import List, Dict, Tuple
load_group_logs_file = Variable.get('load_group_logs_file', 'default_load_group_logs_file')

class LogParser:
    def __init__(self, k_prefix=3, similarity_threshold=0.5, client=None, max_words=70):
        self.k_prefix = k_prefix
        self.similarity_threshold = similarity_threshold
        self.groups = {}
        self.template_memory = []
        self.client = client
        self.ground_truth = {}
        self.num_logs = 0
        self.max_words = max_words
        
    def get_group(self, token_length, prefix):
        if token_length not in self.groups:
            self.groups[token_length] = {}
        if prefix not in self.groups[token_length]:
            self.groups[token_length][prefix] = []
        return self.groups[token_length][prefix]
        
    def load_log_file(self, file_path: str, num_prefix: int = 5) -> List[Tuple[str, str, str]]:
        processed_logs = []
        with open(file_path, 'r') as file:
            logs = file.readlines()
            for log in logs:
                self.num_logs += 1
                parts = log.split(' ', num_prefix)
                if len(parts) > num_prefix:
                    datetime = ' '.join(parts[:num_prefix-1])
                    switch_id = parts[num_prefix-1]
                    log_entry = parts[num_prefix]
                    processed_logs.append((datetime, switch_id, log_entry.strip()))
        return processed_logs

    def _limit_words(self, log_entries):
        limited_logs = []
        total_words = 0
        for log in log_entries:
            word_count = len(log.split())
            if total_words + word_count > self.max_words:
                break
            limited_logs.append(log)
            total_words += word_count
        return limited_logs, total_words
        
    def tokenize(self, log):
        return [re.sub(r'\d+', '*', token) for token in log.split()]

    def calculate_similarity(self, tokens1, tokens2):
        set1, set2 = set(tokens1), set(tokens2)
        if len(set1) == 0 or len(set2) == 0:
            return 0 
        common_tokens = set1.intersection(set2)
        return len(common_tokens) / len(set1.union(set2))

    def process_log(self, log, datetime, switch_id):
        tokens = self.tokenize(log)
        token_length = len(tokens)
        matched_template = self.search_template_memory(log, token_length)
        if matched_template:
            return
    
        prefix = tuple(tokens[:self.k_prefix])
        group = self.get_group(token_length, prefix)
    
        found_group = False
        for g in group:
            if self.calculate_similarity(g['example'], tokens) > self.similarity_threshold:
                g['logs'].append((datetime, switch_id, log))
                found_group = True
                break
    
        if not found_group:
            group.append({'example': tokens, 'logs': [(datetime, switch_id, log)]})

    def search_template_memory(self, log, token_length):
        possible_templates = [t for t in self.template_memory if len(t.split()) <= token_length]
        for template in possible_templates:
            if re.match(template, log):
                return template
        return None

    def add_to_template_memory(self, template):
        regex_template = re.sub(r'<\*>', '(.*?)', template)
        self.template_memory.append(regex_template)

    def _call_llm_api(self, logs):
        log_entries = [log[2] for log in logs]
        limited_log_entries, total_words = self._limit_words(log_entries)
        print("Input_tokens here : ", total_words)
        input_data = ' '.join(limited_log_entries)
        
        json_data = {
                    "args": [f"""<|start_header_id|>system<|end_header_id|>
                                You are a helpful assistant to extract template string from the log entries.
                                <|eot_id|>
                                <|start_header_id|>user<|end_header_id|>
                                Please answer the following
                                <|prompt|>
                                        ### Instruction ###
                                        You will be provided with a list of logs. You must identify and abstract
                                        all the dynamic variables in logs with "<*>" and output ONE static log
                                        template that matches all the logs. Print ONLY ONE input logs’ template
                                        delimited by backticks. NO description in output is needed. The template
                                        needs to be exactly correct to be matched to the templates so that we can
                                        use it for template matching without unnecessary puntuations or letters.
                                        ### Standardizing LLM Response by Input and Output Example ###
                                        
                                        Example Input 1
                                        Log List: ["try to connected to host: 172.16.254.1, finished.", "try to connected to host: 173.16.254.2, finished."]
                                        Example Output 1
                                        `try to connected to host: <*>, finished.`
                                        
                                        Example Input 2
                                        Log List: ["OMN-LabStock-15 swlogd SES AAA INFO: Login by centreon_ssh_admin_v2 from 10.172.6.1 through SSH Success [in LoginAaaSession::handleLoginResult()]", "OMN-LabStock-15 swlogd SES AAA INFO: Login by centreon_ssh_admin_v2 from 10.172.6.1 through SSH Success [in LoginAaaSession::handleLoginResult()]"]
                                        Example Output 2
                                        `OMN-LabStock-15 swlogd SES AAA INFO: Login by centreon_ssh_admin_v2 from <*> through SSH Success [in LoginAaaSession::handleLoginResult()]`
                                        
                                        Example Input 3
                                        Log List: ["OMN-LabStock-15 sshd[551] Received keyboard-interactive/pam for centreon_ssh_admin_v2 from 10.172.6.1 port 21577 ssh2", "OMN-LabStock-15 sshd[7731] Received keyboard-interactive/pam for centreon_ssh_admin_v2 from 10.172.6.1 port 50385 ssh2"]
                                        Example Output 3
                                        `OMN-LabStock-15 sshd[<*>] Received keyboard-interactive/pam for centreon_ssh_admin_v2 from <*> port <*> ssh2`
                                      
                                        Example Input 4
                                        Log List: ["OMN-LabStock-15 sshd[589] Disconnected from user centreon_ssh_admin_v2 10.172.6.1 port 21577", "OMN-LabStock-15 sshd[7768] Disconnected from user centreon_ssh_admin_v2 10.172.6.1 port 50385"]
                                        Example Output 4
                                        `OMN-LabStock-15 sshd[<*>] Disconnected from user centreon_ssh_admin_v2 <*> port <*>`
                                        
                                        Example Input 5
                                        Log List: ["OMN-LabStock-15 swlogd svcCmm mBIND INFO: smgrIsisTransitSvc@126 Service for isid 2121 is found", "OMN-LabStock-15 swlogd svcCmm mBIND INFO: smgrIsisTransitSvc@126 Service for isid 2117 is found"]
                                        Example Output 5
                                        `OMN-LabStock-15 swlogd svcCmm mBIND INFO: smgrIsisTransitSvc@126 Service for isid <*> is found`
                                        
                                        Example Input 6
                                        Log List: ["sshd[551] Received keyboard-interactive/pam for centreon_ssh_admin_v2 from 10.172.6.1 port 21577 ssh2"]
                                        Example Output 6
                                        `sshd[<*>] Received keyboard-interactive/pam for centreon_ssh_admin_v2 from <*> port <*> ssh2`
                                        
                                        ### Retrieval-Augmented Log Parsing ###
                                        Log List: 
                                {input_data}
                                <|prompt|>
                                <|eot_id|>
                                <|start_header_id|>assistant<|end_header_id|>
                            """],
                    "kwargs": {
                    "max_new_tokens": 8000,
                    "return_full_text": False,
                    "temperature": 0.01,
                    "do_sample": False,
                    }
                }

        try:
            username = "admin"
            password = "HtEgv1PsExDxaRMllBioFj7PnJUDl4dU"
            auth = HTTPBasicAuth(username, password)
            response = requests.post('https://elevaite-prodmodelapi.iopex.ai/inference/3/infer', json=json_data, auth=auth, verify=False)
            if response.status_code == 200:
                data = response.json()
                template = data.get('result', '')[0].get('generated_text', '')
                print("Template : ", template)
                return template
            else:
                print(f"API call failed with status code {response.status_code}")
                return ""
        except Exception as e:
            print(f"Failed to call local LLM API: {e}")
            return ""

    def group_logs(self, log_tuples):
        for datetime, switch_id, log in log_tuples:
            self.process_log(log, datetime, switch_id)

    def parse_logs_with_llm(self):
        for length, prefix_groups in self.groups.items():
            for prefix, groups in prefix_groups.items():
                for group in groups:
                    log_list = group['logs']
                    template = self._call_llm_api(log_list)
                    if template:
                        group['template'] = template

    def _generate_topic_with_llm(self, logs):
        log_entries = [log[2] for log in logs]
        limited_log_entries, total_words = self._limit_words(log_entries)
        print("Input Log Group tokens :", total_words)
        input_data = ' '.join(limited_log_entries)

        json_data = {
                "args": [f"""<|start_header_id|>system<|end_header_id|>
                        You are a helpful assistant to generate topics for log entries.
                            ### Instruction ###
                            You will be provided with a list of logs. Please generate a short topic
                            that summarizes what these logs are about in simple words.
                            Output ONLY the topic within backticks, NO description needed.
                            Give me example logs as a follow-up.
                            ### Example ###
                            Log List: ["Error connecting to database.", "Database connection timed out."]
                            Topic: `Database Connection Issues`, Example Logs: ["Error Connecting to database."]
                            ### Logs ###
                        <|eot_id|><|start_header_id|>user<|end_header_id|>
                        
                        <|context|>
                        
                        {input_data}
                        
                        <|context|>
                        <|start_header_id|>assistant<|end_header_id|>
                    """],
                "kwargs": {
                "max_new_tokens": 8000,
                "return_full_text": False,
                "temperature": 0.01,
                "do_sample": False,
                }
            }
        
        try:
            username = "admin"
            password = "HtEgv1PsExDxaRMllBioFj7PnJUDl4dU"
            auth = HTTPBasicAuth(username, password)
            response = requests.post('https://elevaite-prodmodelapi.iopex.ai/inference/3/infer', json=json_data, auth=auth, verify=False)
            if response.status_code == 200:
                data = response.json()
                topic = data.get('result', '')[0].get('generated_text', '')
                print("Topic : ", topic)
                return topic
            else:
                print(f"API call failed with status code {response.status_code}")
                return ""
        except Exception as e:
            print(f"Failed to call local LLM API: {e}")
            return ""

    def generate_topics(self):
        for length, prefix_groups in self.groups.items():
            for prefix, groups in prefix_groups.items():
                for group in groups:
                    log_list = group['logs']
                    topic = self._generate_topic_with_llm(log_list)
                    if topic:
                        group['topic'] = topic

    def extract_variables(self):
        extracted_data = []
        for length, prefix_groups in self.groups.items():
            for prefix, groups in prefix_groups.items():
                for group in groups:
                    template = group.get('template', '').replace('`', '').strip()
                    template = template.replace('[', '\[').replace(']', '\]').replace('(', '\(').replace(')', '\)')
                    regex_template = template.replace('<*>', '(.*?)')
                    for datetime, switch_id, log in group['logs']:
                        if '.' not in datetime:
                            datetime += '.000'
                        extracted_variables = re.match(regex_template, log)
                        if extracted_variables:
                            extracted_data.append({
                                'log_datetime': datetime,
                                'switch_id': switch_id,
                                'raw_log_message': log,
                                'log_template': template,
                                'log_label': group.get('topic', ''),
                                'log_variables': extracted_variables.groups()
                            })
                        else:
                            extracted_data.append({
                                'log_datetime': datetime,
                                'switch_id': switch_id,
                                'raw_log_message': log,
                                'log_template': template,
                                'log_label': group.get('topic', ''),
                                'log_variables': 'None'
                            })
        return extracted_data

def generate_topics(input_path: str, output_path: str):
    with open(input_path, 'r') as f:
        groups = json.load(f)
    
    parser = LogParser()
    parser.groups = groups    
    parser.generate_topics()
    
    with open(output_path, 'w') as f:
        json.dump(parser.groups, f)
    
    return output_path

generated_topics = generate_topics(load_group_logs_file, "topics.json")
Variable.set('generated_topics', generated_topics)