$fa=5; $fs=0.1;

//втулки высокие

    difference()
        {
            translate([4,4,9]) cylinder(r=3.5, h=22, center=true);
            translate([4,4,9]) cylinder(r=2, h=22.01, center=true);
        } 
      
    difference()
        {
            translate([4,-4,9]) cylinder(r=3.5, h=22, center=true);
            translate([4,-4,9]) cylinder(r=2, h=22.01, center=true);
        }     
        
    difference()
        {
            translate([-4,4,9]) cylinder(r=3.5, h=22, center=true);
            translate([-4,4,9]) cylinder(r=2, h=22.01, center=true);
        }   
        
    difference()
        {
            translate([-4,-4,9]) cylinder(r=3.5, h=22, center=true);
            translate([-4,-4,9]) cylinder(r=2, h=22.01, center=true);
        }   