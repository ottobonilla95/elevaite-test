import json
import re
class PostProcessor:
    @staticmethod
    def filter_json(content):
        filtered_message = ""
        i = 0
        for m in content:
            if m == "{":
                i = 1
            if i:
                filtered_message += m
            if m == "}":
                i = 0
        return filtered_message

    @staticmethod
    def find_numbers(content):
        nums =  re.findall(r'\d+', content)
        nums = [int(i) for i in nums]
        return nums
