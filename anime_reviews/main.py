#!/usr/bin/python3 -OO

'''

This module is the main interface towards our collaborative filtering model. 

Sections:
* Imports
* Default Model
* Driver

'''

###########
# Imports #
###########

import argparse

from misc_utilities import *
from global_values import GPU_IDS

#################
# Default Model #
#################

def train_default_model_linear() -> None:
    from models import LinearColaborativeFilteringModel
    number_of_epochs = 15
    batch_size = 256
    gradient_clip_val = 1.0
    learning_rate = 1e-3
    embedding_size = 100
    regularization_factor = 1
    dropout_probability = 0.5
    LinearColaborativeFilteringModel.train_model(
        gpus=gpu_ids,
        learning_rate=learning_rate,
        number_of_epochs=number_of_epochs,
        batch_size=batch_size,
        gradient_clip_val=gradient_clip_val,
        embedding_size=embedding_size,
        regularization_factor=regularization_factor,
        dropout_probability=dropout_probability,
    )
    return

##########
# Driver #
##########

@debug_on_error
def main() -> None:
    parser = argparse.ArgumentParser(prog='tool', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 9999))
    parser.add_argument('-train-default-model-linear', action='store_true', help='Train the default linear model.')
    parser.add_argument('-hyperparameter-search-llinear', action='store_true', help='Perform several trials of hyperparameter search for the linear model.')
    parser.add_argument('-analyze-hyperparameter-search-results-linear', action='store_true', help=f'Analyze completed hyperparameter search trials so far for the linear model.')
    args = parser.parse_args()
    number_of_args_specified = sum(map(int,map(bool,vars(args).values())))
    if number_of_args_specified == 0:
        parser.print_help()
    elif number_of_args_specified > 1:
        print('Please specify exactly one action.')
    elif args.train_default_model_linear:
        train_default_model_linear()
    elif args.hyperparameter_search_linear:
        from hyperparameter_search import hyperparameter_search
        from models import LinearColaborativeFilteringModel
        hyperparameter_search(LinearColaborativeFilteringModel)
    elif args.analyze_hyperparameter_search_results_linear:
        from hyperparameter_search import  analyze_hyperparameter_search_results
        from models import LinearColaborativeFilteringModel
        analyze_hyperparameter_search_results(LinearColaborativeFilteringModel)
    else:
        raise ValueError('Unexpected args received.')
    return

if __name__ == '__main__':
    main()

