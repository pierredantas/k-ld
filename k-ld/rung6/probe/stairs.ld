// Hand-translation of benchmarks/stairs_light/stairs_light.ld into K-LD DSL.
// Faithful to the graphical netlist:
//   * buttons toggle lights_buttons_state (rising-edge, set-if-off / reset-if-on)
//   * rising PIR edge (gated by NOT lights_buttons_state) drives TOF(20s)
//   * stairs_light = TOF0_Q OR lights_buttons_state
// Rising edges are modelled with prev-value helpers (our contacts are level-
// triggered); prev_* are updated AFTER the edges are read, i.e. R_TRIG semantics.

// --- rising-edge detection (read prev BEFORE it is updated below) ---
OTE(rise_up)   := XIC(control_button_up)   * XIO(prev_up) ;
OTE(rise_down) := XIC(control_button_down) * XIO(prev_down) ;
OTE(rise_pir)  := XIC(stairs_pir_sensor)   * XIO(prev_pir) ;

// --- button toggle of lights_buttons_state (snapshot old state to avoid a
//     same-scan set-then-reset race) ---
OTE(do_set)   := ( XIC(rise_up) + XIC(rise_down) ) * XIO(lights_buttons_state) ;
OTE(do_reset) := ( XIC(rise_up) + XIC(rise_down) ) * XIC(lights_buttons_state) ;
OTL(lights_buttons_state) := XIC(do_set) ;
OTU(lights_buttons_state) := XIC(do_reset) ;

// --- off-delay timer: IN = rising(PIR) AND NOT lights_buttons_state, PT=20 ---
OTE(tof_in) := XIC(rise_pir) * XIO(lights_buttons_state) ;
TOF(TOF0_Q, 20, XIC(tof_in)) ;

// --- the light: TOF output OR the manual button state ---
OTE(stairs_light) := XIC(TOF0_Q) + XIC(lights_buttons_state) ;

// --- update edge memories for next scan ---
OTE(prev_up)   := XIC(control_button_up) ;
OTE(prev_down) := XIC(control_button_down) ;
OTE(prev_pir)  := XIC(stairs_pir_sensor) ;
