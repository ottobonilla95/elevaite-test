import config as cfg


dat_content = {
    cfg.summary_key : "N" ,
    cfg.doctype_key : "TS-Guide",
    cfg.docid_key : "documentID",
    cfg.product_key : "Panorama",
    cfg.version_key : "None",
    cfg.topic_key : "None",
    cfg.subtopic_key : "None",
    cfg.url_key : "None",
    cfg.source_key : "Public",
    cfg.text_key : "None"
}


def create_data(content:str, weburl, title, documentId):
    dat_content.update({cfg.text_key:content})
    dat_content.update({cfg.url_key:weburl})
    dat_content.update({cfg.topic_key:title})
    dat_content.update({cfg.subtopic_key:title})
    dat_content.update({cfg.docid_key:documentId})
    return dat_content