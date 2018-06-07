from __future__ import print_function
import os
import sys
from pycparser import c_generator, parse_file
import pickle
import subprocess as sub

output_dir = "output/"

file_list = list()
function_list = list()
variable_mapping = dict()


def exec_command(command):
    #print(command)
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()

    if p.returncode != 0:
        print ("ERROR")
        print(errors)
        exit(-1)
    return output


def generate_ast_edit_script():
    print("\t\t\tgenerating ast edit script..")
    source_a = file_list[0]
    source_b = file_list[1]
    common_path = longestSubstringFinder(source_a, source_b).split("/")[:-1]
    common_path = "/".join(common_path)
    ast_diff_command = "docker run -v " + common_path + ":/diff "
    ast_diff_command += " gumtree diff "
    ast_diff_command += source_a.replace(common_path, "/diff") + " "
    ast_diff_command += source_b.replace(common_path, "/diff")
    ast_diff_command += " | grep -v Match > " + output_dir + "ast-script"
    exec_command(ast_diff_command)


def longestSubstringFinder(string1, string2):
    answer = ""
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        match = ""
        for j in range(len2):
            if (i + j < len1 and string1[i + j] == string2[j]):
                match += string2[j]
            else:
                if (len(match) > len(answer)): answer = match
                match = ""
    return answer


def translate_to_c(ast_file_path):
    if os.path.isfile(ast_file_path):
        with open(ast_file_path, 'rb') as ast_file:
            ast = pickle.load(ast_file)
            generator = c_generator.CGenerator()
            print(generator.visit(ast))
    else:
        print ("Invalid file: file could not be opened")


def translate_to_ast(c_file_path):

    if os.path.isfile(c_file_path):
        file_name = c_file_path.split("/")[-1]
        with open(output_dir + file_name + ".ast", 'wb') as file:
            ast = parse_file(c_file_path, use_cpp=True,
                             cpp_path='gcc', cpp_args=['-E', r'-Itools/pycparser/utils/fake_libc_include'])

            pickle.dump(ast, file, protocol=-1)
    else:
        print ("Invalid file: file could not be opened")


def initialize(source_a, function_a, source_b, function_b, source_c, function_c, var_map):
    global file_list, function_list, variable_mapping
    file_list.append(source_a)
    file_list.append(source_b)
    file_list.append(source_c)

    function_list.append(function_a)
    function_list.append(function_b)
    function_list.append(function_c)

    variable_mapping = dict(var_map)


def generate_ast_files():
    for source_file in file_list:
        translate_to_ast(source_file)


def translate_ast_edit_script():
    print("\t\t\ttranslating ast edit script..")


def transform_buggy_program():
    print("\t\t\tapplying ast transformation to buggy program..")


def transplant(source_a, function_a, source_b, function_b, source_c, function_c, var_map):
    initialize(source_a, function_a, source_b, function_b, source_c, function_c, var_map)
    generate_ast_edit_script()
    translate_ast_edit_script()
    transform_buggy_program()


