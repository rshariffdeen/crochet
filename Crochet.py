#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from tools import Emitter, Logger
from phases import Initialization, Building, Differencing, Detection
from common import Definitions
from common.Utilities import error_exit, create_directories


def first_run_check():
    create_directories()


def run():
    first_run_check()
    Emitter.start()
    start_time = time.time()
    time_info = dict()

    time_start = time.time()
    Initialization.initialize()
    time_info[Definitions.KEY_DURATION_INITIALIZATION] = str(time.time() - time_start)

    time_start = time.time()
    Building.build()
    time_info[Definitions.KEY_DURATION_BUILD_ANALYSIS] = str(time.time() - time_start)

    time_start = time.time()
    Differencing.diff()
    time_info[Definitions.KEY_DURATION_DIFF_ANALYSIS] = str(time.time() - time_start)

    time_start = time.time()
    Detection.detect()
    time_info[Definitions.KEY_DURATION_CLONE_ANALYSIS] = str(time.time() - time_start)


    # time_now = time.time()
    # Mapper.generate()
    # mapping_duration = str(time.time() - time_start)
    #
    # time_start = time.time()
    # Translation.translate()
    # translation_duration = str(time.time() - time_start)
    #
    # time_start = time.time()
    # Weaver.weave()
    # time_info[Definitions.KEY_DURATION_TRANSPLANTATION] = str(time.time() - time_start)

    # Final clean
    Emitter.title("Cleaning residual files generated by Crochet...")
    
    # Final running time and exit message
    time_info[Definitions.KEY_DURATION_TOTAL] = str(time.time() - start_time)
    Emitter.end(time_info)
    Logger.end(time_info)
    
    
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        error_exit("Program Interrupted by User")
