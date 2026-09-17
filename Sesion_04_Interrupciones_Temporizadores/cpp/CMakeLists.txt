cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(reaction_game C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(reaction_game
    main.c
)

target_link_libraries(reaction_game pico_stdlib)

pico_add_extra_outputs(reaction_game)
