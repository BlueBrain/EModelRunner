TITLE Leak sodium current

NEURON {
	SUFFIX TC_Naleak
	USEION na READ ena WRITE ina 
	RANGE gmax, i_rec, ena
}

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(S) = (siemens)
}

PARAMETER {
	gmax = 3.0e-6	(S/cm2)
}

ASSIGNED {
	v	(mV)
	ena	(mV)
	ina	(mA/cm2)
	i_rec
}


BREAKPOINT {
	ina = gmax*(v - ena)
	i_rec = ina
}







