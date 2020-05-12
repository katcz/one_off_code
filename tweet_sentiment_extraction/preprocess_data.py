#!/usr/bin/python3
'#!/usr/bin/python3 -OO'

'''
'''

# @todo fill this in
# @todo verify all the imports are used here and elsewhere

###########
# Imports #
###########

import re
import spacy
import string
import unicodedata
import tqdm
import pandas as pd
import multiprocessing as mp
import concurrent.futures
from typing import Tuple, List, Callable
from spacy.tokenizer import Tokenizer

from misc_utilities import *

import torchtext

###########
# Globals #
###########

tqdm.tqdm.pandas()

def initialize_tokenizer() -> Callable:
    nlp = spacy.load('en')
    prefix_re = re.compile(r'''^['''+re.escape(string.punctuation)+r''']''')
    suffix_re = re.compile(r'''['''+re.escape(string.punctuation)+r''']$''')
    infix_re = re.compile(r'''['''+re.escape(string.punctuation)+r''']''')
    simple_url_re = re.compile(r'''^https?://''')
    nlp.tokenizer = Tokenizer(nlp.vocab,
                              prefix_search=prefix_re.search,
                              suffix_search=suffix_re.search,
                              infix_finditer=infix_re.finditer,
                              token_match=simple_url_re.match)
    tokenizer = lambda input_string: [t.text for t in nlp(input_string)]
    return tokenizer
TOKENIZER = initialize_tokenizer()

TRAINING_DATA_CSV_FILE = './data/train.csv'
PREPROCESSED_TRAINING_DATA_JSON_FILE = './data/preprocessed_train.json'

PREPROCESS_TEXT_IN_PARALLEL = False

#############################
# Sanity Checking Utilities #
#############################

def selected_text_position_validity(preprocessed_input_string: str, preprocessed_selected_text: str) -> Tuple[bool, bool]:
    preprocessed_selected_text_match = next(re.finditer(re.escape(preprocessed_selected_text), preprocessed_input_string))
    preprocessed_selected_text_start_position, preprocessed_selected_text_end_position = (preprocessed_selected_text_match.start(), preprocessed_selected_text_match.end())
    selected_text_starts_in_middle_of_word = False
    if preprocessed_selected_text_start_position > 0:
        selected_text_starts_in_middle_of_word = preprocessed_input_string[preprocessed_selected_text_start_position-1].isalnum()
    selected_text_ends_in_middle_of_word = False
    if preprocessed_selected_text_end_position<len(preprocessed_input_string):
        selected_text_ends_in_middle_of_word = preprocessed_input_string[preprocessed_selected_text_end_position].isalnum()
    return selected_text_starts_in_middle_of_word, selected_text_ends_in_middle_of_word

def sanity_check_training_data_json_file() -> bool:
    if __debug__:
        import json
        with open(PREPROCESSED_TRAINING_DATA_JSON_FILE, 'r') as json_file_handle:
            for row_text in tqdm.tqdm(json_file_handle.readlines()):
                row_data = json.loads(row_text)
                if row_data['textID'] != 'c2c5b285b9':
                    continue
                original_text = row_data['text']
                selected_text = row_data['selected_text']
                token_index_to_position_info_map = row_data['token_index_to_position_info_map']
                numericalized_selected_text = row_data['numericalized_selected_text']
                selected_token_indices = [token_index for token_index, is_selected in enumerate(numericalized_selected_text) if is_selected == '1']
                reconstructed_selected_text = reconstruct_selected_text_from_token_indices(selected_token_indices, original_text, token_index_to_position_info_map)
                preprocessed_input_string, _ = preprocess_tweet(original_text)
                preprocessed_selected_text, _ = preprocess_tweet(selected_text)
                selected_text_is_bogus = any(selected_text_position_validity(preprocessed_input_string, preprocessed_selected_text))
                assert (selected_text_is_bogus or reconstructed_selected_text.lower() == selected_text.lower()), f'\nReconstructed {repr(reconstructed_selected_text)}\nas opposed to {repr(selected_text)}\nfrom          {repr(original_text)}'
    return True

############################
# Interpretation Utilities #
############################

