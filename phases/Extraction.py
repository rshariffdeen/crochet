#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from common import Definitions, Values
from common.Utilities import execute_command, error_exit, save_current_state
from tools import Emitter, Collector, Reader, Writer, Slicer
from ast import Vector

generated_script_list = dict()


def generate_edit_script(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    Emitter.normal("\t" + name_a)
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        command = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -dump-matches " + \
                  file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating edit script: " + output_file)


def generate_script_for_files(file_list_to_patch):
    global generated_script_list
    generated_source_list = list()
    script_file_ab = Definitions.DIRECTORY_TMP + "/diff_script_AB"
    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        vector_source_a = ""
        vector_source_b = ""
        vector_source_c = ""
        vector_source_d = ""
        segment_code = ""
        vector_name_a = ""
        vector_name_c = ""
        try:
            if "func_" in vec_path_a:
                vector_source_a, vector_name_a = vec_path_a.split(".func_")
                vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                vector_source_c, vector_name_c = vec_path_c.split(".func_")
                segment_code = 'func'
            elif "struct_" in vec_path_a:
                    vector_source_a, vector_name_a = vec_path_a.split(".struct_")
                    vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                    vector_source_c, vector_name_c = vec_path_c.split(".struct_")
                    segment_code = 'struct'
            elif "enum_" in vec_path_a:
                vector_source_a, vector_name_a = vec_path_a.split(".enum_")
                vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                vector_source_c, vector_name_c = vec_path_c.split(".enum_")
                segment_code = 'enum'
            elif "var_" in vec_path_a:
                vector_source_a, vector_name_a = vec_path_a.split(".var_")
                vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                vector_source_c, vector_name_c = vec_path_c.split(".var_")
                segment_code = 'var'

            vector_name_b = vector_name_a.replace(Values.PATH_A, Values.PATH_B)
            vector_name_d = vector_name_a.replace(Values.PATH_C, Values.Project_D.path)
            vector_source_d = vector_source_d.replace(Values.PATH_C, Values.Project_D.path)

            if vector_source_a in generated_source_list:
                continue

            Slicer.slice_source_file(vector_source_a, segment_code, vector_name_a.replace(".vec", ""), Values.PATH_A)
            Slicer.slice_source_file(vector_source_b, segment_code, vector_name_b.replace(".vec", ""), Values.PATH_B)
            Slicer.slice_source_file(vector_source_c, segment_code, vector_name_c.replace(".vec", ""), Values.PATH_C)
            Slicer.slice_source_file(vector_source_d, segment_code, vector_name_d.replace(".vec", ""), Values.Project_D.path)

            generate_edit_script(vector_source_a, vector_source_b, script_file_ab)
            original_script, inserted_node_list, map_ab = Collector.collect_instruction_list(script_file_ab)
            generated_data = (original_script, inserted_node_list, map_ab)
            generated_script_list[(vector_source_a, vector_source_b, vector_source_c)] = generated_data
            generated_source_list.append(vector_source_a)

        except Exception as e:
            error_exit("something went wrong with extraction phase")


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
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


def load_values():
    if not Values.file_list_to_patch:
        clone_list = Reader.read_json(Definitions.FILE_CLONE_INFO)
        Values.file_list_to_patch = clone_list
    Definitions.FILE_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/script-info"


def save_values():
    Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    Values.generated_script_files = generated_script_list
    save_current_state()


def extract():
    Emitter.title("Generating AST for context matching")
    # Using all previous structures to transplant patch
    load_values()
    if not Values.SKIP_EXTRACTION:
        if not Values.file_list_to_patch:
            error_exit("no clone file detected to generate AST")
        safe_exec(generate_script_for_files, "generating AST map", Values.file_list_to_patch)
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")

