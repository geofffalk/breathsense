// BreathSense Nasal Clip - Parametric Design
// For 2mm thermistor bead + XIAO nRF52840

// === PARAMETERS (adjust to fit) ===
thermistor_dia = 2.0;       // Thermistor bead diameter
wire_dia = 0.5;             // Wire channel diameter (30 AWG + enamel)
wire_channel_dia = 1.2;     // Slightly larger for easy routing

nose_bridge_width = 28;     // Width across nose bridge
nose_bridge_height = 6;     // Height of bridge piece
nose_bridge_depth = 4;      // Thickness

pad_width = 12;             // Width of each nose pad
pad_height = 10;            // Height of pad
pad_depth = 3;              // Thickness of pad
pad_spacing = 18;           // Distance between pads (center to center)

sensor_arm_length = 15;     // Length of arm holding thermistor
sensor_arm_width = 4;       // Width of sensor arm
sensor_pocket_dia = 2.8;    // Pocket for thermistor (slightly larger than bead)

wall = 1.5;                 // General wall thickness

// === MAIN CLIP ===
module nasal_clip() {
    difference() {
        union() {
            // Nose bridge
            translate([-nose_bridge_width/2, 0, 0])
                cube([nose_bridge_width, nose_bridge_depth, nose_bridge_height]);
            
            // Left pad
            translate([-pad_spacing/2 - pad_width/2, 0, -pad_height + nose_bridge_height])
                cube([pad_width, pad_depth, pad_height]);
            
            // Right pad
            translate([pad_spacing/2 - pad_width/2, 0, -pad_height + nose_bridge_height])
                cube([pad_width, pad_depth, pad_height]);
            
            // Sensor arm (center, going down and forward)
            translate([-sensor_arm_width/2, 0, 0])
                cube([sensor_arm_width, sensor_arm_length, nose_bridge_height/2]);
            
            // Thermistor holder at end of arm
            translate([0, sensor_arm_length, nose_bridge_height/4])
                sphere(d = sensor_pocket_dia + wall*2, $fn=32);
        }
        
        // Wire channel through bridge and down arm
        translate([0, -1, nose_bridge_height/2])
            rotate([-90, 0, 0])
                cylinder(d = wire_channel_dia, h = sensor_arm_length + 5, $fn=16);
        
        // Thermistor pocket (open at bottom for airflow)
        translate([0, sensor_arm_length, nose_bridge_height/4])
            sphere(d = sensor_pocket_dia, $fn=32);
        
        // Opening for thermistor insertion (from below)
        translate([0, sensor_arm_length, -5])
            cylinder(d = sensor_pocket_dia, h = nose_bridge_height/4 + 5, $fn=16);
        
        // Comfort curve on bridge (slight arch)
        translate([0, nose_bridge_depth + 15, nose_bridge_height/2])
            rotate([0, 90, 0])
                cylinder(d = 35, h = nose_bridge_width + 10, center=true, $fn=64);
    }
}

// === SOFT PAD (print in TPU) ===
module soft_pad() {
    difference() {
        // Outer pad shape
        hull() {
            translate([0, 0, 0])
                cube([pad_width + 2, pad_depth + 2, 0.1]);
            translate([1, 1, pad_height])
                cube([pad_width, pad_depth, 0.1]);
        }
        
        // Cutout for rigid pad to slot in
        translate([1, 0, 2])
            cube([pad_width, pad_depth, pad_height]);
    }
}

// === RENDER ===
// Uncomment the part you want to export:

nasal_clip();           // Main clip body (print in PLA/PETG)

// Soft pads - print separately in TPU
// translate([40, 0, 0]) soft_pad();
// translate([60, 0, 0]) soft_pad();