def reconstruct_selected_text_from_token_indices(token_indices: List[int], original_text: str, token_index_to_position_info_map: dict) -> str:
    assert token_indices == sorted(token_indices)
    selected_text_substrings: List[str] = []
    previous_end_position = None
    for token_index in token_indices:
        token_position_data = token_index_to_position_info_map[str(token_index)]
        token_original_start_position = token_position_data['token_original_start_position']
        token_original_end_position = token_position_data['token_original_end_position']
        selected_text_substring = original_text[token_original_start_position:token_original_end_position]
        assert selected_text_substring == token_position_data['original_token']
        if previous_end_position is not None:
            selected_text_substrings.append(original_text[previous_end_position:token_original_start_position])
        selected_text_substrings.append(selected_text_substring)
        previous_end_position = token_original_end_position
    selected_text = ''.join(selected_text_substrings)
    return selected_text

###########################
# Preprocessing Utilities #
###########################

def pervasively_replace(input_string: str, old: str, new: str) -> str:
    while old in input_string:
        input_string = input_string.replace(old, new)
    return input_string

def normalize_string_white_space(input_string: str) -> str:
    normalized_input_string = input_string
    normalized_input_string = pervasively_replace(normalized_input_string, '\t', ' ')
    normalized_input_string = pervasively_replace(normalized_input_string, '\n', ' ')
    normalized_input_string = pervasively_replace(normalized_input_string, '  ',' ')
    normalized_input_string = normalized_input_string.strip()
    return normalized_input_string

def preprocess_token(token: str) -> str:
    print('\n'*3)
    preprocessed_token = token
    print(f"preprocessed_token {repr(preprocessed_token)}")
    preprocessed_token = unicodedata.normalize('NFKD', preprocessed_token).encode('ascii', 'ignore').decode('utf-8')
    print(f"preprocessed_token {repr(preprocessed_token)}")
    preprocessed_token = preprocessed_token.lower()
    assert len(token) == len(preprocessed_token)
    print(f"token {repr(token)}")
    print(f"preprocessed_token {repr(preprocessed_token)}")
    assert len(set(string.punctuation).union(set(preprocessed_token))) == 0
    assert ' ' not in preprocessed_token
    return preprocessed_token

@trace
def preprocess_tweet(input_string: str) -> Tuple[str, List[dict]]:
    current_input_string_position = 0
    token_index_to_position_info_map = {}
    normalized_input_string = normalize_string_white_space(input_string)
    input_string_tokens = TOKENIZER(normalized_input_string)
    preprocessed_tokens = eager_map(preprocess_token, input_string_tokens)
    for token_index, (token, preprocessed_token) in enumerate(zip(input_string_tokens, preprocessed_tokens)):
        print(f"(token_index, preprocessed_token) {repr((token_index, preprocessed_token))}")
        for _ in range(len(input_string)):
            if input_string[current_input_string_position] != token[0]:
                current_input_string_position +=1
            else:
                break
        token_start = current_input_string_position
        current_input_string_position += len(token)
        token_end = current_input_string_position
        assert token[0] == input_string[token_start]
        assert token[-1] == input_string[token_end-1]
        assert current_input_string_position <= len(input_string)
        token_index_to_position_info_map[token_index] = {'token_original_start_position': token_start, 'token_original_end_position': token_end, 'original_token': token, 'preprocessed_token': preprocessed_token}
    preprocessed_input_string = ' '.join(preprocessed_tokens)
    return (preprocessed_input_string, token_index_to_position_info_map)

