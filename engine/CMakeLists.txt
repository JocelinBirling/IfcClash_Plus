# IfcClash_Plus — libifcclash_engine (SPEC_OptimisationInCPP.md)
#
# Build (inside the conda environment of environment_cpp.yml, which holds
# the only OCCT of the process, shared by pythonocc-core and IfcOpenShell):
#
#   conda activate ifcclash_cpp
#   cmake -S engine -B build/engine -G Ninja -DCMAKE_BUILD_TYPE=Release
#   cmake --build build/engine
#   ctest --test-dir build/engine
#
# The Python module _ifcclash_engine is written to ifcclash_plus/engine/.
cmake_minimum_required(VERSION 3.20)
project(ifcclash_engine VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

option(IFCCLASH_BUILD_PYTHON "Build the pybind11 module" ON)
option(IFCCLASH_BUILD_TESTS "Build the C++ unit tests (Catch2)" ON)
set(IFCCLASH_MODULE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../ifcclash_plus/engine"
    CACHE PATH "Where the Python module is written")

if(DEFINED ENV{CONDA_PREFIX})
  list(PREPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")
endif()

# ---- Dependencies (conda-forge)
find_package(OpenCASCADE CONFIG REQUIRED)
find_package(Eigen3 CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(Boost CONFIG REQUIRED)
# zstd: the .ifcview reader (sources/ifcview/third_party, LGPL v3)
find_path(ZSTD_INCLUDE_DIR zstd.h REQUIRED)
find_library(ZSTD_LIBRARY NAMES zstd REQUIRED)

# IfcOpenShell (IfcParse / IfcGeom) has no CMake package: headers and
# shared libraries of the conda-forge ifcopenshell package.
find_path(IFCOPENSHELL_INCLUDE_DIR ifcparse/file.h REQUIRED)
foreach(lib ifcopenshell.parse ifcopenshell.geometry ifcopenshell.plugin)
  string(REPLACE "." "_" var "${lib}")
  find_library(IFCOPENSHELL_${var} NAMES ${lib} REQUIRED)
  list(APPEND IFCOPENSHELL_LIBRARIES ${IFCOPENSHELL_${var}})
endforeach()

set(OCCT_LIBS TKernel TKMath TKG3d TKBRep TKGeomBase TKTopAlgo)

# ---- The engine library
add_library(ifcclash_engine STATIC
  core/Result.cpp
  geometry/MeshMeasures.cpp
  sources/IfcSource.cpp
  sources/IfcClashTree.cpp
  provider/GeometryProvider.cpp
  rules/RuleBase.cpp
  rules/Volume.cpp
  rules/Intersection.cpp
  rules/Clearance.cpp
  rules/Collision.cpp
  pipeline/BroadPhase.cpp
  pipeline/Pipelines.cpp
  registry/RuleSpec.cpp
  registry/Registry.cpp
  api/Session.cpp
  sources/ifcview/IfcViewSource.cpp
  sources/ifcview/third_party/IfcViewReader.cpp
  sources/ifcview/third_party/InstanceCompose.cpp
)
target_include_directories(ifcclash_engine
  PUBLIC  ${CMAKE_CURRENT_SOURCE_DIR}
  PRIVATE ${IFCOPENSHELL_INCLUDE_DIR} ${ZSTD_INCLUDE_DIR})
target_include_directories(ifcclash_engine SYSTEM PUBLIC ${OpenCASCADE_INCLUDE_DIR})
target_link_libraries(ifcclash_engine
  PUBLIC  nlohmann_json::nlohmann_json ${OCCT_LIBS}
  PRIVATE ${IFCOPENSHELL_LIBRARIES} ${ZSTD_LIBRARY} Eigen3::Eigen Boost::headers)
target_compile_options(ifcclash_engine PRIVATE -Wall -Wextra -Wno-unused-parameter)
# The macros the conda-forge ifcopenshell package was built with. They
# change the layout of the IfcParse classes (ifcopenshell::file holds a
# rocksdb storage variant): a mismatch corrupts the heap at the first
# ifcopenshell::file construction.
set(IFCCLASH_IFCOPENSHELL_DEFINITIONS IFOPSH_WITH_ROCKSDB IFOPSH_WITH_OPENCASCADE IFOPSH_WITH_CGAL
    CACHE STRING "Compile definitions matching the IfcOpenShell build")
target_compile_definitions(ifcclash_engine PRIVATE ${IFCCLASH_IFCOPENSHELL_DEFINITIONS})

# The IfcOpenShell plugins (schemas, kernels, trees) are loaded at run time
# from the library directory: keep it in the RPATH.
get_filename_component(IFCOPENSHELL_LIB_DIR "${IFCOPENSHELL_ifcopenshell_parse}" DIRECTORY)
set(CMAKE_BUILD_RPATH "${IFCOPENSHELL_LIB_DIR}")
set(CMAKE_INSTALL_RPATH "${IFCOPENSHELL_LIB_DIR}")

# ---- Python module
if(IFCCLASH_BUILD_PYTHON)
  find_package(Python 3.10 COMPONENTS Interpreter Development.Module REQUIRED)
  find_package(pybind11 CONFIG REQUIRED)
  pybind11_add_module(_ifcclash_engine bindings/module.cpp)
  target_link_libraries(_ifcclash_engine PRIVATE ifcclash_engine)
  set_target_properties(_ifcclash_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${IFCCLASH_MODULE_DIR}"
    BUILD_RPATH "${IFCOPENSHELL_LIB_DIR}")
endif()

# ---- Unit tests
if(IFCCLASH_BUILD_TESTS)
  find_package(Catch2 3 CONFIG REQUIRED)
  enable_testing()
  add_executable(engine_tests
    tests/test_geometry.cpp
    tests/test_registry.cpp
    tests/test_broad_phase.cpp
    tests/test_session.cpp
    tests/test_ifcview.cpp)
  target_link_libraries(engine_tests PRIVATE ifcclash_engine Catch2::Catch2WithMain)
  target_compile_definitions(engine_tests PRIVATE
    IFCCLASH_REPO_DIR="${CMAKE_CURRENT_SOURCE_DIR}/..")
  include(Catch)
  catch_discover_tests(engine_tests)
endif()
