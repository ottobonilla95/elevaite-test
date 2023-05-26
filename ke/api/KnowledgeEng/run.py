import html_util as hu
import html_dwnld as hd
import html_title as ht
import config as config
import os
import nlp_util as nlp

os.system("cls" if os.name == "nt" else "clear")
import warnings
warnings.filterwarnings("ignore")

# run the program
def execute():
    #url = "https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClkBCAS"
    #url = "https://docs.paloaltonetworks.com/globalprotect/9-1/globalprotect-admin/globalprotect-quick-configs/globalprotect-multiple-gateway-configuration"
    url = "https://docs.paloaltonetworks.com/panorama/9-1/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/context-switchfirewall-or-panorama"
    #content = hd.getTextContent(url)
    #tag_file_path = config.clsfy_prdct_path
    #output = nlp.getBestMatch(content, tags_path=tag_file_path)
    #print(output)

    #output = ht.getTitles(url)
    print(ht.getFirstTitle(url)) #Topic, subTopic
    #print(hu.getFileNameFromURL(url)) #Document id

    #print(output)
    

execute()
