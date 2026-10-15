# Pure Tcl helpers; also exercised by selftest.tcl without Vivado.
proc ppa_options {arguments} {
    set options [dict create output "" top fir_frequency_serial bench tb_fir_frequency_ppa \
        period_ns 100 latency_cycles 559 block_cycles 575 active_cycles 147200 \
        vectors vectors/ppa_vectors.txt]
    if {[llength $arguments] && ![string match -* [lindex $arguments 0]]} {
        dict set options output [lindex $arguments 0]
        set arguments [lrange $arguments 1 end]
    }
    if {[llength $arguments] % 2} {error "Expected option/value pairs after the optional output directory"}
    foreach {flag value} $arguments {
        if {$flag ni {-top -bench -period_ns -latency_cycles -block_cycles -active_cycles -vectors}} {
            error "Unknown PPA option: $flag"
        }
        dict set options [string range $flag 1 end] $value
    }
    foreach key {top bench} {
        if {![regexp {^[A-Za-z_][A-Za-z0-9_$]*$} [dict get $options $key]]} {
            error "Invalid module name for $key"
        }
    }
    set period [dict get $options period_ns]
    if {![string is double -strict $period] || !($period > 0 && $period < Inf)} {
        error "period_ns must be finite and positive"
    }
    foreach key {latency_cycles block_cycles active_cycles} {
        set value [dict get $options $key]
        if {![string is integer -strict $value] || $value <= 0} {error "$key must be a positive integer"}
    }
    return $options
}

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
