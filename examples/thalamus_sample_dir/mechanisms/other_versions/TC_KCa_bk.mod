TITLE Potasium C type current for RD Traub, J Neurophysiol 89:909-921, 2003

: From ModelDB, accession: 20756. There is no temperature correction. BK-like channel (Traub et al., 2003)
COMMENT

	Implemented by Maciej Lazarewicz 2003 (mlazarew@seas.upenn.edu)

ENDCOMMENT

INDEPENDENT { t FROM 0 TO 1 WITH 1 (ms) }

UNITS { 
	(mV) = (millivolt) 
	(mA) = (milliamp) 
	(S)  = (siemens)
	(mM) = (milli/liter)
}
 
NEURON { 
	SUFFIX TC_KCa_bk
	USEION k READ ek WRITE ik
	USEION ca READ cai
	RANGE  gk_max, ik, i_rec
}

PARAMETER { 
	gk_max =  1e-4  (S/cm2)  
	v  		(mV)  
	:ek		(mv) :EI: moved in assigned
	cai		(mM)
} 

ASSIGNED { 
	ik 		(mA/cm2)
	ek		(mV)
	i_rec 		(mA/cm2) 
	alpha beta	(/ms)
}
 
STATE {
	m
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	if( 0.004(1/mM) * cai < 1 ) {  : (1/mM) from Traub 2005 (ModelDB, accession 45539)
		ik = gk_max * m * 0.004 (1/mM) * cai * ( v - ek )
		
	}else{
		:printf("%3.10f\n",cai)		
		ik = gk_max * m * ( v - ek )
		
	}
	i_rec = ik	
}
 
INITIAL { 
	settables(v) 
	m = alpha / ( alpha + beta )
	:m = 0
}
 
DERIVATIVE states { 
	settables(v) 
	m' = alpha * ( 1 - m ) - beta * m 
}

UNITSOFF 

PROCEDURE settables(v) { 
	TABLE alpha, beta FROM -120 TO 40 WITH 641
	: Other possible formulation in McCormick & Huguenard, 1992
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





