
# dataload

A collection of data set loading functions.

## functions

| Code              | Dataset Name                                      | Languages        |
|------------------|------------------------------------------------|----------------|
| `conan`         | CONAN                                          | en/fr/it      |
| `mlma_hate`     | MLMA_hate_speech                               | ar/en/fr      |
| `largescale_hate` | largescale-hatespeech                        | en/tr         |
| `hateval2019`   | hateval2019                                    | en/es         |
| `hasoc2020`     | hasoc-2020                                     | de/en/hi      |
| `en_hate1`      | hate-speech-and-offensive-language             | en            |
| `en_hate2`      | NAACL_SRW_2016                                 | en            |
| `en_hate3`      | hate-speech-dataset                           | en            |
| `en_hate4`      | hatespeechtwitter                             | en            |
| `en_delft`      | delft/data/sequenceLabelling/toxic            | en            |
| `en_offense19`  | OffensEval 2019 (SemEval 2019 - Task 6)       | en            |
| `en_offense20`  | OffensEval 2020                               | en            |
| `en_olid`      | OLID                                          | en            |
| `en_hatexplain` | HateXplain                                    | en            |
| `en_malignant`  | MalignantCommentClassification               | en            |
| `en_cad`        | ContextualAbuseDataset                       | en            |
| `en_threat1`    | hexis-english-threats                        | en            |
| `en_spam1`      | smsspamcollection                            | en            |
| `de_germeval`   | loader for various versions of the tab-separated germeval format. also: haspeede 2020 (it) | de/it         |
| `de_germeval2021` | germeval 2021                             | de            |
| `es_hate1`      | haternet                                      | es            |
| `es_hate2`      | violentometro-online                         | es            |
| `it_hate1`      | Italian Hate Speech Corpus (IHSC)            | it            |
| `ru_hate1`      | russian-inappropriate-messages               | ru            |
| `ru_hate2`      | Russian Language Toxic Comments              | ru            |
| `ru_hate3`      | RuEthnoHate                                  | ru            |
| `fr_hate1`      | help_dicrah                                  | fr            |
| `ar_hate1`      | Aljazeera Deleted Comments                   | ar            |
| `ar_hate2`      | Corpus_of_offensive_language_in_Arabic      | ar            |
| `pt_hate1`      | OffComBR                                     | pt            |
| `pt_hate2`      | Portuguese-Hate-Speech-Dataset              | pt            |
| `pt_hate3`      | ToLD-Br                                      | pt            |
| `tr_troff`      | troff                                       | tr            |
| `ko_hatescore`  | hatescore-korean-hate-speech                | ko            |
| `hi_constraint` | Constraint_AAAI2021                         | hi            |
| `el_offense20`  | greek offenseval 2020                       | el            |
| `id_hate1`      | id-hatespeech-detection                     | id            |
| `id_hate2`      | id-multi-label-hate-speech-and-abusive-language-detection | id          |
| `mr_mahahate`   | L3Cube-MahaHate                              | mr            |
| `pl_poleval19`  | PolEval_2019                                 | pl            |
| `vi_vihsd`      | vihsd                                       | vi            |
| `da_dkhate`     | dkhate                                      | da            |
| `nl_dalc`       | DALC                                        | nl            |
| `wordlist`      | loader for wordlists                         | -             |
| `augmentations` | loader for dataset-specific augmentations    | -             |
| `relabel`       | loader for re-labeled data                   | -             |
| `debias_madlibs` | loads eval_datasets from _unintended-ml-bias-analysis_ | -             |
| `twint`         | loads the output of twint scraper           | -             |

## install

`pip install git+https://github.com/neospe/dataload`

## good to know

- `dataload` is built into [augment](https://github.com/neospe/augment), [bpemb](https://github.com/neospe/bpemb), and [autofit](https://github.com/neospe/autofit) as well as [autofit2](https://github.com/neospe/autofit2).
- The paper _Antypas & Camacho-Collados - Robust Hate Speech Detection in Social Media: A Cross-Dataset Empirical Evaluation_ [[arxiv link](https://arxiv.org/abs/2307.01680)] backs up some of our re-labelings and selective use of certain data sets in order to improve data aggregation.

