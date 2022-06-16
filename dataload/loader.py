
import os
import re
import json
import pandas as pd

# data lake
from io import StringIO, BytesIO
from pymongo import MongoClient
import gridfs
DB_ADDR = os.environ.get('DATALAKE_ADDR', '127.0.0.1:27017')
DB_NAME = 'datalake'


# general loading functions

def wordlist(files=None, local=False, silent=True):
    """
    loader for various wordlists
    takes one or more paths as input and outputs the parsed and concatenated data

    arguments:
    files: list of paths (local fs) or names (gridfs)
    local: bool -> default: False
    silent: bool -> default: True
    """
    db = MongoClient(DB_ADDR)
    fs = gridfs.GridFS(db[DB_NAME])
    
    swear_list = []
    for path in files:
        if local == False:
            
            query = {'filename': {'$regex': path+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
        else:
            f = open(path,'r', encoding='utf-8')

        for line in f:
            swear_list.append(line.rstrip())
        
        f.close()
    return list(set(swear_list))

def augmentations(files=None, local=False, silent=True):
    """
    loader for dataset-specific augmentations

    files:
       1. pfad zu backlog.json
       2. path(s): muss dataset_name aus backlog enthalten, der in eine augmentation-uid übersetzt wird, anhand der die daten von gridfs bzw. lokalem fs geladen werden können
    local: bool -> default: False
    silent: bool -> default: True
    """
    AUGS_BASEPATH = 'data/hexis/augmentations'
    db = MongoClient(DB_ADDR)
    fs = gridfs.GridFS(db[DB_NAME])

    """
    TODO: backlog nicht in gridfs speichern -> siehe training.md/augmentation/NEU
    if local == False:
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        f = open(files[0], 'r', encoding='utf-8')
    """
    f = open(files[0], 'r', encoding='utf-8')
    backlog = json.load(f)
    f.close()

    data = []
    for uid, config in backlog.items():
        for path in files[1:]:
            if config['dataset_name'] in path:
                print('%s (%s)' % (config['dataset_name'], uid))

                if local == False:
                    data += germeval([uid+'.txt$'], local=False)
                else:
                    data += germeval([AUGS_BASEPATH+'/'+uid+'.txt'], local=True)
    
    return data

def relabel(files=None, local=False, silent=True):
    """
    loader for files in aggression/re-labeling
    takes one or more paths as input and outputs the parsed and concatenated data
    anm: grundlage ist klasse abuse, die mit einem profanity detector in zwei klassen, profanity und insults, aufgeteilt wurde

    arguments:
    files: list of paths (local fs) or names (gridfs)
    local: bool -> default: False
    silent: bool -> default: True
    """
    db = MongoClient(DB_ADDR)
    fs = gridfs.GridFS(db[DB_NAME])

    data = []
    for path in files:
        if local == False:
            query = {'filename': {'$regex': path+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            data_corr = pd.read_csv(f, delimiter=',', index_col=0)  # index = tweet_id
            f.close()
        else:
            data_corr = pd.read_csv(path, delimiter=',', index_col=0)  # index = tweet_id    

        for i, row in data_corr.iterrows():
            text = row[0].rstrip()
            label_str = row[2]
            
            if text == '':
                if silent == False:
                    print('empty string')
                continue

            post={}
            post['text'] = text
            if label_str == 'PROF':
                post['label'] = 'profanity'
            elif label_str == 'NONE':
                post['label'] = 'insult'  # part of 'abuse' that is not 'profanity', is 'insult'
            else:
                if silent == False:
                    print('LABEL ERROR: %s' % (label_str))
                continue
            
            data.append(post)

    return data

def debias_madlibs(files=None, local=False, silent=True):
    """
    loader for files in unintended-ml-bias-analysis/unintended_ml_bias/eval_datasets
    takes one or more paths as input and outputs the parsed and concatenated data
    classes: BAD, NOT_BAD
    anm: BAD entspricht identity hate

    arguments:
    files: list of paths (local fs) or names (gridfs)
    local: bool -> default: False
    silent: bool -> default: True
    """
    db = MongoClient(DB_ADDR)
    fs = gridfs.GridFS(db[DB_NAME])
    
    data = []
    for path in files:
        if local == False:
            query = {'filename': {'$regex': path+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
        else:
            f = open(path, 'r', encoding='utf-8')
        
        for line in f.readlines()[1:]:
            try:
                i, text, label_str = line.split(',')
            except:
                i, text, label_str = line.split('"')

            post={}
            post['text'] = text
            if label_str == 'NOT_BAD':
                post['label'] = 'normal'
            elif label_str == 'BAD':
                post['label'] = 'hate'
            else:
                if silent == False:
                    print('LABEL ERROR: %s' % (label_str))
                continue
            
            data.append(post)
        f.close()

    return data

def twint(files=None, local=False, silent=True):
    """
    loads the output of twint scraper
    takes one or more paths as input and outputs the parsed and concatenated data
    anm: reads just the text content from column 'tweets'

    arguments:
    files: list of paths (local fs) or names (gridfs)
    local: bool -> default: False
    silent: bool -> default: True
    """
    db = MongoClient(DB_ADDR)
    fs = gridfs.GridFS(db[DB_NAME])

    data = []
    for path in files:
        if local == False:
            query = {'filename': {'$regex': path+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            txts_df = pd.read_csv(f, delimiter=',', index_col=0)
            f.close()
        else:
            txts_df = pd.read_csv(path, delimiter=',', index_col=0) 

        for i, row in txts_df.iterrows():
            if isinstance(row['tweet'], float) or row['tweet'].isnumeric():  # twint scraper produces erroneuos lines sometiems
                continue
            post={}
            post['text'] = row['tweet'].rstrip()
            data.append(post)
        
    return data


# multilingual

def conan(lang, files=None, local=False, silent=True):
    """
    CONAN (en/fr/it)
    collection von hate- und counterspeech beispielen
    15k bsp, gefiltert nach id: IT + zu jeder HS ID jede augmentation nur 1x -> 2502 bsp
    id layout: FR|T1|ST0014|HS0015|CN001238|T1 = Language | HS Type | HS SubTopic | HS ID | CN Count | augmentation type (P1: paraphrase 1 / P2: paraphrase 2 / T1: translation 1)
    anm: returns label als int
    """
    if lang not in ['it', 'fr', 'en']:
        if silent == False:
            print('unknown language code:', str(lang))
        return []
    
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['CONAN/CONAN.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',')
        f.close()
    else:
        if not files:
            files = ['data/multi/en, fr, it/CONAN/CONAN/CONAN.csv']
        df = pd.read_csv(files[0], delimiter=',')

    data = []
    sample_ids = []
    for i, row in df.iterrows():
        post_id = row['cn_id']
        if post_id.startswith(lang.upper()):
            post_id_begin, post_id_end = post_id.split('HS')
            hs_id, _ = post_id_end.split('CN')
            aug_type = post_id_end[-2:]
            sample_id = hs_id + aug_type
            if sample_id in sample_ids:
                continue
            else:
                sample_ids.append(sample_id)

                post = {}
                post['text'] = row['hateSpeech'].rstrip()        
                post['label'] = 1
                data.append(post)

                post = {}
                post['text'] = row['counterSpeech'].rstrip()         
                post['label'] = 0
                data.append(post)
    return data

def mlma_hate(lang, files=None, local=False, silent=True):
    """
    MLMA_hate_speech (ar/en/fr)
    fr: 4014 bsp, exkl. bsp die '…' enthalten -> 2808 bsp
    ar: 4014 bsp, exkl. bsp die '…' enthalten -> 2449 bsp
    classes: sentiment (Abusive, Hateful, Offensive, Disrespectful, Fearful, Normal) + andere: directness,annotator_sentiment,target,group
    """
    if lang not in ['ar', 'fr', 'en']:
        if silent == False:
            print('unknown language code:', str(lang))
        return []

    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['hate_speech_mlma/'+lang.lower()+'_dataset.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',')
        f.close()
    else:
        if not files:
            files = ['data/multi/ar, en, fr/MLMA_hate_speech/hate_speech_mlma/'+lang.lower()+'_dataset.csv']
        df = pd.read_csv(files[0], delimiter=',')

    data = []
    for i, row in df.iterrows():
        label = row['sentiment']
        text = row['tweet'].rstrip()
        if '…' in text:
            continue

        post = {}
        post['text'] = text        
        post['label'] = label
        data.append(post)
    return data

def largescale_hate(lang, files=None, local=False, silent=True):
    """
    largescale-hatespeech (en/tr)
    100k bsp, classes: Normal (0), Offensive (1), Hate (2)
    20k je domain: Gender, Race, Politics, Sports
    anm: returns label als int
    """
    if lang not in ['tr', 'en']:
        if silent == False:
            print('unknown language code:', str(lang))
        return []

    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/multi/en, tr/largescale-hatespeech/hate_speech_dataset-tweets.jsonl',
                    '/multi/en, tr/largescale-hatespeech/hate_speech_dataset.csv']

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter=',', index_col=0)  # index = tweet_id
        f.close()

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/multi/en, tr/largescale-hatespeech/hate_speech_dataset-tweets.jsonl',
                    'data/multi/en, tr/largescale-hatespeech/hate_speech_dataset.csv']
        labels_df = pd.read_csv(files[1], delimiter=',', index_col=0)  # index = tweet_id
        f = open(files[0],'r', encoding='utf-8')
    
    data = []
    count_notfound = 0
    for line in f:
        item = json.loads(line)
        if item['id'] not in labels_df.index:
            if int(item['id_str']) not in labels_df.index:
                count_notfound += 1
                continue
            else:
                tweet_id = int(item['id_str'])
        else:
            tweet_id = item['id']

        lang_id = labels_df.loc[tweet_id].values[0]  # LangID is the first column
        if lang_id != int(lang.lower() == 'en'):  # 0-Turkish, 1-English
            continue
        
        post = {}
        post['text'] = item['full_text'].strip()
        post['label'] = labels_df.loc[tweet_id].values[-1]  # HateLabel is the last column
        data.append(post)
    f.close()
    #print(count_notfound, 'labels not found')
    return data

def hateval2019(lang, files=None, local=False, silent=True):
    """
    hateval2019 (en/es)
    6600 bsp, classes: 0 (non-hate), 1 (hate) -> falls hate: Target Range (0/1), Aggressiveness (0/1)
    anm: returns label als int
    """
    if lang not in ['en', 'es']:
        if silent == False:
            print('unknown language code:', str(lang))
        return []

    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/multi/en, es/hateval2019/hateval2019_'+lang.lower()+'_train.csv',
                    '/multi/en, es/hateval2019/hateval2019_'+lang.lower()+'_dev.csv',
                    '/multi/en, es/hateval2019/hateval2019_'+lang.lower()+'_test.csv']
    else:
        if not files:
            files = ['data/multi/en, es/hateval2019/hateval2019_'+lang.lower()+'_train.csv',
                    'data/multi/en, es/hateval2019/hateval2019_'+lang.lower()+'_dev.csv',
                    'data/multi/en, es/hateval2019/hateval2019_'+lang.lower()+'_test.csv']

    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter=',', index_col=0)
            f.close()
        else:
            df = pd.read_csv(file, delimiter=',', index_col=0)

        for i, row in df.iterrows():
            post = {}
            post['text'] = row['text']
            post['label'] = int(row['HS'])
            data.append(post)
    return data

def hasoc2020(lang, files=None, local=False, silent=True):
    """
    hasoc-2020 (de/en/hi)
    je ca. 3k bsp, classes: task 1 (NOT/HOF), task 2 (NONE/PRFN/OFFN/HATE)
    """
    if lang not in ['de', 'en', 'hi']:
        if silent == False:
            print('unknown language code:', str(lang))
        return []

    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/multi/de, en, hi/hasoc-2020/hasoc_2020_'+lang.lower()+'_train_new.xlsx',
                    '/multi/de, en, hi/hasoc-2020/hasoc_2020_'+lang.lower()+'_test_new.xlsx']
    else:
        if not files:
            files = ['data/multi/de, en, hi/hasoc-2020/hasoc_2020_'+lang.lower()+'_train_new.xlsx',
                    'data/multi/de, en, hi/hasoc-2020/hasoc_2020_'+lang.lower()+'_test_new.xlsx']
    
    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = BytesIO(grid_out.read())
            df = pd.read_excel(f)
            f.close()
        else:
            df = pd.read_excel(file)

        for i, row in df.iterrows():
            label = row['task1']
            text = row['text'].rstrip()
            
            post = {}
            post['text'] = text        
            post['label'] = label
            data.append(post)
    return data


# english

def en_hate1(files=None, local=False, silent=True):
    """
    source: https://github.com/t-davidson/hate-speech-and-offensive-language
    file: labeled_data.csv, len: 24783
    classes: 0 = hate speech, 1 = offensive language, 2 = neither

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/hate-speech-and-offensive-language/data/labeled_data.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/en/hate-speech-and-offensive-language/data/labeled_data.csv']
        f = open(files[0], 'r', encoding='utf-8')
    
    data = []
    for line in f:
        if str(line).startswith(','):  # omit header
            continue
            
        entry = line.split(',')
        text = entry[6].rstrip()

        if text == '':
            if silent == False:
                print('empty string')
            continue

        post = {}
        post['text'] = text
        if entry[5] == '0':
            post['label'] = 'hate_speech'
        elif entry[5] == '1':
            post['label'] = 'offensive_language'
        elif entry[5] == '2':
            post['label'] = 'neither'
        else:
            if silent == False:
                print('LABEL ERROR: %s' % (entry[5]))
            continue

        data.append(post)
    
    f.close()
    return data
    
def en_hate2(files=None, local=False, silent=True):
    """
    https://github.com/zeerakw/hatespeech bzw. https://github.com/amyhemmeter/AutomaticDetectionofHateSpeech
    text: hatespeech.csv, labels: NAACL_SRW_2016.csv, len: 16035
    classes: racism, sexism, none
    anm: die negative class (none) enthält schwierige beispiele (an der grenze zu offensive), die positive classes (racism, sexism) scheinen inkonsistent -> besser ausschließen

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/AutomaticDetectionofHateSpeech/hatespeech.csv',
                    '/en/hatespeech/NAACL_SRW_2016.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts_df = pd.read_csv(f, delimiter=',', index_col=0)
        f.close()

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter=',', index_col=0)  # index = tweet_id
        f.close()
    else:
        if not files:
            files = ['data/en/AutomaticDetectionofHateSpeech/hatespeech.csv',
                    'data/en/hatespeech/NAACL_SRW_2016.csv']
        txts_df = pd.read_csv(files[0], delimiter=',', index_col=0)
        labels_df = pd.read_csv(files[1], delimiter=',', index_col=0)  # index = tweet_id

    data = []
    for i, row in txts_df.iterrows():
        text = row[8].rstrip()
        tweet_id = row[5]
        label_str = labels_df.loc[tweet_id].values[0]

        if label_str=='racism' or label_str=='sexism':  # exclude noisy labels
            continue

        if text == '':
            if silent == False:
                print('empty string')
            continue

        post={}
        post['text'] = text
        post['label'] = label_str

        data.append(post)

    return data

def en_hate3(files=None, local=False, silent=True):
    """
    source: https://github.com/aitor-garcia-p/hate-speech-dataset
    labels: annotations_metadata.csv, text: all_files/*.txt, len: 10943
    classes: noHate, hate

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/hate-speech-dataset/annotations_metadata.csv',
                    '/en/hate-speech-dataset/all_files']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter=',')
        f.close()
    else:
        if not files:
            files = ['data/en/hate-speech-dataset/annotations_metadata.csv',
                    'data/en/hate-speech-dataset/all_files']
        labels_df = pd.read_csv(files[0], delimiter=',')

    data = []
    for i, row in labels_df.iterrows():
        label_str = row[4]

        if local == False:
            text_path = files[1]+'/'+str(row[0])+'.txt'
            query = {'filename': {'$regex': text_path+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            text = f.readline()
            f.close()
        else:
            text_path = files[1]+'/'+str(row[0])+'.txt'
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.readline()

        # ANM: es gibt ein paar dokumente, die zw. 200-300 wörter lang sind -> evtl. hier in einzelne 100-wort-dokumente aufsplitten (ansonsten wird alles über 100 wörter nachher von der padding funktion rausgeworfen)
        
        if text == '':
            if silent == False:
                print('empty string')
            continue

        if label_str not in ['hate', 'noHate']:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue

        post={}
        post['text'] = text
        post['label'] = label_str

        data.append(post)

    return data

def en_hate4(files=None, local=False, silent=True):
    """
    source: https://dataverse.mpi-sws.org/dataset.xhtml?persistentId=doi:10.5072/FK2/ZDTEMN (founta-corpus)
    text: hatespeechtwitter-tweets.csv, labels: hatespeechtwitter.tsv, len: 80000
    classes: normal, abusive, hateful, spam
    anm: abusive entspricht insult + profanity

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/founta-corpus/hatespeechtwitter-tweets.csv',
                    '/en/founta-corpus/hatespeechtwitter.tsv',
                    '/en/re-labelings/founta-corpus-profanity-predicted-edit.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts_df = pd.read_csv(f, delimiter=',', index_col=0)
        f.close()

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter='\t', index_col=0)
        f.close()

        query = {'filename': {'$regex': files[2]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        data_corr = pd.read_csv(f, delimiter=',', index_col=0)  # index = tweet_id
        f.close()
    else:
        if not files:
            files = ['data/en/founta-corpus/hatespeechtwitter-tweets.csv',
                    'data/en/founta-corpus/hatespeechtwitter.tsv',
                    'data/en/re-labelings/founta-corpus-profanity-predicted-edit.csv']
        txts_df = pd.read_csv(files[0], delimiter=',', index_col=0)
        labels_df = pd.read_csv(files[1], delimiter='\t', index_col=0)
        data_corr = pd.read_csv(files[2], delimiter=',', index_col=0)  # index = tweet_id

    data = []
    for i, row in txts_df.iterrows():
        text = row[16].rstrip()
        tweet_id = row[5]
        label_str = labels_df.loc[tweet_id].values[0]

        if not isinstance(label_str, str):
            if isinstance(label_str, float):  # value: nan
                continue
            label_str = label_str[0]  # value in array

        if label_str == 'abusive':  # omit the abusive class, the corrected data is loaded seperately
            continue
        
        if text == '':
            if silent == False:
                print('empty string')
            continue

        if label_str not in ['normal', 'hateful', 'spam']:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue

        post={}
        post['text'] = text        
        post['label'] = label_str

        data.append(post)

    for i, row in data_corr.iterrows():
        text = row[0].rstrip()
        label_str = row[2]

        if text == '':
            if silent == False:
                print('empty string')
            continue

        post={}
        post['text'] = text
        post['label'] = label_str
        data.append(post)

    return data

"""
# not in use, data classes not mapping well to the rest + not updated for fine grained data classes
def en_delft(PATHS):
    #https://github.com/kermitt2/delft/tree/master/data/sequenceLabelling/toxic
    #files: train.csv + test: test.csv, test_labels.csv, len: 1114698
    #PATHS (list): path to texts csv file, path to texts csv file, path to labels csv file
    
    data = []
    train_df = pd.read_csv(PATHS[0], delimiter=',', index_col=0)
    test_df = pd.read_csv(PATHS[1], delimiter=',', index_col=0)
    test_labels_df = pd.read_csv(PATHS[2], delimiter=',', index_col=0)  # index = tweet_id
    
    for i, row in train_df.iterrows():
        post={}
        text = row[0]
        #text = clean_str(text)
        #text = text.replace('\n\n\n', '|LBR|')
        #text = text.replace('\n\n', '|LBR|')
        #text = text.replace('\n', '|LBR|')
        if text == '':
            print('empty string')
            continue

        post['text'] = text
        post['label'] = int(1 in row.values)

        # debug
        #if post['label'] == 1:
        #    print(post)

        data.append(post)
    
    for i, row in test_labels_df.iterrows():
        post={}
        text = test_df.loc[i].values[0]
        #text = clean_str(text)
        if text == '':
            print('empty string')
            continue

        post['text'] = text
        labels = labels = row.values
        post['label'] = int(1 in labels)

        # debug
        #if post['label'] == 1:
        #    print(label)
        #    print(post)

        data.append(post)

    return data
"""

def en_offense19(files=None, local=False, silent=True):
    """
    source: OffensEval 2019 (SemEval 2019 - Task 6)
    files: offenseval-training-v1.tsv, re-lablings: OffensEval-2019-profanity-predicted-edit.csv, total len: 13240
    classes: OFF, NOT
    subtask b: TIN (targeted), UNT (untargeted)
    subtask c: IND (individual), GRP (group), OTH (other)

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/OffensEval-2019/offenseval-training-v1.tsv',
                    '/en/re-labelings/OffensEval-2019-profanity-predicted-edit.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts_df = pd.read_csv(f, delimiter='\t', index_col=0)

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        data_corr = pd.read_csv(f, delimiter=',', index_col=0)  # index = tweet_id
    else:
        if not files:
            files = ['data/en/OffensEval-2019/offenseval-training-v1.tsv',
                    'data/en/re-labelings/OffensEval-2019-profanity-predicted-edit.csv']
        
        txts_df = pd.read_csv(files[0], delimiter='\t', index_col=0)
        data_corr = pd.read_csv(files[1], delimiter=',', index_col=0)  # index = tweet_id
    
    data = []
    for i, row in txts_df.iterrows():
        text = row[0].rstrip()
        label_str = row[1]
        
        if label_str == 'OFF':  # omit the offensive class, the corrected data is loaded seperately
            continue

        if text == '':
            if silent == False:
                print('empty string')
            continue

        post={}
        post['text'] = text
        post['label'] = 'NOT'  # offensive class has been omitted
        data.append(post)

    for i, row in data_corr.iterrows():
        text = row[0].rstrip()
        label_str = row[2]
        
        if text == '':
            if silent == False:
                print('empty string')
            continue

        if label_str not in ['PROF', 'NONE']:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue

        post={}
        post['text'] = text
        post['label'] = label_str
        data.append(post)

    return data

def en_offense20(files=None, local=False, silent=True):
    """
    source: OffensEval 2020
    classes: OFF, NOT
    
    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/SOLID/semeval_test/test_a_tweets.tsv',
                    '/en/SOLID/semeval_test/test_a_labels.csv',
                    '/en/SOLID/extended_test/test_a_tweets_all.tsv',
                    '/en/SOLID/extended_test/test_a_labels_all.csv',
                    '/en/re-labelings/SOLID-testdata-profanity-predicted-edit.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts1_df = pd.read_csv(f, delimiter='\t', index_col=0)

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels1_df = pd.read_csv(f, delimiter=',', index_col=0, header=None)

        query = {'filename': {'$regex': files[2]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts2_df = pd.read_csv(f, delimiter='\t', index_col=0)

        query = {'filename': {'$regex': files[3]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels2_df = pd.read_csv(f, delimiter=',', index_col=0, header=None)

        query = {'filename': {'$regex': files[4]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        data_corr = pd.read_csv(f, delimiter=',', index_col=0)
    else:
        if not files:
            files = ['data/en/OffensEval-2020/SOLID/semeval_test/test_a_tweets.tsv',
                    'data/en/OffensEval-2020/SOLID/semeval_test/test_a_labels.csv',
                    'data/en/OffensEval-2020/SOLID/extended_test/test_a_tweets_all.tsv',
                    'data/en/OffensEval-2020/SOLID/extended_test/test_a_labels_all.csv',
                    'data/en/re-labelings/SOLID-testdata-profanity-predicted-edit.csv']
        
        txts1_df = pd.read_csv(files[0], delimiter='\t', index_col=0)
        labels1_df = pd.read_csv(files[1], delimiter=',', index_col=0, header=None)  # index = tweet_id
        txts2_df = pd.read_csv(files[2], delimiter='\t', index_col=0)
        labels2_df = pd.read_csv(files[3], delimiter=',', index_col=0, header=None)  # index = tweet_id
        data_corr = pd.read_csv(files[4], delimiter=',', index_col=0)  # index = tweet_id

    data = []
    for txts_df, labels_df in [(txts1_df, labels1_df), (txts2_df, labels2_df)]:
        for tweet_id, row in txts_df.iterrows():
            text = row[0].rstrip()
            label_str = labels_df.loc[tweet_id].values[0]
            
            if label_str == 'OFF':  # omit the offensive class, the corrected data is loaded seperately
                continue

            #print(tweet_id, '--', row, '\n')
            if tweet_id == 'id':
                continue

            if text == '':
                if silent == False:
                    print('empty string')
                continue

            post={}
            post['text'] = text
            post['label'] = 'NOT'

            data.append(post)

    for i, row in data_corr.iterrows():
        text = row[0].rstrip()
        label_str = row[2]

        if text == '':
            if silent == False:
                print('empty string')
            continue

        if label_str not in ['PROF', 'NONE']:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue

        post={}
        post['text'] = text
        post['label'] = label_str

        data.append(post)

    return data

def en_olid(files=None, local=False, silent=True):
    """
    OLID
    
    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/OLIDv1.0/testset-levela.tsv',
                    '/en/OLIDv1.0/labels-levela.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts_df = pd.read_csv(f, delimiter='\t', index_col=0)

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter=',', index_col=0, header=None)  # index = tweet_id
    else:
        if not files:
            files = ['data/en/OLIDv1.0/testset-levela.tsv',
                    'data/en/OLIDv1.0/labels-levela.csv']
        
        txts_df = pd.read_csv(files[0], delimiter='\t', index_col=0)
        labels_df = pd.read_csv(files[1], delimiter=',', index_col=0, header=None)  # index = tweet_id

    data = []
    for tweet_id, row in txts_df.iterrows():
        text = row[0].rstrip()
        label_str = labels_df.loc[tweet_id].values[0]

        #print(tweet_id, '--', row, '\n')
        if tweet_id == 'id':
            continue

        if text == '':
            if silent == False:
                print('empty string')
            continue

        if label_str not in ['OFF', 'NOT']:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue

        post={}
        post['text'] = text
        post['label'] = label_str

        data.append(post)

    return data

def en_hatexplain(files=None, local=False, silent=True):
    """
    source: HateXplain
    file: dataset.json
    classes: hatespeech, offensive, normal
    anm: offensive entspricht profanity

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/HateXplain/Data/dataset.json']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/en/HateXplain/HateXplain/Data/dataset.json']
        f = open(files[0], 'r', encoding='utf-8')

    txts_json = json.load(f)
    f.close()
    
    data = []
    for k, item in txts_json.items():
        labels = [item['annotators'][0]['label'], item['annotators'][1]['label'], item['annotators'][2]['label']]
        majority_label = max(set(labels), key = labels.count)
        #print(labels, '--', majority_label, '\n')  # debug

        if majority_label not in ['hatespeech', 'offensive', 'normal']:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue
        
        post={}
        post['text'] = ' '.join(item['post_tokens'])
        post['label'] = majority_label

        data.append(post)

    return data

def en_malignant(files=None, local=False, silent=True):
    """
    MalignantCommentClassification

    files: train.csv, len: 159571
    classes: malignant,highly_malignant,rude,threat,abuse,loathe
    anm:
    - threats sind gut annotiert, aber nur wenige (ca. 400)
    - profanity ('rude') alleine kommt selten vor (ca. 300)
    - malignant/highly_malignant sind eine art überkategorie
        - es gibt aber auch einige (ca. 5000) bsp die nur als 'malignant' annotiert sind

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/en/MalignantCommentClassification/train.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts_df = pd.read_csv(f, delimiter=',', index_col=0)
        f.close()
    else:
        if not files:
            files = ['data/en/MalignantCommentClassification/train.csv']
        txts_df = pd.read_csv(files[0], delimiter=',', index_col=0)

    data = []
    for i, row in txts_df.iterrows():
        text = row[0].rstrip()

        # wikipedia talk pages-specific patterns
        lines = text.split('\n')
        lines_new = []
        for line in lines:
            for s in ['|', '!', '{|', ':', '[', '(']:
                if line.startswith(s):
                    continue

            line = re.sub(' *— Preceding.*$', '', line)
            line = re.sub(' *\(.*\) *$', '', line)
            line = re.sub('\[\[[\w :|]*\]\]|\[\[[^ ]*\]\]|\{\{[^ ]*\}\}', '', line)
            line = re.sub('\[\[.*$', '', line)
            line = re.sub('[^\w]?talk .*[^\w]?$|[^\w]?talk[^\w]? .*$| *talk *$', '', line)

            line = line.replace('Wikipedia:', '').replace('WP:', '').replace('Wikipedia_talk:', '').replace('Image:', '').replace('User talk:', '').replace('contribs/talk', '').replace('++:', '').replace(' WP ', '').replace(' wp ', '').replace('WP:', '')

            lines_new.append(line)
        
        text = '\n'.join(lines_new)

        if text == '':
            if silent == False:
                print('empty string')
            continue

        post={}
        post['text'] = text
        if row[1] == 1:
            post['label'] = 'malignant'
        elif row[2] == 1:
            post['label'] = 'highly_malignant'
        elif row[3] == 1:
            post['label'] = 'rude'
        elif row[4] == 1:
            post['label'] = 'threat'
        elif row[5] == 1:
            post['label'] = 'malignant'  # abuse: class not compatible with abuse in other datasets
        elif row[6] == 1:
            post['label'] = 'loathe'
        else:
            post['label'] = 'normal'

        data.append(post)

    return data

"""
# not in use, data classes not mapping well to the rest
def en_cad(files=None, local=False, silent=True):
    # ContextualAbuseDataset

    # files: cad_v1_1_train.tsv, cad_v1_1_dev.tsv, cad_v1_1_test.tsv, len total: 23417
    # classes: Neutral, PersonDirectedAbuse, IdentityDirectedAbuse, AffiliationDirectedAbuse, CounterSpeech
    # anm:
    # - die 'abuse' klassen scheinen neutrale, insult und abuse/hate zu enthalten
    #   - die neutralen bsp sind im kontext des threads evtl. abusive, der ist aber nicht abgebildet
    #   - evtl. mit profanity clf trennen versuchen
    # - die 'neutral' klasse enthält wiederum sehr rohe/unkultivierte aussagen

    # arguments:
    # files: list of paths (local fs) or names (gridfs) -> default: see below
    # local: bool -> default: False
    # silent: bool -> default: True

    if local == False:
        if not files:
            files = ['ContextualAbuseDataset/data/cad_v1_1_train.tsv',
                    'ContextualAbuseDataset/data/cad_v1_1_dev.tsv',
                    'ContextualAbuseDataset/data/cad_v1_1_test.tsv']

        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        train_df = pd.read_csv(f, delimiter='\t', index_col=0)
        f.close()

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        dev_df = pd.read_csv(f, delimiter='\t', index_col=0)
        f.close()

        query = {'filename': {'$regex': files[2]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        test_df = pd.read_csv(f, delimiter='\t', index_col=0)
        f.close()

    else:
        if not files:
            files = ['data/ContextualAbuseDataset/data/cad_v1_1_train.tsv',
                    'data/ContextualAbuseDataset/data/cad_v1_1_dev.tsv',
                    'data/ContextualAbuseDataset/data/cad_v1_1_test.tsv']
        
        train_df = pd.read_csv(files[0], delimiter='\t', index_col=0)
        dev_df = pd.read_csv(files[0], delimiter='\t', index_col=0)
        test_df = pd.read_csv(files[0], delimiter='\t', index_col=0)

    data = []
    for df in [train_df, dev_tf, test_df]:
        for i, row in df.iterrows():
            text = row[1].rstrip()
            label_str = row[2]
            
            post={}
            post['text'] = text
            post['label'] = label_str
            
            data.append(post)

    return data
"""

def en_threat1(files=None, local=False, silent=True):
    """
    Muschalik - Threatening in English. Appendix

    files: hexis-english-threats.txt, len: 299
    classes: all bsp sind OFFENSE + THREAT

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/hexis/hexis-english-threats/hexis-english-threats.txt']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/hexis/hexis-english-threats/hexis-english-threats.txt']
        f = open(files[0], 'r', encoding='utf-8')

    data = []
    for line in f:
        entry = line.split('\t')
        text = entry[0].rstrip()

        if text == '':
            if silent == False:
                print('empty string')
            continue

        post={}
        post['text'] = text
        post['label'] = entry[1].rstrip()
        post['label2'] = entry[2].rstrip()

        data.append(post)

    f.close()
    return data

def en_spam1(files=None, local=False, silent=True):
    """
    source: smsspamcollection
    classes: spam, ham

    arguments:
    files: list of paths (local fs) or names (gridfs) -> default: see below
    local: bool -> default: False
    silent: bool -> default: True
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['smsspamcollection/SMSSpamCollection.txt']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/spam/smsspamcollection/SMSSpamCollection.txt']
        f = open(files[0], 'r', encoding='utf-8')

    data = []
    for line in f:
        entry = line.split('\t')
        text = entry[1].rstrip()
        label_str = entry[0]
        
        if label_str=='ham':  # we only want the spam messages
            continue

        if text == '':
            if silent == False:
                print('empty string')
            continue

        if len(text.split(' ')) < 4:  # ignore very short messages
            continue

        post = {}
        post['text'] = text
        if label_str=='spam':
            post['label'] = 'spam'
        else:
            if silent == False:
                print('LABEL ERROR: %s' % (label_str))
            continue

        data.append(post)

    f.close()
    return data


# german

def de_germeval(files=None, local=False, silent=True):
    """
    loader for various versions of the tab-separated germeval format
    takes one or more paths as input and outputs the parsed and concatenated data

    arguments:
    files: list of paths (local fs) or names (gridfs)
    local: bool -> default: False
    silent: bool -> default: True
    """
    db = MongoClient(DB_ADDR)
    fs = gridfs.GridFS(db[DB_NAME])

    data = []
    for path in files:
        if local == False:
            query = {'filename': {'$regex': path+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
        else:
            f = open(path,'r', encoding='utf-8')
        
        for line in f:
            post={}
            entry = line.split('\t')
            #print(entry)

            if len(entry) == 2:  # normal germeval format
                post['text'] = entry[0]
                post['label'] = entry[1].rstrip()
            elif len(entry) == 3:
                if entry[0].isnumeric() == True:
                    post['id'] = entry[0]
                    post['text'] = entry[1]
                    post['label'] = entry[2].rstrip()
                else:
                    post['text'] = entry[0]
                    post['label'] = entry[1]
                    post['label2'] = entry[2].rstrip()
            elif len(entry) == 4:
                if entry[0].isnumeric() == True:
                    post['id'] = entry[0]
                    post['text'] = entry[1]
                    post['label'] = entry[2]
                    post['label2'] = entry[3].rstrip()
                else:
                    post['text'] = entry[0]
                    post['label'] = entry[1]
                    post['label2'] = entry[2]
                    post['label3'] = entry[3].rstrip()
            elif len(entry) == 5:
                post['id'] = entry[0]
                post['text'] = entry[1]
                post['label'] = entry[2]
                post['label2'] = entry[3]
                post['label3'] = entry[4].rstrip()
            else:
                if silent == False:
                    print('FORMAT ERROR:', line)
                continue

            data.append(post)
    
        f.close()
    return data

"""
# not in use, toxic language task not mapping well to the rest
def de_germeval2021(paths):
    # germeval 2021 
    # files: GermEval21_TrainData.csv, GermEval21_TestData.csv
    # 4190 bsp, classes: Sub1_Toxic (0/1) - andere: Sub2_Engaging, Sub3_FactClaiming

    data = []
    for path in paths:
        df = pd.read_csv(path, delimiter=',')
        for i, row in df.iterrows():
            post = {}
            post['text'] = row['comment_text'].rstrip()
            post['label'] = int(row['Sub1_Toxic'])
            data.append(post)
    return data
"""

# spanish

def es_hate1(files=None, local=False, silent=True):
    """
    haternet: https://zenodo.org/record/2592149
    6k bsp, classes: 0 (no-offense), 1 (offense)
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/es/HaterNet/labeled_corpus_6K.txt']
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/es/HaterNet/labeled_corpus_6K.txt']
        f = open(files[0], 'r', encoding='utf-8')

    data = []
    for line in f:
        entry = line.split(';||;')
        post = {}
        post['text'] = entry[1].rstrip()
        post['label'] = int(entry[2].rstrip())
        data.append(post)
    return data

def es_hate2(files=None, local=False, silent=True):
    """
    violentometro-online 
    4100 bsp (facebook comments: 1969 bsp + mex-a3t auszug: 793+1145+215=2153 bsp), classes: 0 (no-offense), 1 (offense)
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/es/violentometro-online/clean_comentarios_facebook.csv',
                    '/es/violentometro-online/comentarios1.csv',
                    '/es/violentometro-online/comentarios2.csv',
                    '/es/violentometro-online/comentarios3.csv']
    else:
        if not files:
            files = ['data/es/violentometro-online/clean_comentarios_facebook.csv',
                    'data/es/violentometro-online/comentarios1.csv',
                    'data/es/violentometro-online/comentarios2.csv',
                    'data/es/violentometro-online/comentarios3.csv']

    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter=',')
            f.close()
        else:
            df = pd.read_csv(file, delimiter=',')

        for i, row in df.iterrows():
            if not pd.isna(row['Text']):
                post = {}
                post['text'] = row['Text'].rstrip()
                post['label'] = int(row['Category'])
                data.append(post)
    return data


# italian

def it_hate1(files=None, local=False, silent=True):
    """
    Italian Hate Speech Corpus (IHSC): https://github.com/msang/hate-speech-corpus
    6928 bsp, classes: hs (yes/no), aggressiveness (weak/strong/no), offensiveness (weak/strong/no), irony (yes/no), stereotype (yes/no)
    """

    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/it/Italian Hate Speech Corpus (IHSC)/IHSC-tweets.csv',
                    '/it/Italian Hate Speech Corpus (IHSC)/IHSC_ids.tsv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        txts_df = pd.read_csv(f, delimiter=',', index_col=0)
        f.close()

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter='\t', index_col=0)
        f.close()
    else:
        if not files:
            files = ['data/it/Italian Hate Speech Corpus (IHSC)/IHSC-tweets.csv',
                    'data/it/Italian Hate Speech Corpus (IHSC)/IHSC_ids.tsv']
        txts_df = pd.read_csv(files[0], delimiter=',', index_col=0)
        labels_df = pd.read_csv(files[1], delimiter='\t', index_col=0)

    data = []
    for i, row in txts_df.iterrows():
        text = row[16].rstrip()
        tweet_id = row[5]
        labels = labels_df.loc[tweet_id]
        post={}
        post['text'] = text        
        post['label'] = labels.values[0]
        post['label2'] = labels.values[1]
        post['label3'] = labels.values[2]
        data.append(post)
    return data

# haspeede 2020
# 6839 bsp, classes: non-hate (0), hate (1) - auch vorhanden: stereotype (0/1)
it_hate2 = de_germeval


# russian

def ru_hate1(files=None, local=False, silent=True):
    """
    russian-inappropriate-messages
    umfang (human_labeled): 7064 (train.csv), 937 (test.csv), 839 (val.csv)
    classes (alle floats bis auf human_labeled): inappropriate,offline_crime,online_crime,drugs,gambling,pornography,prostitution,
    slavery,suicide,terrorism,weapons,body_shaming,health_shaming,politics,racism,religion,sexual_minorities,sexism,social_injustice,human_labeled
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/ru/russian-inappropriate-messages/train.csv',
                    '/ru/russian-inappropriate-messages/test.csv',
                    '/ru/russian-inappropriate-messages/val.csv']
    else:
        if not files:
            files = ['data/ru/russian-inappropriate-messages/train.csv',
                    'data/ru/russian-inappropriate-messages/test.csv',
                    'data/ru/russian-inappropriate-messages/val.csv']
    
    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter=',')
            f.close()
        else:
            df = pd.read_csv(file, delimiter=',')

        for i, row in df.iterrows():
            if row['human_labeled'] == 1:
                text = row['text']
                label = int(row['inappropriate'] > 0.0)  # if inappropriate > 0.0 then label=1 else label=0
                post={}
                post['text'] = text        
                post['label'] = label
                data.append(post)
    return data

def ru_hate2(files=None, local=False, silent=True):
    """
    Russian Language Toxic Comments
    27857 bsp, classes: non-toxic (0.0), toxic (1.0)
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/ru/Russian Language Toxic Comments/labeled.csv']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',')
    else:
        if not files:
            files = ['data/ru/Russian Language Toxic Comments/labeled.csv']
        df = pd.read_csv(files[0], delimiter=',')

    data = []
    for i, row in df.iterrows():
        post={}
        post['text'] = row[0].rstrip()        
        post['label'] = int(row[1])
        data.append(post)
    return data

def ru_hate3(files=None, local=False, silent=True):
    """
    RuEthnoHate
    5594 bsp, classes: -1	(negative), 0 (neutral), 1 (positive)
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/ru/RuEthnoHate/RuEthnoHate.json']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/ru/RuEthnoHate/RuEthnoHate.json']
        f = open(files[0], 'r', encoding='utf-8')
    
    texts = json.loads(f.read())
    data = []
    for item in texts:
        post={}
        post['text'] = item['text'].rstrip()        
        post['label'] = int(item['class'])
        data.append(post)
    return data


# french

def fr_hate1(files=None, local=False, silent=True):
    """
    help_dicrah
    4k bsp, classes: N (neutral), S/H/SH (violent/racist), ENG (nicht weiter kategorisiertes englisch), PUB (spam)
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/fr/help_dicrah/data/tweets_labeled_4k_cleaned.csv']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',')
    else:
        if not files:
            files = ['data/fr/help_dicrah/data/tweets_labeled_4k_cleaned.csv']
        df = pd.read_csv(files[0], delimiter=',')

    data = []
    for i, row in df.iterrows():
        label = row['Label']
        text = row['Texte'].rstrip()
        
        if label in ['ENG', 'PUB']:
            continue

        post = {}
        post['text'] = text        
        post['label'] = label
        data.append(post)
    return data


# arabic

def ar_hate1(files=None, local=False, silent=True):
    """
    Aljazeera Deleted Comments
    32k bsp, classes: 0 (clean), -1 (offensive), -2 (obscene)
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/ar/Aljazeera Deleted Comments/AJCommentsClassification-CF.xlsx']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = BytesIO(grid_out.read())  #.decode(encoding='cp1256')
        df = pd.read_excel(f)
    else:
        if not files:
            files = ['data/ar/Aljazeera Deleted Comments/AJCommentsClassification-CF.xlsx']
        df = pd.read_excel(files[0])

    data = []
    for i, row in df.iterrows():
        label = int(row['languagecomment'] != 0)  # if label != 0 -> label = 1
        text = row['body'].rstrip()

        post = {}
        post['text'] = text        
        post['label'] = label
        data.append(post)
    return data

def ar_hate2(files=None, local=False, silent=True):
    """
    Corpus_of_offensive_language_in_Arabic
    15k bsp, classes: N (negative = non-offense), P (positive = offense)
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/ar/Corpus_of_offensive_language_in_Arabic/LabeledDataset.xlsx']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = BytesIO(grid_out.read())
        df = pd.read_excel(f)
    else:
        if not files:
            files = ['data/ar/Corpus_of_offensive_language_in_Arabic/LabeledDataset.xlsx']
        df = pd.read_excel(files[0])

    data = []
    for i, row in df.iterrows():
        if not pd.isna(row['commentText']):
            text = row['commentText'].rstrip()
            if text == '':
                text = row['replies.commentText'].rstrip()
                if text == '':
                    continue
        else:
            text = row['replies.commentText'].rstrip()
            if text == '':
                continue

        labels = [row['annotator1'], row['annotator2'], row['annotator3']]
        label = max(set(labels), key=labels.count)  # most frequent item in list

        post = {}
        post['text'] = text        
        post['label'] = label
        data.append(post)

    return data


# portuguese

def pt_hate1(files=None, local=False, silent=True):
    """
    OffComBR
    2290 bsp, classes: offense (yes), non-offense (no)
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/pt/OffComBR/OffComBR2.csv',
                    '/pt/OffComBR/OffComBR3.csv']
    else:
        if not files:
            files = ['data/pt/OffComBR/OffComBR2.csv',
                    'data/pt/OffComBR/OffComBR3.csv']

    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter=',')
            f.close()
        else:
            df = pd.read_csv(file, delimiter=',')

        for i, row in df.iterrows():
            post = {}
            post['text'] = row['document'].strip()
            post['label'] = int(row['@@class'] == 'yes')
            data.append(post)
    return data

def pt_hate2(files=None, local=False, silent=True):
    """
    Portuguese-Hate-Speech-Dataset
    7479 bsp, classes: hate (1), non-hate (0)
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/pt/Portuguese-Hate-Speech-Dataset/2019-05-28_portuguese_hate_speech_binary_classification.csv']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',')
    else:
        if not files:
            files = ['data/pt/Portuguese-Hate-Speech-Dataset/2019-05-28_portuguese_hate_speech_binary_classification.csv']
        df = pd.read_csv(files[0], delimiter=',')

    data = []
    for i, row in df.iterrows():
        post = {}
        post['text'] = row['text'].strip()
        post['label'] = int(row['hatespeech_comb'])
        data.append(post)
    return data

def pt_hate3(files=None, local=False, silent=True):
    """
    ToLD-Br
    21k bsp, classes: text, homophobia, obscene, insult, racism, misogyny, xenophobia
    Each column has a value (float) from 0 to 3 representing the number of times this example got flagged as toxic
    anm: returns label als int
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/pt/ToLD-Br/ToLD-BR.csv']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',')
    else:
        if not files:
            files = ['data/pt/ToLD-Br/ToLD-Br.csv']
        df = pd.read_csv(files[0], delimiter=',')

    data = []
    for i, row in df.iterrows():
        post = {}
        post['text'] = row['text'].strip()
        post['label'] = int(row['homophobia'] > 1 or row['obscene'] > 1 or row['insult'] > 1 or row['racism'] > 1 or row['misogyny'] > 1 or row['xenophobia'] > 1)
        data.append(post)
    return data


# turkish

def tr_troff(files=None, local=False, silent=True):
    """
    troff
    36k bsp, classes: non-offensive (non), offensive (prof, grp, ind, oth)
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/tr/troff/troff-v1.0.tsv']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter='\t')
    else:
        if not files:
            files = ['data/tr/troff/troff-v1.0.tsv']
        df = pd.read_csv(files[0], delimiter='\t')

    data = []
    for i, row in df.iterrows():
        post = {}
        post['text'] = row['text'].strip()
        post['label'] = row['label'].strip()
        data.append(post)
    return data


# korean

def ko_hatescore(files=None, local=False, silent=True):
    """
    hatescore-korean-hate-speech
    11k bsp, classes: 혐오발언 (= hate speech), Clean
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/ko/hatescore-korean-hate-speech/HateScore.csv']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        df = pd.read_csv(f, delimiter=',', index_col=0)
    else:
        if not files:
            files = ['data/ko/hatescore-korean-hate-speech/HateScore.csv']
        df = pd.read_csv(files[0], delimiter=',', index_col=0)

    data = []
    for i, row in df.iterrows():
        post = {}
        post['text'] = row['comment'].strip()
        post['label'] = row['macrolabel'].strip()
        data.append(post)
    return data


# hindi

def hi_constraint(files=None, local=False, silent=True):
    """
    Constraint_AAAI2021
    8k bsp, classes: non-offensive ('non-hostile'), offensive ('hate', 'offensive'), other ('fake', 'defamation')
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/hi/Constraint_AAAI2021/constraint_Hindi_Train.xlsx',
                    '/hi/Constraint_AAAI2021/Constraint_Hindi_Valid.xlsx',
                    '/hi/Constraint_AAAI2021/Test Set Complete.xlsx']
    else:
        if not files:
            files = ['data/hi/Constraint_AAAI2021/constraint_Hindi_Train.xlsx',
                    'data/hi/Constraint_AAAI2021/Constraint_Hindi_Valid.xlsx',
                    'data/hi/Constraint_AAAI2021/Test Set Complete.xlsx']
    
    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = BytesIO(grid_out.read())
            df = pd.read_excel(f)
            f.close()
        else:
            df = pd.read_excel(file)

        for i, row in df.iterrows():
            post = {}
            post['text'] = row['Post'].strip()        
            post['label'] = row['Labels Set'].strip()
            data.append(post)
    return data


# greek

def el_offense20(files=None, local=False, silent=True):
    """
    greek offenseval 2020
    10k bsp, classes: OFF, NOT
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/el/offenseval2020-greek/offenseval-gr-training-v1/offenseval-gr-training-v1.tsv',
                    '/el/offenseval2020-greek/offenseval-gr-testsetv1/offenseval-gr-test-v1-combined.tsv']
    else:
        if not files:
            files = ['data/el/offenseval2020-greek/offenseval-gr-training-v1/offenseval-gr-training-v1.tsv',
                    'data/el/offenseval2020-greek/offenseval-gr-testsetv1/offenseval-gr-test-v1-combined.tsv']

    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter='\t', index_col=0)
            f.close()
        else:
            df = pd.read_csv(file, delimiter='\t', index_col=0)

        for i, row in df.iterrows():
            post = {}
            post['text'] = row['tweet'].strip()
            post['label'] = row['subtask_a'].strip()
            data.append(post)
    return data


# indonesian

def id_hate1(files=None, local=False, silent=True):
    """
    id-hatespeech-detection
    700 bsp, classes: HS, Non_HS
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/id/id-hatespeech-detection/IDHSD_RIO_unbalanced_713_2017.txt']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode(encoding='cp1252'))
        df = pd.read_csv(f, delimiter='\t', index_col=False)
    else:
        if not files:
            files = ['data/id/id-hatespeech-detection/IDHSD_RIO_unbalanced_713_2017.txt']
        df = pd.read_csv(files[0], delimiter='\t', index_col=False)

    data = []
    for i, row in df.iterrows():
        post = {}
        post['text'] = row['Tweet'].strip()
        post['label'] = row['Label'].strip()
        data.append(post)
    return data

def id_hate2(files=None, local=False, silent=True):
    """
    id-multi-label-hate-speech-and-abusive-language-detection
    13k bsp, classes: 0, 1
    columns: Tweet,HS,Abusive,HS_Individual,HS_Group,HS_Religion,HS_Race,HS_Physical,HS_Gender,HS_Other,HS_Weak,HS_Moderate,HS_Strong
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/id/id-multi-label-hate-speech-and-abusive-language-detection/re_dataset.csv']
        
        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode(encoding='cp1252'))
        df = pd.read_csv(f, delimiter=',', index_col=False)
    else:
        if not files:
            files = ['data/id/id-multi-label-hate-speech-and-abusive-language-detection/re_dataset.csv']
        df = pd.read_csv(files[0], delimiter=',', index_col=False)

    data = []
    for i, row in df.iterrows():
        post = {}
        post['text'] = row['Tweet'].strip()
        post['label'] = int(row['HS'] == 1 or row['Abusive'] == 1)
        data.append(post)
    return data


# maharati

def mr_mahahate(files=None, local=False, silent=True):
    """
    L3Cube-MahaHate
    37k bsp, classes: HOF, NOT
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/mr/L3Cube-MahaHate/2-class/hate_bin_train.xlsx',
                    '/mr/L3Cube-MahaHate/2-class/hate_bin_valid.xlsx',
                    '/mr/L3Cube-MahaHate/2-class/hate_bin_test.xlsx']
    else:
        if not files:
            files = ['data/mr/L3Cube-MahaHate/2-class/hate_bin_train.xlsx',
                    'data/mr/L3Cube-MahaHate/2-class/hate_bin_valid.xlsx',
                    'data/mr/L3Cube-MahaHate/2-class/hate_bin_test.xlsx']
    
    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = BytesIO(grid_out.read())
            df = pd.read_excel(f)
            f.close()
        else:
            df = pd.read_excel(file)

        for i, row in df.iterrows():
            post = {}
            post['text'] = row['text'].strip()        
            post['label'] = row['label'].strip()
            data.append(post)
    return data


# polish

def pl_poleval19(files=None, local=False, silent=True):
    """
    PolEval_2019
    11k bsp, classes: 0, 1 + multiclass: 0 (non-harmful), 1 (cyberbullying), 2 (hate-speech)
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/pl/PolEval_2019/data/training_set_texts.txt',
                    '/pl/PolEval_2019/data/training_set_tags.txt']

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        texts = f.readlines()
        f.close()

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels = f.readlines()
        f.close()
    else:
        if not files:
            files = ['data/pl/PolEval_2019/data/training_set_texts.txt',
                    'data/pl/PolEval_2019/data/training_set_tags.txt']
        with open(files[0], 'r') as f:
            texts = f.readlines()
        with open(files[1], 'r') as f:
            labels = f.readlines()
    
    data = []
    for text, label in zip(texts, labels):
        post = {}
        post['text'] = text.strip().replace('@anonymized_account', '@USER')
        post['label'] = label.strip()
        data.append(post)
    return data


# vietnamese

def vi_vihsd(files=None, local=False, silent=True):
    """
    vihsd
    33k bsp, classes: 0 (clean), 1 (offensive), 2 (hate)
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/vi/vihsd/data/train.csv',
                    '/vi/vihsd/data/dev.csv',
                    '/vi/vihsd/data/test.csv']
    else:
        if not files:
            files = ['data/vi/vihsd/data/train.csv',
                    'data/vi/vihsd/data/dev.csv',
                    'data/vi/vihsd/data/test.csv']

    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter=',', index_col=False)
            f.close()
        else:
            df = pd.read_csv(file, delimiter=',', index_col=False)

        for i, row in df.iterrows():
            if pd.isna(row['free_text']):
                continue
            post = {}
            post['text'] = row['free_text'].strip()
            post['label'] = row['label_id']
            data.append(post)
    return data


# danish

def da_dkhate(files=None, local=False, silent=True):
    """
    dkhate
    3k bsp, classes: OFF, NOT
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/da/dkhate/oe20da_data/offenseval-da-training-v1.tsv',
                    '/da/dkhate/oe20da_data/offenseval-da-test-v1.tsv']
    else:
        if not files:
            files = ['data/da/dkhate/oe20da_data/offenseval-da-training-v1.tsv',
                    'data/da/dkhate/oe20da_data/offenseval-da-test-v1.tsv']

    data = []
    for file in files:
        if local == False:
            query = {'filename': {'$regex': file+'$'}} 
            grid_out = fs.find_one(query)
            f = StringIO(grid_out.read().decode())
            df = pd.read_csv(f, delimiter='\t', index_col=False)
            f.close()
        else:
            df = pd.read_csv(file, delimiter='\t', index_col=False)

        for i, row in df.iterrows():
            if pd.isna(row['tweet']):
                continue
            post = {}
            post['text'] = row['tweet'].strip()
            post['label'] = row['subtask_a'].strip()
            data.append(post)
    return data


