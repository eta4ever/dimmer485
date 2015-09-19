$fa=5; $fs=0.1;

difference(){

    union()
    {
        // платформа
        
        hull(){
            translate([-10, 8, -1]) cylinder(r=17, h=2, center=true);
            translate([10, 8, -1]) cylinder(r=17, h=2, center=true);
            translate([10, -8, -1]) cylinder(r=17, h=2, center=true);
            translate([-10, -8, -1]) cylinder(r=17, h=2, center=true);
        }
        
        // упоры
        translate([18.1, 15.88, 5]) cylinder(r=3, h=2, center=true);
        translate([-18.1, 15.88, 5]) cylinder(r=3, h=2, center=true);
        translate([18.1, -15.88, 5]) cylinder(r=3, h=2, center=true);
        translate([-18.1, -15.88, 5]) cylinder(r=3, h=2, center=true);
        
        translate([18.1, 15.88, 2]) cube([9,7,4], center=true);
        translate([18.1, -15.88, 2]) cube([9,7,4], center=true);
        translate([-18.1, 15.88, 2]) cube([9,7,4], center=true);
        translate([-18.1, -15.88, 2]) cube([9,7,4], center=true);
        
    }
    
    union()
    {
        // отверстия под плату
        translate([18.1, 15.88, 2]) cylinder(r=1.7, h=8.01, center=true);
        translate([-18.1, 15.88, 2]) cylinder(r=1.7, h=8.01, center=true);
        translate([18.1, -15.88, 2]) cylinder(r=1.7, h=8.01, center=true);
        translate([-18.1, -15.88, 2]) cylinder(r=1.7, h=8.01, center=true);
        
        // прорези под гайки
        translate([18.1, 15.88, 1.36]) cube([5.6, 7.01, 2.7], center=true);
        translate([-18.1, 15.88, 1.36]) cube([5.6, 7.01, 2.7], center=true);
        translate([18.1, -15.88, 1.36]) cube([5.6, 7.01, 2.7], center=true);
        translate([-18.1, -15.88, 1.36]) cube([5.6, 7.01, 2.7], center=true);
        
        // крепежные отверстия
        translate([-11, 21 , -1]) cylinder(r=1.7, h=2.01, center=true);
        translate([11, 21 , -1]) cylinder(r=1.7, h=2.01, center=true);
        translate([11, -21 , -1]) cylinder(r=1.7, h=2.01, center=true);
        translate([-11, -21 , -1]) cylinder(r=1.7, h=2.01, center=true);
        
        // центральное отверстие
        translate([0, 0, -1]) cylinder(r=17, h=2.01, center=true);
        
        
    }
    
}

//втулки высокие

    difference()
        {
            translate([5,5,9]) cylinder(r=3, h=22, center=true);
            translate([5,5,9]) cylinder(r=1.7, h=22.01, center=true);
        } 
      
    difference()
        {
            translate([5,-5,9]) cylinder(r=3, h=22, center=true);
            translate([5,-5,9]) cylinder(r=1.7, h=22.01, center=true);
        }     
        
    difference()
        {
            translate([-5,5,9]) cylinder(r=3, h=22, center=true);
            translate([-5,5,9]) cylinder(r=1.7, h=22.01, center=true);
        }   
        
    difference()
        {
            translate([-5,-5,9]) cylinder(r=3, h=22, center=true);
            translate([-5,-5,9]) cylinder(r=1.7, h=22.01, center=true);
        }   