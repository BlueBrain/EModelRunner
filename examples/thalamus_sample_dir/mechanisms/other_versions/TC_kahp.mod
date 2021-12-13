TITLE Potasium AHP type current for RD Traub, J Neurophysiol 89:909-921, 2003

: From ModelDB, accession: 20756. There's no temperature correction. (SK-type)
COMMENT

	Implemented by Maciej Lazarewicz 2003 (mlazarew@seas.upenn.edu)

ENDCOMMENT

UNITS { 
	(mV) = (millivolt) 
	(mA) = (milliamp) 
 	(S)  = (siemens)
	(mM) = (milli/liter)
} 

NEURON { 
	SUFFIX TC_kahp
	USEION k READ ek WRITE ik
	USEION ca READ cai
	RANGE gk_max, ik, i_rec
}

PARAMETER { 
	gk_max = 2.5e-5 	(S/cm2)
	v		(mV) 
	:ek 		(mV)  :EI: moved in assigned
	cai		(mM)
}
 
ASSIGNED { 
	ik 		(mA/cm2)
	ek		(mV) 
	i_rec		(mA/cm2)
	alpha beta	(/ms)
}
 
STATE {
	m
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	ik = gk_max * m * ( v - ek ) 
	i_rec = ik
}
 
INITIAL { 
	rates( cai )
	m = alpha / ( alpha + beta )
	m = 0
}
 
DERIVATIVE states { 
	rates( cai )
	m' = alpha * ( 1 - m ) - beta * m 
}

UNITSOFF 

PROCEDURE rates(chi) { 
	
	if( cai < 100 ) {
		:printf("%3.10f\n",cai)	
		alpha = cai / 10000
	}else{
		printf("alpha=0.01")
		alpha = 0.01
	}
	beta = 0.01
}

UNITSON





