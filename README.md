
# dataload

A collection of data set loading functions.

## functions

- ```conan```: CONAN (en/fr/it)
- ```mlma_hate```: MLMA_hate_speech (ar/en/fr)
- ```largescale_hate```: largescale-hatespeech (en/tr)
- ```hateval2019```: hateval2019 (en/es)
- ```hasoc2020```: hasoc-2020 (de/en/hi)
- ```en_hate1```: hate-speech-and-offensive-language
- ```en_hate2```: NAACL_SRW_2016
- ```en_hate3```: hate-speech-dataset
- ```en_hate4```: hatespeechtwitter
- ```en_delft```: delft/data/sequenceLabelling/toxic
- ```en_offense19```: OffensEval 2019 (SemEval 2019 - Task 6)
- ```en_offense20```: OffensEval 2020
- ```en_olid```: OLID
- ```en_hatexplain```: HateXplain
- ```en_malignant```: MalignantCommentClassification
- ```en_cad```: ContextualAbuseDataset
- ```en_threat1```: hexis-english-threats
- ```en_spam1```: smsspamcollection
- ```de_germeval```: loader for various versions of the tab-separated germeval format. also: haspeede 2020
- ```de_germeval2021```: germeval 2021
- ```es_hate1```: haternet
- ```es_hate2```: violentometro-online
- ```it_hate1```: Italian Hate Speech Corpus (IHSC)
- ```ru_hate1```: russian-inappropriate-messages
- ```ru_hate2```: Russian Language Toxic Comments
- ```ru_hate3```: RuEthnoHate
- ```fr_hate1```: help_dicrah
- ```ar_hate1```: Aljazeera Deleted Comments
- ```ar_hate2```: Corpus_of_offensive_language_in_Arabic
- ```pt_hate1```: OffComBR
- ```pt_hate2```: Portuguese-Hate-Speech-Dataset
- ```pt_hate3```: ToLD-Br
- ```tr_troff```: troff
- ```ko_hatescore```: hatescore-korean-hate-speech
- ```hi_constraint```: Constraint_AAAI2021
- ```el_offense20```: greek offenseval 2020
- ```id_hate1```: id-hatespeech-detection
- ```id_hate2```: id-multi-label-hate-speech-and-abusive-language-detection
- ```mr_mahahate```: L3Cube-MahaHate
- ```pl_poleval19```: PolEval_2019
- ```vi_vihsd```: vihsd
- ```da_dkhate```: dkhate
- ```nl_dalc```: DALC
- ```wordlist```: loader for wordlists
- ```augmentations```: loader for dataset-specific augmentations
- ```relabel```: loader for re-labeled data
- ```debias_madlibs```: loads eval_datasets from _unintended-ml-bias-analysis_
- ```twint```: loads the output of twint scraper

## install

```pip install git+https://git.sr.ht/~spe/dataload```

## good to know

- ```dataload``` is built into [augment](https://git.sr.ht/~spe/augment), [bpemb](https://git.sr.ht/~spe/bpemb), and [autofit](https://git.sr.ht/~spe/autofit) as well as [autofit2](https://git.sr.ht/~spe/autofit2).
- The paper _Antypas & Camacho-Collados - Robust Hate Speech Detection in Social Media: A Cross-Dataset Empirical Evaluation_ [[arxiv link](https://arxiv.org/abs/2307.01680)] backs up some of our re-labelings and selective use of certain data sets in order to improve data aggregation.

