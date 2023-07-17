
class RegexRules:
    def __init__(self):
        self.dict_regex_account_numbers = {
            "UKB": r"GP-?\d{8}",
            "ONEBILL": r"\b(?:VP-?\d{8}|\d{8}-?ac01)\b",
            "TELEPHONY": r"\b(?:SW|EM|CL|CM|WM|EA|ES|SS)-?\d{8}\b",
            "CONFERENCING_EMEA": r"\b(?:EB-?)(?:\w{5}|\w{3}-?\d{5})\b",
            "PCNBS": r"\d{8}-?ac01",
            "BTNET": r"WM-?\d{8}",
            "IPN": r"CSBT-?\d{5}",
            "CYCLONE": r"\b(?:FO|HO|GO)-?\d{4}\b",
            "RADIANZ": r"(?:503-BA-|BA-)\w*",
            # "CUSTOM_CONTRACT": r,
            "GLOSSI_ATM": r"\b\d{7}-?7001\b",
            "BROADBAND": r"(?:WM|GD)-?\d{8}|CSBT-?\d{5}",
            "GLOSSI_GBSP": r"(?:(?:\w{7}BIL)|(?:00|01)\d{6}|\d{7}A|00\d{6})",
            # "OUK_SAP": r"",
            "INET": r"PS-?\d{7}",
            # "C&SI": r"",
            "ONEPHONE": r"GP00-?\d{6}",
            "HSCN": r"HSCN-\w",
            "AIRTIME": r"[79]\d{8}",
            "TELEWORKER": r"GB-?\d{8}",
            "FEATURENET": r"GB-?\d{8}",
            "ETHERNET": r"GP-?\d{8}",
            "THIRD_PARTY": r"GB-?\d{8}",
            "DISE_MOBILE": r"MC-?\d{8}",
            "RECARE": r"CCTV-?\d{6}|RP-?\d{9}",
            "ITS": r"10002348-?MO\w{3}|PSI\w{3}",
            # "BTBA": r"VP-?\w",
            "MEDIA_AND_BROADCAST": r"MB-?\d{7}",
            "APS_HOSTING": r"ICH-?(UK|2\d{6})",
            # "MSL": r"\D{3}\d{7}",
            "SIP_TRUNKING": r"GP-?\d{8}",
            "VOIP": r"GB-?\d{8}",
            # "INFONET": r"",
            "DIAL_PLUS": r"1\d{9}",
            "WHOLESALE_GENIUS": r"GD-?\d{8}",
            # "TMUK_SAP": r"",
            # "INTERNATIONAL_PCB": r"",
            # "PAYPHONES": r"",
            # "TMUK_AIRTIME": r"",
            # "TIKIT": r"",
            # "B2B": r"",
            # "GLOSSI_CMP": r"NETADV",
            # "ARBOR": r"",
            # "EPICOR": r""
            "CNSP": r"CNSP-?\w{0,}"
            # "DIRECTORIES": r"",
        }

        self.dict_regex_time = {
            "day": r"\b(mon|tue|wed|thu|fri|sat|sun)\b",
            "mon": r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
            "year": r"(^|\s)\b([12]\d{3})\b",
            "date": r"\b(\d{1,2}\/\d{1,2}\/\d{2,4})\b",
            "connectors": r"\b(at|on)\b",
            "time": r"\b(\d{1,2}:\d{2}(:\d{2})?(\s?[a|p]m)?)\b"
        }

        self.regex_special_characters = r"(^|\s)\W{1}($|\s)"

        self.sentence_seperators = "[\.!\?\n]"

        self.regex_paragraph = r"[ -*\W]*"

        self.regex_email = r""

        self.list_email_separator_first_words = ["From", "Sent", "To", "Cc", "BCc", "Subject"]

        self.email_reply_special_chars = "^>\s*"

        self.email_conversation_header_regex = "^(?:From:|To:|Cc:|Subject:|Sent:)"

        self.email_seperator_regex = "^on.*wrote:\s*$"

        self.regex_non_empty_paragraph = r"\S"

        self.regex_order_number = r"(?:(?<=num|no.|id.|ref))[ ]*[1-9]\d{4,}|(?:(?<=number))[ ]*[1-9]\d{4,}|(?:(?<=num.|ref.))[ ]*[1-9]\d{4,}"

        self.bank_account_number = r"(?<=[\s^])(\d{2})-?(\d{2})-?(\d{2})-?(\d{2})(?=\s|$)"

        self.email_address = r"\w+\@\w+\.\w+"

        self.email_message_id = "^<[A-Za-z0-9-_\.@!#$%&'*\+\/=\?\^_`\{\|\}\~;:\(\),\\\[\]]*>"

# print(account_numbers['ONEBILL'])