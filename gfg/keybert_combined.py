import os, shutil
import numpy as np
from keybert import KeyBERT
from keyphrase_vectorizers import KeyphraseCountVectorizer
from transformers import BertTokenizer, BertModel
import torch
import subprocess

domain = "esg_financing"
data_path = r"D:\scrapy\scrapy_with_googlesearch\gfg"


def read_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
    return data


def extract_combined_docs(data_path, domain):
    data_path = os.path.join(data_path, f"{domain}_basic")
    docs_list = []
    for file in os.listdir(data_path):
        if file.endswith("_text.txt"):
            docs_list.append(read_txt(os.path.join(data_path, file)))

    print("Data Collected")

    doc = ""
    for doc_val in docs_list:
        doc = doc + doc_val + "\n"

    kw_model = KeyBERT()
    print("Model Loaded")
    seed_kw = " ".join(domain.split("_"))
    print(f"Seed keywords: {seed_kw}")
    keywords = kw_model.extract_keywords(doc, vectorizer=KeyphraseCountVectorizer(), top_n=15, use_mmr=True, diversity=0.3,
                                         seed_keywords=[seed_kw])
    print(keywords)

    keywords_name = [x[0] for x in keywords]
    phrases_path = f"D:\scrapy\scrapy_with_googlesearch\gfg\{domain}_keywords.txt"

    with open(phrases_path, "w", encoding="utf-8") as f:
        for item in keywords_name:
            f.write(f"{item}\n")

    return phrases_path


def extract_and_match_individual_docs(data_path, phrases_path):
    os.makedirs(os.path.join(data_path, f"{domain}_similar_urls"), mode=777, exist_ok=True)
    data_path = os.path.join(data_path, f"{domain}_extended")
    os.makedirs(data_path, mode=777, exist_ok=True)
    kw_model = KeyBERT()
    checkpoint = "bert-base-uncased"
    tokenizer = BertTokenizer.from_pretrained(checkpoint)
    bert_model = BertModel.from_pretrained(checkpoint)
    print("Loaded KeyBERT")
    docs_list = []
    docs_name = []
    for file in os.listdir(data_path):
        if file.endswith("_text.txt"):
            docs_name.append(file)
            docs_list.append(read_txt(os.path.join(data_path, file)))

    kwords_list = []
    for doc in docs_list:
        keywords = kw_model.extract_keywords(doc, vectorizer=KeyphraseCountVectorizer(), top_n=15, use_mmr=True,
                                             diversity=0.3)
        kwords_list.append(keywords)
        if len(kwords_list) % 10 == 0:
            print(f"{len(kwords_list)} done for keybert.")

    with open(phrases_path, "r", encoding="utf-8") as f:
        extracted_phrases = f.readlines()

    extracted_phrases = [item[:-1] for item in extracted_phrases]

    similarity_list = [torch.tensor(1) for _ in range(len(docs_list))]
    print(similarity_list)
    avg_emb_out = []
    count = 0
    for kwords in kwords_list:
        emb_outputs = []
        for kw, score in kwords:
            with torch.no_grad():
                encoded_input = tokenizer(kw, padding=True, truncation=True, return_tensors='pt')
                output = bert_model(**encoded_input)
                emb_outputs.append(output.last_hidden_state.squeeze(0).mean(dim=0))
        #print(len(emb_outputs))
        try:
            avg_emb_out.append(torch.stack(emb_outputs, dim=0).mean(dim=0))
        except:
            similarity_list[count] = torch.tensor(0)
            print(similarity_list[count])
        count += 1
        if count % 10 == 0:
            print(f"{count} done.")
    print("Calculated Embeddings of Each Document.")

    emb_extracted = []
    for kw in extracted_phrases:
        with torch.no_grad():
            encoded_input = tokenizer(kw, padding=True, truncation=True, return_tensors='pt')
            output = bert_model(**encoded_input)
            emb_extracted.append(output.last_hidden_state.squeeze(0).mean(dim=0))
    reference_emb = torch.stack(emb_extracted, dim=0).mean(dim=0)
    print("Calculated Embeddings of Main Keywords")
    co_sim = torch.nn.CosineSimilarity(dim=0, eps=1e-08)
    count = 0
    for emb_val in avg_emb_out:
        print(similarity_list[count])
        if similarity_list[count] == torch.tensor(0):
            #similarity_list[count] = similarity_list[count].data[0]
            count += 1
            continue
        similarity_list[count] = co_sim(reference_emb, emb_val)
        count += 1

    if similarity_list[-1] == torch.tensor(1):
        similarity_list = similarity_list[:-1]
    indexes = np.argsort(similarity_list)
    print("Filtered files in order")
    f = open("ordered_txt_files.txt", "a", encoding="utf8")
    count = 0
    for ind in list(reversed(indexes)):
        if similarity_list[ind].item() < torch.tensor(0.9).item():
            print(f"Final Count of Similar Files: {count}")
            break
        else:
            count += 1
            print(docs_name[ind])
            f.write(f"{docs_name[ind]}\n")
            try:
                shutil.copy(os.path.join(data_path, docs_name[ind]), os.path.join(r"D:\scrapy\scrapy_with_googlesearch\gfg\esg_financing_similar_urls", docs_name[ind]))
            except:
                pass


phrases_path = extract_combined_docs(data_path, domain)
print("------------Keywords Collected------------")
subprocess.run("scrapy crawl extract", shell=True)
print("------------Scraped More Data-------------")
phrases_path = r"D:\scrapy\scrapy_with_googlesearch\gfg\esg_financing_keywords.txt"
print(phrases_path)
extract_and_match_individual_docs(data_path, phrases_path)
print("---------Calculated Similarity score for individual docs----------")
