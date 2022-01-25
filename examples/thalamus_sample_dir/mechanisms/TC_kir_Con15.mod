TITLE Inward Rectifying Potassium Channel (IRK)

COMMENT
	*********************************************
	reference:	NISENBAUM, E. S. & WILSON, C. J. (1995). Potassium currents
responsible for inward and outward rectification in rat neostriatal
spiny projection neurons. Journal of Neuroscience 15, 4449-4463.	

as reported in Williams SR et al., J Physiol (1997)

William Connelly 2013
	*********************************************
  
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
       SUFFIX TC_kir_Con15
       USEION k READ ek WRITE ik 
  RANGE gkbar, m_inf, tau_m 
  GLOBAL shift
}

UNITS {
      (mA) = (milliamp)
      (mV) = (millivolt)
}

PARAMETER {
	  v		(mV)
	  ek			(mV)
	  gkbar= 0.0005		(mho/cm2)
  	  tau_m = 1.0
 	  shift = 0         EI: See Connelly et al., 2015
}

STATE {
      m
}

ASSIGNED {
	 ik		(mA/cm2)
	 m_inf
}

BREAKPOINT { 
	   SOLVE states METHOD cnexp
 	   ik = gkbar * m^3 * (v-ek)
}

DERIVATIVE states { 
	   evaluate_fct(v)
	   m'= (m_inf-m) / tau_m
}

INITIAL {
	evaluate_fct(v)
	m = m_inf
}

PROCEDURE evaluate_fct(v(mV)) {

	  m_inf = 1/(1 + exp( (v - ek - 15 + shift)/10) )
}