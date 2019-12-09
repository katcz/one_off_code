#!/usr/bin/python3

"""

Tests for String processsing utilities.

Owner : paul-tqh-nguyen

Created : 11/15/2019

File Name : string_processing_tests.py

File Organization:
* Imports
* Misc. Utilities
* Testing Utilities
* Tests

"""

###########
# Imports #
###########

import unittest
import re
import tqdm
from contextlib import contextmanager
from torch.utils import data
from datetime import datetime
from word2vec_utilities import WORD2VEC_MODEL
from string_processing_utilities import unknown_word_worth_dwimming, normalized_words_from_text_string, PUNCTUATION_SET, timer
from sentiment_analysis import determine_training_and_validation_datasets

###################
# Misc. Utilities #
###################

def identity(args):
    return args

#####################
# Testing Utilities #
#####################

COMMONLY_USED_MISSING_WORD2VEC_WORDS = [
    # stop words
    'a', 'to', 'and', 'of',
]

def questionable_normalized_words_from_text_string(text_string: str) -> bool:
    normalized_words = normalized_words_from_text_string(text_string)
    unknown_words_worth_mentioning = normalized_words
    unknown_words_worth_mentioning = filter(lambda word: word not in COMMONLY_USED_MISSING_WORD2VEC_WORDS, unknown_words_worth_mentioning)
    unknown_words_worth_mentioning = filter(lambda word: unknown_word_worth_dwimming(word), unknown_words_worth_mentioning)
    return list(unknown_words_worth_mentioning)

#########
# Tests #
#########

class testTextStringNormalizationViaData(unittest.TestCase):
    def testTextStringNormalizationViaData(self):
        print()
        training_set, validation_set = determine_training_and_validation_datasets()
        training_generator = data.DataLoader(training_set, batch_size=1, shuffle=False)
        validation_generator = data.DataLoader(validation_set, batch_size=1, shuffle=False)
        latest_failed_string = None
        for generator in (training_generator, validation_generator):
            log_progress = False
            possibly_tqdm = tqdm.tqdm if log_progress else identity
            for iteration_index, (input_batch, _) in possibly_tqdm(enumerate(generator)):
                notes_worth_printing = []
                assert len(input_batch)==1
                sentiment_text = input_batch[0]
                questionable_normalized_words_determination_timing_results = dict()
                def note_questionable_normalized_words_determination_timing_results(time):
                    questionable_normalized_words_determination_timing_results['total_time'] = time
                with timer(exitCallback=note_questionable_normalized_words_determination_timing_results):
                    questionable_normalized_words = questionable_normalized_words_from_text_string(sentiment_text)
                questionable_normalized_words_determination_time = questionable_normalized_words_determination_timing_results['total_time']
                max_tolerable_number_of_seconds_for_processing = 0.01
                if questionable_normalized_words_determination_time > max_tolerable_number_of_seconds_for_processing:
                    notes_worth_printing.append("Processing the following string took {questionable_normalized_words_determination_time} to process:\n{sentiment_text}\n".format(
                        questionable_normalized_words_determination_time=questionable_normalized_words_determination_time,
                        sentiment_text=sentiment_text))
                if len(questionable_normalized_words)!=0:
                    latest_failed_string = sentiment_text
                    notes_worth_printing.append("\nWe encountered these unhandled words: {questionable_normalized_words}".format(questionable_normalized_words=questionable_normalized_words))
                    notes_worth_printing.append("")
                if len(notes_worth_printing) != 0:
                    print()
                    print("==============================================================================================")
                    print("Timestamp: {timestamp}".format(timestamp=datetime.now()))
                    print("Current Iteration: {iteration_index}".format(iteration_index=iteration_index))
                    print("Current Sentence Being Processed:\n{sentiment_text}\n".format(sentiment_text=sentiment_text))
                    for note in notes_worth_printing:
                        print(note)
                    print("==============================================================================================")
                    print()
        self.assertTrue(latest_failed_string is None, msg="We failed to process the following string (among possibly many): \n{bad_string}".format(bad_string=latest_failed_string))

def run_all_tests():
    print()
    print("Running our test suite.")
    print()
    loader = unittest.TestLoader()
    tests = [
        loader.loadTestsFromTestCase(testTextStringNormalizationViaData),
    ]
    suite = unittest.TestSuite(tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    print()
    print("Test run complete.")
    print()

if __name__ == '__main__':
    run_all_tests()
