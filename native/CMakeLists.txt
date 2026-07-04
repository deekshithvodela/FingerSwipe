find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBINPUT REQUIRED IMPORTED_TARGET libinput)
pkg_check_modules(LIBUDEV REQUIRED IMPORTED_TARGET libudev)
pkg_check_modules(PIPEWIRE REQUIRED IMPORTED_TARGET libpipewire-0.3)

find_package(Threads REQUIRED)

add_library(fingerswipe SHARED src/api.c src/core/libinput.c src/backends/pipewire.c)
add_library(FingerSwipe::fingerswipe ALIAS fingerswipe)
target_compile_definitions(fingerswipe PRIVATE FINGERSWIPE_BUILD _GNU_SOURCE)
target_include_directories(fingerswipe PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
target_link_libraries(fingerswipe PRIVATE PkgConfig::LIBINPUT PkgConfig::LIBUDEV PkgConfig::PIPEWIRE Threads::Threads)
target_compile_options(fingerswipe PRIVATE -Wall -Wextra -Wpedantic -Werror)
set_target_properties(fingerswipe PROPERTIES VERSION 1.0.0 SOVERSION 1 C_VISIBILITY_PRESET hidden)

include(GNUInstallDirs)
install(TARGETS fingerswipe LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(DIRECTORY include/fingerswipe DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
