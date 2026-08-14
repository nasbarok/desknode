# DeskNode — firmware P1 « Living PCB statique plein écran » (story dn1-2).
#
# Projet DISTINCT de firmware/hello-desknode, qui reste le témoin minimal :
# quand le bring-up RGB part en panic, hello-desknode prouve en 6 s que la
# chaîne build/flash/monitor, elle, n'est pas en cause (décision D-F).

cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(desknode)

# L'asset Living PCB vit dans une PARTITION DE DONNÉES dédiée, pas dans
# .rodata (voir tools/gen_living_pcb.py et hardware/…-affichage.md) :
# EMBED_FILES le ferait recopier en PSRAM au boot dès que CONFIG_SPIRAM_RODATA
# est activé, ce qui brouillerait la mesure XIP.
#
# `esptool_py_flash_to_partition` fait flasher ce binaire par `idf.py flash`,
# au bon offset, sans qu'on ait à le retenir.
set(DN_ASSET_BIN "${CMAKE_BINARY_DIR}/living_pcb_v0.bin")
set(DN_ASSET_GEN "${CMAKE_CURRENT_LIST_DIR}/../../tools/gen_living_pcb.py")

add_custom_command(
    OUTPUT "${DN_ASSET_BIN}"
    COMMAND ${CMAKE_COMMAND} -E echo "Génération de l'asset Living PCB v0…"
    COMMAND python3 "${DN_ASSET_GEN}" --out-bin "${DN_ASSET_BIN}"
    DEPENDS "${DN_ASSET_GEN}"
    COMMENT "asset Living PCB v0 (480x640 RGB565 LE)"
    VERBATIM)

add_custom_target(dn_asset ALL DEPENDS "${DN_ASSET_BIN}")

esptool_py_flash_to_partition(flash "assets" "${DN_ASSET_BIN}")
add_dependencies(flash dn_asset)