@trace
def numericalize_selected_text(preprocessed_input_string: str, selected_text: str) -> str:
    assert isinstance(preprocessed_input_string, str)
    assert isinstance(selected_text, str)
    preprocessed_selected_text, _ = preprocess_tweet(selected_text)
    if __debug__:
        selected_text_starts_in_middle_of_word, selected_text_ends_in_middle_of_word = selected_text_position_validity(preprocessed_input_string, preprocessed_selected_text)
    assert preprocessed_selected_text in preprocessed_input_string
    preprocessed_input_string_tokens = TOKENIZER(preprocessed_input_string)
    preprocessed_selected_text_match = next(re.finditer(re.escape(preprocessed_selected_text), preprocessed_input_string))
    preprocessed_selected_text_start_position, preprocessed_selected_text_end_position = (preprocessed_selected_text_match.start(), preprocessed_selected_text_match.end())
    assert preprocessed_input_string[preprocessed_selected_text_start_position:preprocessed_selected_text_end_position] == preprocessed_selected_text
    current_sentence_position = 0
    numericalized_text = [0]*len(preprocessed_input_string_tokens)
    for preprocessed_token_index, preprocessed_input_string_token in enumerate(preprocessed_input_string_tokens):
        print(f"(preprocessed_token_index, preprocessed_input_string_token) {repr((preprocessed_token_index, preprocessed_input_string_token))}")
        if current_sentence_position == preprocessed_selected_text_start_position:
            assert current_sentence_position == preprocessed_selected_text_start_position or selected_text_starts_in_middle_of_word
            numericalized_text[preprocessed_token_index] = 1
        elif current_sentence_position > preprocessed_selected_text_start_position:
            assert numericalized_text[preprocessed_token_index-1]==1 or selected_text_starts_in_middle_of_word
            numericalized_text[preprocessed_token_index] = 1
        current_sentence_position += len(preprocessed_input_string_token)
        if current_sentence_position >= preprocessed_selected_text_end_position:
            print(f"preprocessed_input_string_token {repr(preprocessed_input_string_token)}")
            print(f"list(zip(range(999), preprocessed_input_string_tokens, numericalized_text)) {repr(list(zip(range(999), preprocessed_input_string_tokens, numericalized_text)))}")
            assert current_sentence_position == preprocessed_selected_text_end_position or selected_text_ends_in_middle_of_word
            assert numericalized_text[preprocessed_token_index] == 1 or selected_text_starts_in_middle_of_word
            break
        if current_sentence_position<len(preprocessed_input_string):
            if preprocessed_input_string[current_sentence_position] == ' ':
                current_sentence_position += 1
    assert len(list(uniq(numericalized_text))) <= 3
    numericalized_text_as_string = ''.join(map(str, numericalized_text))
    assert len(numericalized_text_as_string) == len(preprocessed_input_string_tokens)
    return numericalized_text_as_string

###############
# Main Driver #
###############

def preprocess_data() -> None:
    training_data_df = pd.read_csv(TRAINING_DATA_CSV_FILE)
    training_data_df = training_data_df[training_data_df.textID == 'c2c5b285b9']
    training_data_df[['text', 'selected_text']] = training_data_df[['text', 'selected_text']].fillna(value='')
    if PREPROCESS_TEXT_IN_PARALLEL:
        with concurrent.futures.ProcessPoolExecutor(mp.cpu_count()) as pool:
            text_series_preprocessed = pd.Series(pool.map(preprocess_tweet, training_data_df.text, chunksize=1000))
    else:
        text_series_preprocessed = training_data_df.text.progress_map(preprocess_tweet)
    preprocessed_input_string_series = text_series_preprocessed.progress_map(lambda pair: pair[0])
    token_index_to_position_info_map_series = text_series_preprocessed.progress_map(lambda pair: pair[1])
    assert all(preprocessed_input_string_series.progress_map(lambda x: isinstance(x, str)))
    assert all(token_index_to_position_info_map_series.progress_map(lambda x: isinstance(x, dict)))
    training_data_df['preprocessed_input_string'] = preprocessed_input_string_series
    training_data_df['token_index_to_position_info_map'] = token_index_to_position_info_map_series
    numericalized_selected_text_series = training_data_df[['preprocessed_input_string', 'selected_text']].progress_apply(lambda row: numericalize_selected_text(row[0], row[1]), axis=1)
    assert isinstance(numericalized_selected_text_series, pd.Series)
    training_data_df['numericalized_selected_text'] = numericalized_selected_text_series
    print(f'''{len(training_data_df[training_data_df.numericalized_selected_text.map(lambda x: 0 if x=='' else int(x)) == 0])} out of {len(training_data_df)} '''
          '''unhandled cases likely due to selected text starting or ending within a word.''')
    training_data_df = training_data_df[training_data_df.numericalized_selected_text.str.contains('1')]
    training_data_df.to_json(PREPROCESSED_TRAINING_DATA_JSON_FILE, orient='records', lines=True)
    assert sanity_check_training_data_json_file()
    return

if __name__ == '__main__':
    preprocess_data()
