#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time, sys
from common.Utilities import execute_command, error_exit, save_current_state, load_state
from common import Definitions, Values
from ast import Vector, Parser
from tools import Logger, Emitter, Detector, Writer, Generator, Reader

clone_list = dict()


def generate_target_vectors():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("Generating vector files for all functions in Target")
    # Generator.generate_vectors("*\.h", Definitions.FILE_FIND_RESULT, Values.Project_C)
    Generator.generate_vectors("*\.c", Definitions.FILE_FIND_RESULT, Values.Project_C)


def find_clones():
    global clone_list
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("Finding clone functions in Target")
    clone_list = Detector.find_clone()
    # Values.c_file_list_to_patch = Detector.find_clone()


def load_values():
    if not Values.diff_info:
        Values.diff_info = Reader.read_json(Definitions.FILE_DIFF_INFO)
        load_state()
    Definitions.FILE_CLONE_INFO = Definitions.DIRECTORY_OUTPUT + "/clone-info"


def save_values():
    Writer.write_clone_list(clone_list, Definitions.FILE_CLONE_INFO)
    Values.c_file_list_to_patch = clone_list
    save_current_state()


def safe_exec(function_def, title, *args):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    Emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        Logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Emitter.error("Crash during " + description + ", after " + duration + " seconds.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def detect():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Clone Detection")
    load_values()
    if not Values.SKIP_DETECTION:
        if not Values.SKIP_VEC_GEN:
            safe_exec(generate_target_vectors, "generating vectors for target")
        safe_exec(find_clones, "finding clones in target")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")