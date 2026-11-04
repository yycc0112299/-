# Use the repository unpacked beside this script; no Vivado installation files are changed.
set script_dir [file dirname [file normalize [info script]]]
set board_root [file join $script_dir board_repos XilinxBoardStore-master boards]
if {![file exists [file join $board_root TUL pynqzu 1.1 board.xml]]} {
    error "PYNQ-ZU board files are missing under $board_root"
}
set_param board.repoPaths [list $board_root]
set matches [get_board_parts *pynqzu*]
if {[llength $matches] == 0} {
    error "Vivado did not find a PYNQ-ZU board part in $board_root"
}
puts "PYNQ_ZU_BOARD_PARTS=$matches"
