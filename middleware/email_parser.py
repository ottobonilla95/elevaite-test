import re
from regex_rules import RegexRules
import sys

class EmailConversationParser:
    
    def get_email_conversations(self, email_content):
        self.email_content = email_content
        email_content_without_header = self.get_email_content_without_header()
        email_content_without_special_chars = self.remove_reply_special_chars(email_content_without_header)
        email_content_without_footers = self.remove_footers(email_content_without_special_chars)
        email_content_paragraphs_list = self.get_paragraphs(email_content_without_footers)
        all_email_conversations = self.get_emails(email_content_paragraphs_list)
        # Remove signatures
        all_email_conversations_with_header = [ self.remove_signature(email) for email in all_email_conversations ]
        all_email_conversations_without_header = [self.remove_conversation_header(conversation) for conversation in all_email_conversations]

        return all_email_conversations_without_header

    def remove_reply_special_chars(self, email_content_without_header):
        conv_lines = email_content_without_header.split("\n")
        conv_without_special_chars = []
        email_regex_rules = RegexRules()
        for line in conv_lines:
            if(re.match(email_regex_rules.email_reply_special_chars, line.strip())):
                repline = re.sub(email_regex_rules.email_reply_special_chars, "", line.strip())
                conv_without_special_chars.append(repline)
            else:
                conv_without_special_chars.append(line)
        return "\n".join(conv_without_special_chars)

    def remove_conversation_header(self, conversation):
        conv_lines = conversation.split("\n")
        conv_without_header = []
        email_regex_rules = RegexRules()
        for line in conv_lines:
            if(re.match(email_regex_rules.email_conversation_header_regex, line.strip()) or 
                    re.match(email_regex_rules.email_seperator_regex, line.strip().lower()) ):
                pass
            else:
                conv_without_header.append(line)
        if(len(conv_without_header) > 0):
            return "\n".join(conv_without_header)
        else:
            return ''
    
    def get_email_content_without_header(self):
        most_recent_email_content = self.email_content.split("\n\n")[0]
        historical_email_content = "\n\n".join(self.email_content.split("\n\n")[1:])
        most_recent_email_without_header = []
        message_id = None
        subject = None
        _from = None
        _email_format = None
        # Remove email header from the most recent email conversation
        for line in most_recent_email_content.split("\n"):
            if(":" in line):
                [key, value] = [line.split(":")[0], ":".join(line.split(":")[1:])]
                if(key == "MessageId"):
                    _email_format = "exchange"
                    message_id = value.strip()
                elif(key == "Subject"):
                    subject = value.strip()
                elif(key == "Sender Email" or key == "From"):
                    _from = value.strip()
                else:
                    pass
            elif(_email_format is None and re.match(RegexRules().email_message_id, line.strip())):
                _email_format = "generic"
                # sometimes the actual content gets appended in the same line with message id. 
                remaining_line_text = re.sub(RegexRules().email_message_id, "", line.strip())
                if (remaining_line_text.strip()):
                    most_recent_email_without_header.append(remaining_line_text)
            else:
                if(re.match(RegexRules().email_seperator_regex, line.strip().lower())):
                    break;
                most_recent_email_without_header.append(line)
        email_content_without_header = "\n".join(most_recent_email_without_header) + "\n\n" + historical_email_content
        return email_content_without_header

    def remove_footers(self, string_email, cosine_distance_threshold=0.9):
        sw = ['is', 'to', 'this', 'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'of', 'in', 'so']
        def cosine(sentence_x, sentence_y):
            try:
                x_set = { w for w in sentence_x.split() if w.lower() not in sw}
                y_set = { w for w in sentence_y.split() if w.lower() not in sw}
                cosine = 0
                # Form a set containing keywords of both strings
                rvector = x_set.union(y_set)
                l1 = []
                l2 = []
                # Creating a vector
                for w in rvector:
                    if(w in x_set): l1.append(1)
                    else: l1.append(0)
                    if(w in y_set): l2.append(1)
                    else: l2.append(0)
                
                c = 0
                # Cosine formula
                for i in range(len(rvector)):
                    c += l1[i]*l2[i]
                    cosine = c / float((sum(l1) * sum(l2)) ** 0.5)
            except Exception:
                cosine = 0

            return(cosine)

        string_footer = """
        This message is private and confidential and is intended solely for the
        addressee. Access to this e-mail by anyone else is unauthorised. If you
        have received this in error you must notify us by replying or contacting
        our local office and then remove it from your system.
        We do not accept any liability for the content of this email or for the
        consequences of any actions taken on the basis of the information
        provided.

        Please consider the environment before printing this email.
        named in the message header. Unless otherwise indicated, it contains
        information that is confidential, privileged and/or exempt from
        disclosure under applicable law. If you have received this message in
        error, please notify the sender of the error and delete the message.
        For more information about how we handle your personal information, please see our privacy policy.

        DISCLAIMER : The content of this email is confidential and intended for the
        recipient specified in message only. It is strictly forbidden to share any
        part of this message with any third party, without a written consent of the
        sender. If you received this message by mistake, please reply to this
        message and follow with its deletion, so that we can ensure such a mistake
        does not occur in the future.
        """

        list_paragraphs = [paragraph.strip() for paragraph in str(string_email).split("\n\n") if not all(char == " " for char in paragraph)]
        list_final_paragraphs = []
        for paragraph_number in range(len(list_paragraphs)):
            paragraph = list_paragraphs[paragraph_number]
            list_lines_email =  re.split(RegexRules().sentence_seperators, paragraph)
            list_lines_footer = re.split(RegexRules().sentence_seperators, string_footer)
            bool_is_footer = False
            for line_email in list_lines_email:
                for line_footer in list_lines_footer:
                    cosine_distance = cosine(line_email.lower(), line_footer.lower())
                    if(cosine_distance > cosine_distance_threshold):
                        bool_is_footer = True

            if(not bool_is_footer):
                list_final_paragraphs.append(paragraph)

        if(len(list_final_paragraphs) == 0):
            list_final_paragraphs = list_paragraphs

        string_final_email = "\n\n".join(list_final_paragraphs)
        return(string_final_email)
    
    def get_paragraphs(self, text):
        list_paragraphs = [
                    paragraph
                    for paragraph in re.split("\n\n|\n[-_=]{2,}\n", text)
                    if not all(char == " " for char in paragraph)
                ]
        return(list_paragraphs)

    def get_emails(self, list_paragraphs):
        list_emails = []
        list_email_indices = [0] + self.get_email_separator(list_paragraphs)
        if(list_email_indices[0] == list_email_indices[1]):
            list_email_indices = list_email_indices[1:]
        for list_index, index in enumerate(list_email_indices):
            if(list_index < len(list_email_indices) - 1):
                list_emails.append(
                    "\n\n".join(list_paragraphs[index : list_email_indices[list_index + 1]]))
            else:
                list_emails.append("\n\n" + list_paragraphs[-1])
        return(list_emails)

    def check_to_from(self, list_first_words):
        # Check if the first words contain the required set of words
        list_first_words = [word.lower() for word in list_first_words]
        list_preset_first_words = [
            word.lower() for word in RegexRules().list_email_separator_first_words]
        number_of_matched_words = len(
            list(set(list_first_words) & set(list_preset_first_words)))
        if(number_of_matched_words > 3):
            return(True)
        else:
            return(False)

    def get_email_separator(self, list_paragraphs):
        list_matched_paragraph_index = []
        for index, paragraph in enumerate(list_paragraphs):
            list_lines = [item for item in paragraph.split("\n")]
            list_first_words = []
            for line in list_lines:
                if (re.match(RegexRules().email_seperator_regex, line.strip().lower())):
                    list_matched_paragraph_index.append(index)
                    break;
                list_first_words.append([word.strip()
                                         for word in line.split(" ")][0])
            list_first_words_cleaned = []
            if(index not in list_matched_paragraph_index):
                for first_word in list_first_words:
                    list_first_words_cleaned.append(
                        "".join(char for char in first_word if char.isalnum()))
                if(self.check_to_from(list_first_words_cleaned)):
                    list_matched_paragraph_index.append(index)

        return(list_matched_paragraph_index)

    def is_signature(self, text):
        """
        Combine all words f the word:
        1. is purely alphabetical with first letter capitalized
        2. is a number
        3. is an email
        """
        list_words = re.split(" |\n", text)
        list_words = [word for word in list_words if word.isalnum()]
        list_words = ["".join(char for char in word if char not in ["(", ")", "$", "[", "]", "#", "!", "*", "^", "%", "+", "-", "_"]) for word in list_words if word != ""]
        number_of_words = len(list_words)
        # print("Number of words: ", number_of_words)
        # Remove email
        list_words = [word for word in list_words if not re.match(RegexRules().email_address, word)]
        # Remove numbers
        list_words = [word for word in list_words if not word.isnumeric()]
        # Remove pure words where first alphabet is capitalized
        list_words = [word for word in list_words if not word[0].isupper()]
        if(number_of_words > 4 and len(list_words)/number_of_words < 0.10):
            return(True)
        else:
            return(False)

    def get_name(self, text):
        list_words = re.split(" |\n", text)
        list_words = [word for word in list_words if word.isalnum()]
        list_words = [word for word in list_words if word != ""]
        list_name = []
        if(len(list_words) < 5):
            for word in list_words:
                if(word[0].isupper()):
                    list_name.append(word)
        return(" ".join(list_name))

    def remove_signature(self, email):
        name = None
        list_paragraphs = self.get_paragraphs(email)
        if(len(list_paragraphs) > 0):
            for i in range(len(list_paragraphs), 0, -1):
                if(self.is_signature(list_paragraphs[i-1])):
                    list_paragraphs = list_paragraphs[:i-1]
                    # Get name
                    # print(list_paragraphs)
                    try:
                        name = self.get_name(list_paragraphs[-1])
                    except IndexError:
                        name = None
                    break
        else:
            pass
        return({
            "email": "\n\n".join(list_paragraphs),
            "name": name
        })

