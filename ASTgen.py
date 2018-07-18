# -*- coding: utf-8 -*-

''' Main vector generation functions '''

from Utils import err_exit, exec_com
import ASTVector
import ASTparser
import Print

crochet_diff = "crochet-diff "

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

def gen_vec(proj, proj_attribute, file, f_or_struct, start, end, Deckard=True):
    v = ASTVector.ASTVector(proj, file, f_or_struct, start, end, Deckard)
    if not v.vector:
        return None
    if file in proj_attribute.keys():
        proj_attribute[file][f_or_struct] = v
    else:
        proj_attribute[file] = dict()
        proj_attribute[file][f_or_struct] = v
    return v

def ASTdump(file, output):
    c = crochet_diff + "-ast-dump-json " + file + \
        " 2> output/errors_AST_dump > " + output
    a = exec_com(c, True)
    Print.yellow(a[0])

def gen_json(filepath):
    json_file = filepath + ".ASTalt"
    ASTdump(filepath, json_file)
    return ASTparser.AST_from_file(json_file)

def parseAST(filepath, proj, Deckard=True):

    # Save functions here
    function_lines = list()
    # Save variables for each function d[function] = "typevar namevar; ...;"
    dict_file = dict()
    try:        
        # NEW CODE #
        try:
            ast = gen_json(filepath)
        except:
            Print.yellow("Skipping... Failed for file:\n\t" + filepath)
            return function_lines, dict_file
        
    except Exception as e:
        err_exit(e, "Unexpected error in gen_json with file:", filepath)
        
    
    # If we're inside the tree parsing a function
    #in_function = False
    # If we're inside the tree parsing a struct
    #in_struct = False
    # Start and ending line of the function/struct
    start = 0
    end = 0
    file = filepath.split("/")[-1]
    
    if Deckard:
        Print.grey("Generating vectors for " + filepath.split("/")[-1])

    function_nodes = []
    root = ast[0]
    root.get_nodes("type", "FunctionDecl", function_nodes)
    #Print.white(function_nodes)
    for node in function_nodes:
        set_struct_nodes = set()
        #Print.yellow(node.file)
        if node.file != None and file in node.file:
            f = node.value.split("(")[0]
            start = int(node.line)
            end = int(node.line_end)
            function_lines.append((f, start, end))
            gen_vec(proj, proj.funcs, filepath, f, start, end, Deckard)
            structural_nodes = []
            for interesting_type in interesting:
                node.get_nodes("type", interesting_type, structural_nodes)
            for struct_node in structural_nodes:
                var = struct_node.value.split("(")
                var_type = var[-1][:-1]
                var = var[0]
                line = var_type + " " + var + ";"
                if f not in dict_file.keys():
                    dict_file[f] = ""
                dict_file[f] = dict_file[f] + line
                set_struct_nodes.add(struct_node.value)
                
    with open('output/function-lines', 'w') as func_l:
        for l in function_lines:
            func_l.write(l[0] + " " + str(l[1]) + "-" + str(l[2]) + "\n")
    with open('output/function-vars', 'w') as func_l:
        for func in dict_file.keys():
            func_l.write(func + "\n")
            for line in dict_file[func].split(";"):
                func_l.write("\t" + line.replace("  ", "") + "\n")
    if Deckard:
        get_vars(proj, filepath, dict_file)
   
    return function_lines, dict_file


def get_vars(proj, file, dict_file):
    for func in dict_file.keys():
        for line in dict_file[func].split(";"):
            if file in proj.funcs.keys():
                if func in proj.funcs[file].keys():
                    proj.funcs[file][func].params.append(line)
                        

def intersect(start, end, start2, end2):
    return not (end2 < start or start2 > end)
    
                        
def find_affected_funcs(proj, file, pertinent_lines):
    try:
        function_lines, dict_file = parseAST(file, proj, False)
    except Exception as e:
        err_exit(e, "Error in parseAST.")
    for start2, end2 in pertinent_lines:
        for f, start, end in function_lines:
            if intersect(start, end, start2, end2):
                if file not in proj.funcs.keys():
                    proj.funcs[file] = dict()
                if f not in proj.funcs[file]:
                    proj.funcs[file][f] = ASTVector.ASTVector(proj, file, f,
                                                              start, end, True)
                    Print.rose("\t\tFunction successfully found: " + f + \
                               " in " + file.replace(proj.path, 
                                                     proj.name + "/"))
                    Print.grey("\t\t\t" + f + " " + str(start) + "-" + \
                               str(end), False)
                break
    get_vars(proj, file, dict_file)
    return function_lines, dict_file