TITLE Potasium C type current for RD Traub, J Neurophysiol 89:909-921, 2003

:   from RD Traub, J Neurophysiol 89:909-921, 2003
:   implemented by Maciej Lazarewicz 2003 (mlazarew@seas.upenn.edu)
:   Modified by Yimy Amarillo, 2014 (Amarillo et al., J Neurophysiol, 2014)

INDEPENDENT { t FROM 0 TO 1 WITH 1 (ms) }

UNITS { 
	(mV) = (millivolt) 
	(mA) = (milliamp) 
}
 
NEURON { 
	SUFFIX IKCa
	USEION k READ ek WRITE ik
	USEION ca READ cai
	RANGE  gkmax, ik
}

PARAMETER { 
	gkmax = 1.0e-4 	(S/cm2)	: Default maximum conductance
	v ek 		(mV)  
	cai		(1)
} 

ASSIGNED { 
	ik 		(mA/cm2) 
	alpha beta	(/ms)
}
 
STATE {
	m
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	if( 0.004 * cai < 0.000001 ) {
		ik = gkmax * m * 0.004 * cai * ( v - ek ) 
	}else{
		ik = gkmax * m * ( v - ek ) 
	}
}
 
INITIAL { 
	settables(v) 
	m = alpha / ( alpha + beta )
	m = 0
}
 
DERIVATIVE states { 
	settables(v) 
	m' = alpha * ( 1 - m ) - beta * m 
}

UNITSOFF 

PROCEDURE settables(v) { 
	TABLE alpha, beta FROM -120 TO 40 WITH 641

	if( v < -10.0 ) {
		alpha = 2 / 37.95 * ( exp( ( v + 50 ) / 11 - ( v + 53.5 ) / 27 ) )

		: Note that there is typo in the paper - missing minus sign in the front of 'v'
		beta  = 2 * exp( ( - v - 53.5 ) / 27 ) - alpha
	}else{
		alpha = 2 * exp( ( - v - 53.5 ) / 27 )
		beta  = 0
	}
}

UNITSON