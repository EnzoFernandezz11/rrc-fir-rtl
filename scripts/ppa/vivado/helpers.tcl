# Pure Tcl helpers; also exercised by selftest.tcl without Vivado.
proc ppa_read {path} {
    set fh [open $path r]
    fconfigure $fh -encoding utf-8
    set data [read $fh]
    close $fh
    return $data
}
proc ppa_write {path data} {
    set fh [open $path w]
    fconfigure $fh -encoding utf-8
    puts $fh $data
    close $fh
}
proc ppa_json_number {text key} {
    set pattern [format {"%s"\s*:\s*([-+0-9.eE]+)} $key]
    if {![regexp $pattern $text -> number] || ![string is double -strict $number]} {
        error "Missing numeric benchmark field: $key"
    }
    return $number
}
proc ppa_report_number {text labels} {
    foreach label $labels {
        foreach line [split $text \n] {
            set fields [split $line |]
            if {[llength $fields] < 3} {continue}
            set name [string trim [lindex $fields 1] " \t*\r"]
            set value [string map {, {}} [string trim [lindex $fields 2]]]
            if {$name eq $label && [string is double -strict $value]} {return $value}
        }
    }
    error "Report format not recognized for $labels; inspect the original .rpt"
}
proc ppa_diagnostic_report {diagnosis} {
    set text ""
    if {[file isfile $diagnosis]} {append text "\n[ppa_read $diagnosis]\n"}
    foreach {report title} {
        timing_critical.rpt {Camino critico implementado: origen, destino y retardo de logica/ruteo}
        utilization_hierarchical.rpt {Recursos implementados por jerarquia: padres incluyen descendientes}
    } {
        if {[file isfile $report]} {
            append text "\n### $title\n\n```text\n[ppa_read $report]\n```\n"
        }
    }
    return $text
}
proc ppa_exec {log executable args} {
    set command [auto_execok $executable]
    if {$command eq ""} {error "$executable unavailable; use a Vivado command shell"}
    puts "Running $executable; log: $log"
    # A Tcl list preserves paths with spaces, including Windows batch launchers.
    exec {*}$command {*}$args > $log 2>@1
}
proc ppa_inventory {directory {prefix ""}} {
    set rows ""
    foreach path [lsort -unique [glob -nocomplain -directory $directory * .*]] {
        set name [file tail $path]
        if {$name in {. ..}} {continue}
        set relative [file join $prefix $name]
        if {[file type $path] eq "directory"} {
            append rows [ppa_inventory $path $relative]
        } elseif {[file type $path] eq "file"} {
            append rows "$relative\t[file size $path]\n"
        }
    }
    return $rows
}