# dutch

def nl_dalc(files=None, local=False, silent=True):
    """
    DALC
    11k bsp, classes: NOT, EXPLICIT, IMPLICIT
    columns: id,abusive,offensive_aggregated,target_aggregated,abusive_offensive_not,offense_a1,offense_a2,offense_a3,offense_a4,target_a1,target_a2,target_a3,target_a4
    """
    if local == False:
        db = MongoClient(DB_ADDR)
        fs = gridfs.GridFS(db[DB_NAME])
        if not files:
            files = ['/nl/DALC/v2.0/data/DALC-2_train-tweets.jsonl',
                    '/nl/DALC/v2.0/data/DALC-2_train.csv']

        query = {'filename': {'$regex': files[1]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
        labels_df = pd.read_csv(f, delimiter=',', index_col=0)  # index = tweet_id
        f.close()

        query = {'filename': {'$regex': files[0]+'$'}} 
        grid_out = fs.find_one(query)
        f = StringIO(grid_out.read().decode())
    else:
        if not files:
            files = ['data/nl/DALC/v2.0/data/DALC-2_train-tweets.jsonl',
                    'data/nl/DALC/v2.0/data/DALC-2_train.csv']
        labels_df = pd.read_csv(files[1], delimiter=',', index_col=0)  # index = tweet_id
        f = open(files[0],'r', encoding='utf-8')
    
    data = []
    count_notfound = 0
    for line in f:
        item = json.loads(line)
        if item['id'] not in labels_df.index:
            if int(item['id_str']) not in labels_df.index:
                count_notfound += 1
                continue
            else:
                tweet_id = int(item['id_str'])
        else:
            tweet_id = item['id']
        
        post = {}
        post['text'] = item['full_text'].strip()
        post['label'] = int(labels_df.loc[tweet_id].values[0] != 'NOT' or labels_df.loc[tweet_id].values[1] != 'NOT')  # col 0 = abusive, col 1 = offensive_aggregated
        data.append(post)
    f.close()
    #print(count_notfound, 'labels not found')
    return data


# backwards compatibility for autofit v1

hate1 = en_hate1
hate2 = en_hate2
hate3 = en_hate3
hate4 = en_hate4
offense19 = en_offense19
offense20 = en_offense20
olid = en_olid
hatexplain = en_hatexplain
malignant = en_malignant
threat1 = en_threat1
spam1 = en_spam1
germeval = de_germeval
