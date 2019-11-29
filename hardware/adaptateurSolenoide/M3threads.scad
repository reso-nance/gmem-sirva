// Norm Nuts and Bolts - a OpenSCAD library
// Copyright (C) 2012  Johannes Kneer

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


// USAGE EXAMPLES


include <cyl_head_bolt.scad>;
include <materials.scad>;


// == example nut catches and holes ==
/*
difference() {
	translate([-15, -15, 0]) cube([80, 30, 50]);
	rotate([180,0,0]) nutcatch_parallel("M5", l=5);
	translate([0, 0, 50+e]) hole_through(name="M5", l=50+5, cld=0.1, h=10, hcld=0.4);
	translate([55, 0, 9+e]) nutcatch_sidecut("M8", l=100, clk=0.1, clh=0.1, clsl=0.1);
	translate([55, 0, 50+e]) hole_through(name="M8", l=50+5, cld=0.1, h=10, hcld=0.4);
	translate([27.5, 0, 50+e]) hole_threaded(name="M5", l=60);
}
*/


// == example nuts and screws ==

$fn=60;
//translate([0,50, 0]) stainless() screw("M20x100", thread="modeled");
//translate([0,50,-120]) stainless() nut("M20", thread="modeled");

//translate([30,50,0]) screw("M12x60");
//translate([30,50,-80]) nut("M12");

translate([0,0,0]) screw("M3x10", thread="modeled");
//translate([8,0,0]) nut("M3", 20, thread="modeled");
difference(){
    translate([10,0,0]) cylinder(h=20, r1=6, r2=6, center=true);
    translate([10, 0, 10]) hole_threaded(name="M3", l=30, thread="modeled");

};



// == example db lookups ==

//echo(_get_fam("M8"));
echo(_get_screw("M5x8"));
//echo(_get_screw_fam("M5x8"));

