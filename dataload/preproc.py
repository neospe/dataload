
import re
import html
import unicodedata


url_pattern = re.compile('((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
user_pattern = re.compile('@\S+')
number_pattern = re.compile('([0-9]+?)')
ip_pattern = re.compile('\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')


MAPPING_BINARYCLASS = {
    # map label string to class index
    # none: 0
    # offense: 1
    0: 0,
    1: 1,
    '0': 0,
    '1': 1,
    'neither': 0,
    'normal': 0,
    'none': 0,
    'NONE': 0,
    'NOT': 0,
    'noHate': 0,
    'OTHER': 0,
    'other': 0,
    'spam': 1,
    'profanity': 1,
    'PROFANITY': 1,
    'PROF': 1,
    'offensive_language': 1,
    'offensive': 1,
    'OFF': 1,
    'OFFENSE': 1,
    'insult': 1,
    'INSULT': 1,
    'malignant': 1,
    'rude': 1,
    'ABUSE': 1,
    'hate': 1,
    'hatespeech': 1,
    'hateful': 1,
    'hate_speech': 1,
    'THREAT': 1,
    'highly_malignant': 1,
    'threat': 1,
    'loathe': 1
}

MAPPING_MULTICLASS = {
    # map label string to class index
    # none: 0
    # spam: 1
    # profanity: 2
    # insult: 3
    # hate: 4
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    'neither': 0,
    'normal': 0,
    'none': 0,
    'NONE': 0,
    'NOT': 0,
    'NOTHING': 0,
    'noHate': 0,
    'OTHER': 0,
    'other': 0,
    'spam': 1,
    'profanity': 2,
    'PROFANITY': 2,
    'PROF': 2,
    'offensive_language': 2,
    'offensive': 2,
    'OFF': 2,
    'OFFENSE': 2,
    'insult': 3,
    'INSULT': 3,
    'malignant': 3,
    'rude': 3,
    'ABUSE': 4,
    'hate': 4,
    'hatespeech': 4,
    'hateful': 4,
    'hate_speech': 4,
    'THREAT': 4,
    'highly_malignant': 4,
    'threat': 4,
    'loathe': 4
}


def clean_str_mini(string):
    """minimal but stronger normalization for testing"""
    string = html.unescape(string)
    string = url_pattern.sub('', string)
    string = user_pattern.sub('', string)
    string = number_pattern.sub('', string)
    string = string.replace('|LBR|', '')
    string = string.replace('\n', '')
    string = string.replace('   ', ' ').replace('  ', ' ').strip()
    string = re.sub('[^A-Za-z ]+', '', string)  # remove all non-alphabet characters
    return string


def clean_str(string, placeholder=True):
    #string_orig = string

    string = html.unescape(string)  # translate html entities to utf8 (e.g. '&amp'->'&')
    string = ip_pattern.sub('', string)  # remove ip addresses

    if placeholder == True:
        string = url_pattern.sub('|URL|', string)
        string = user_pattern.sub('|USER|', string)
        string = number_pattern.sub('|NUMBER|', string)
    else:
        string = url_pattern.sub('', string)
        string = user_pattern.sub('', string)
        string = number_pattern.sub('', string)

    # transform emoticons to corresponding emoji
    string = string.replace(' :)', ' 🙂 ').replace(' :-)', ' 🙂 ').replace(' ;)', ' 😉 ').replace(' ;-)', ' 😉 ').replace(' :D', ' 😁 ').replace(' :-D', ' 😁 ').replace(' :(', ' 🙁 ').replace(' :-(', ' 🙁 ').replace(' :/', ' 😕 ').replace(' :-/', ' 😕 ').replace(' 8)', ' 😎 ').replace(' 8-)', ' 😎 ').replace(' X)', ' 😵 ').replace(' X-)', ' 😵 ').replace(' :-P', ' 😋 ').replace(' :P', ' 😋 ').replace(' <3', ' ❤️ ').replace(' :\'(', ' 😢 ').replace(' :\'-(', ' 😢 ')
    
    ######################
    # ONLY FOR TRAINING

    # ENGLISH
    if placeholder == True:
        string = string.replace('<user>', '|USER|').replace('<number>', '|NUMBER|').replace('<date>', '|NUMBER|').replace('<time>', '|NUMBER|')
    else:
        string = string.replace('<user>', '').replace('<number>', '').replace('<date>', '').replace('<time>', '')
    string = string.replace('<censored>', '🤬').replace('<url>', '').replace('<percent>', '%').replace('<money>', '💵').replace('<tong>', '😋').replace('<annoyed>', '😒').replace('<sad>', '😔').replace('<happy>', '😄').replace('<wink>', '😉')

    # DEUTSCH
    # tokenize utf-8 codepoints
    string = string.replace('>', '> ')
    string = string.replace('<', ' <')
    # transform emoji as utf-8 codepoints (e.g. '<U+0001F937>') to binary representation
    # fixes germeval2019GoldLabelsSubtask12.txt, germeval2019_training_subtask12.txt
    try:
        callback = lambda pat: chr(int('000'+pat.group(0)[6:-1], 16))
        string = re.sub(r'<\S+>', callback, string)
        #if re.match(r'<\S+>', string):  # debug
        #    print(string)
    except:
        pass

    # WHITESPACE HANDLING
    string = re.sub(r'[\r\n]+', ' |LBR| ', string)
    string = string.replace(' |LBR|  |LBR| ', ' |LBR| ')
    string = string.replace('"""', '')
    string = string.replace('""', '')
    if placeholder == False:
        string = string.replace(' |LBR| ', ' ')
    string = string.replace('   ', ' ').replace('  ', ' ').strip()

    # UNICODE NORMALIZATITON (MOSTLY FOR SCRAPED DATA)
    # remove control characters, bidirectional classes
    # cf. https://www.unicode.org/reports/tr44/#BC_Values_Table
    bidi_classes = ['', 'L', 'EN', 'ES', 'ET', 'CS', 'WS', 'ON']
    string = ''.join(c for c in string if not unicodedata.category(c).startswith('C') and unicodedata.bidirectional(c) in bidi_classes)
    # remove braille: 0x2800-0x28FF, arabic: 0x0600-0x06FF, diacritics: 0x0300-0x036F
    # cf. https://www.ssec.wisc.edu/~tomw/java/unicode.html
    string = re.sub('[\u2800-\u28FF]|[\u0600-\u06FF]|[\u0300-\u036F]', '', string)

    # debug
    #if string_orig != string:
    #    print(string_orig)
    #    print(string, '\n')

    return string
