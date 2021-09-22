#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import os
import shutil
from app.common.utilities import execute_command, error_exit, save_current_state, clear_values
from app.common import definitions, values
from app.tools import db
from app.tools import identifier, merger
from app.tools import generator, differ, emitter, logger

FILE_EXCLUDED_EXTENSIONS = ""
FILE_EXCLUDED_EXTENSIONS_A = ""
FILE_EXCLUDED_EXTENSIONS_B = ""
FILE_DIFF_C = ""
FILE_DIFF_H = ""
FILE_DIFF_ALL = ""
FILE_AST_SCRIPT = ""
FILE_AST_DIFF_ERROR = ""

ported_diff_info = dict()
original_diff_info = dict()
# list of (source, func)
ported_vectors = list()
original_vectors = list()
# list of db.MapEntry
vector_mappings = list() 


def analyse_source_diff(path_a, path_b):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    differ.diff_files(definitions.FILE_DIFF_ALL,
                      definitions.FILE_DIFF_C,
                      definitions.FILE_DIFF_H,
                      definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      definitions.FILE_EXCLUDED_EXTENSIONS,
                      path_a,
                      path_b)

    emitter.sub_sub_title("analysing untracked files")
    untracked_file_list = generator.generate_untracked_file_list(definitions.FILE_EXCLUDED_EXTENSIONS, path_a)
    emitter.sub_sub_title("analysing header files")
    diff_h_file_list = differ.diff_h_files(definitions.FILE_DIFF_H, path_a, untracked_file_list)
    emitter.sub_sub_title("analysing C/CPP source files")
    diff_c_file_list = differ.diff_c_files(definitions.FILE_DIFF_C, path_b, untracked_file_list)
    emitter.sub_sub_title("analysing changed code lines")
    diff_info_c = differ.diff_line(diff_c_file_list, definitions.FILE_TEMP_DIFF)
    diff_info_h = differ.diff_line(diff_h_file_list, definitions.FILE_TEMP_DIFF)
    diff_info = merger.merge_diff_info(diff_info_c, diff_info_h)
    return diff_info


def analyse_ast_diff(path_a, path_b, diff_info):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not diff_info:
        error_exit("no files modified in diff")
    updated_diff_info = differ.diff_ast(diff_info,
                                        path_a,
                                        path_b,
                                        definitions.FILE_AST_SCRIPT)
    return updated_diff_info


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B
    definitions.FILE_ORIG_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/orig-diff-info"
    definitions.FILE_PORT_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/port-diff-info"
    definitions.FILE_ORIG_DIFF = definitions.DIRECTORY_OUTPUT + "/orig-diff"
    definitions.FILE_PORT_DIFF = definitions.DIRECTORY_OUTPUT + "/port-diff"
    definitions.FILE_COMPARISON_RESULT = definitions.DIRECTORY_OUTPUT + "/comparison-result"
    definitions.FILE_PORT_N = definitions.DIRECTORY_OUTPUT + "/n-port"
    definitions.FILE_TRANS_N = definitions.DIRECTORY_OUTPUT + "/n-trans"


def safe_exec(function_def, title, *args):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def segment_code(diff_info, project, out_file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.sub_sub_title("identifying modified definitions")
    identifier.identify_definition_segment(diff_info, project)
    emitter.sub_sub_title("identifying modified segments")
    identifier.identify_code_segment(diff_info, project, out_file_path)


def process_original():
    global original_diff_info, original_vectors
    clear_values(values.Project_A)
    # definitions.FILE_TRAINING_VECTORS = definitions.DIRECTORY_OUTPUT + "/training-vec-orig"
    emitter.sub_title("analysing source diff of Original Patch")
    original_diff_info = analyse_source_diff(values.CONF_PATH_A, values.CONF_PATH_B)
    segment_code(original_diff_info, values.Project_A, definitions.FILE_ORIG_N)
    # TODO: include vars as well
    for source_file, val in values.Project_A.function_list.items():
        precise_source = os.path.relpath(source_file, values.CONF_PATH_A)
        for function_name, _ in val.items():
            original_vectors.append((precise_source, function_name))
    

def process_ported():
    global ported_diff_info, ported_vectors
    clear_values(values.Project_C)
    # definitions.FILE_TRAINING_VECTORS = definitions.DIRECTORY_OUTPUT + "/training-vec-ported"
    emitter.sub_title("analysing source diff of Ported Patch")
    ported_diff_info = analyse_source_diff(values.CONF_PATH_C, values.CONF_PATH_E)
    segment_code(ported_diff_info, values.Project_C, definitions.FILE_PORT_N)
    # TODO: include vars as well
    for source_file, val in values.Project_C.function_list.items():
        precise_source = os.path.relpath(source_file, values.CONF_PATH_C)
        for function_name, _ in val.items():
            ported_vectors.append((precise_source, function_name))


def generate_vector_mappings():
    global vector_mappings
    version_a = values.CONF_VERSION_A
    version_c = values.CONF_VERSION_C
    # match by function/variable names
    # TODO: include variables
    original_funcs = [ f for _ , f in original_vectors ]
    unmatched_vectors = list()
    for source_c, func_c in ported_vectors:
        if func_c not in original_funcs:
            unmatched_vectors.append((source_c, func_c))
    for source_a, func_a in original_vectors:
        for source_c, func_c in ported_vectors:
            if func_a == func_c:
                # found a match, prepare an entry for adding to db
                vec_c_list = [(source_c, func_c)] 
                vec_c_list.extend(unmatched_vectors)
                vector_mappings.append(
                    db.MapEntry(version_a, source_a, func_a, version_c, vec_c_list))
                break


def save_mapping_to_db():
    for map_entry in vector_mappings:
        db.insert_mapping_entry(map_entry)


def clean_up():
    # mark in db that this pair has been trained
    db.mark_pair_as_trained(values.CONF_COMMIT_B, values.CONF_COMMIT_E)


def start():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    try:
        if values.PHASE_SETTING[definitions.PHASE_TRAINING]:
            load_values()
            emitter.title("Training from Evolution History")
            process_original()
            process_ported()
            generate_vector_mappings()
            if not values.ANALYSE_N:
                save_mapping_to_db()
            clean_up()
    except:
        # something wrong happened to this pair, mark it
        db.mark_pair_as_error(values.CONF_COMMIT_B, values.CONF_COMMIT_E)