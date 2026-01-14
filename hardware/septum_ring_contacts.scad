// BreathSense Septum Ring with Contact Pads
// For 2mm thermistor bead + detachable spring clip connection

// === PARAMETERS ===
ring_od = 10;              // Outer diameter of ring (mm)
ring_id = 8;               // Inner diameter (nose opening)
bar_dia = 1.2;             // Thickness of ring bar
ball_dia = 3.5;            // Ball end diameter

// Contact pad parameters
pad_width = 1.5;           // Width of each contact pad
pad_height = 1.0;          // Height of pad
pad_spacing = 2.0;         // Distance between pad centers
pad_depth = 0.3;           // How far pad protrudes (for copper tape)

// Thermistor
thermistor_dia = 2.0;      // Thermistor bead diameter
thermistor_pocket = 2.4;   // Pocket size (slightly larger)

// Wire channel
wire_dia = 0.4;            // For 30 AWG magnet wire

$fn = 64;

// === MODULES ===

module ring_body() {
    difference() {
        union() {
            // Main ring arc (horseshoe shape)
            rotate_extrude(angle = 300, convexity = 10)
                translate([ring_od/2 - bar_dia/2, 0, 0])
                    circle(d = bar_dia);
            
            // Ball end 1
            rotate([0, 0, -30])
                translate([ring_od/2 - bar_dia/2, 0, 0])
                    sphere(d = ball_dia);
            
            // Ball end 2 (with contact pads)
            rotate([0, 0, -270])
                translate([ring_od/2 - bar_dia/2, 0, 0])
                    sphere(d = ball_dia);
        }
        
        // Wire channels (two channels for two wires)
        rotate([0, 0, -30])
            translate([ring_od/2 - bar_dia/2, 0, 0])
                rotate([0, 90, 0])
                    cylinder(d = wire_dia, h = ring_od, center = true);
    }
}

module contact_pads() {
    // Two flat pads on ball end 2 for copper tape
    rotate([0, 0, -270])
        translate([ring_od/2 - bar_dia/2, 0, 0]) {
            // Pad 1
            translate([0, -pad_spacing/2, ball_dia/2 - 0.1])
                cube([pad_width, pad_width, pad_depth], center = true);
            // Pad 2
            translate([0, pad_spacing/2, ball_dia/2 - 0.1])
                cube([pad_width, pad_width, pad_depth], center = true);
        }
}

module thermistor_holder() {
    // Small arm extending down from ring center with thermistor pocket
    translate([0, -ring_od/2 - 3, 0]) {
        // Arm
        hull() {
            translate([0, ring_od/2 + 1, 0])
                sphere(d = bar_dia);
            sphere(d = bar_dia + 0.5);
        }
        // Thermistor pocket
        translate([0, 0, -1])
            sphere(d = thermistor_pocket);
    }
}

// === RENDER ===
difference() {
    union() {
        ring_body();
        contact_pads();
        thermistor_holder();
    }
    
    // Hollow out thermistor pocket
    translate([0, -ring_od/2 - 3, -1])
        sphere(d = thermistor_dia);
    
    // Opening for thermistor insertion from below
    translate([0, -ring_od/2 - 3, -5])
        cylinder(d = thermistor_dia, h = 5);
}
