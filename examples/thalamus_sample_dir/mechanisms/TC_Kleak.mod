TITLE Leak potassium current
: From Amarillo et al., 2014

NEURON {
	SUFFIX TC_Kleak
	USEION  k READ ek WRITE ik
	RANGE gmax, i_rec
}

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(S) = (siemens)
}

PARAMETER {
	gmax = 1.0e-5	(S/cm2)
}

ASSIGNED {
	v	(mV)
	ek	(mV)
	ik	(mA/cm2)
	i_rec
}


BREAKPOINT {
	ik = gmax*(v - ek)
	i_rec = ik
}







