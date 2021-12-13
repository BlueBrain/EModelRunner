TITLE transient potassium current (A-current)

: EI: From ModelDB, accession 3808
COMMENT
	*********************************************
	reference:	Huguenard & McCormick (1992) 
			J.Neurophysiology 68(4), 1373-1383
	found in:	thalamic relay neurons		 	
	*********************************************
	Original by Alain Destexhe
	Rewritten for MyFirstNEURON by Arthur Houweling
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX TC_iA_old
	USEION k READ ek WRITE ik 
        RANGE gk_max, m_inf1, tau_m, h_inf, tau_h1, ik, i_rec
}

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(S)  = (siemens)
	
}

PARAMETER {
	:v		(mV) : EI: move in assigned
	celsius		(degC)
	:dt		(ms)
	:ek		(mV) :EI: moved in assigned
	gk_max= 5.5e-3	(S/cm2) : EI: from Amarillo et al., 2014 
}

STATE {
	m1 h1
}

ASSIGNED {
	v		(mV)
	ik		(mA/cm2)
	ek 		(mV)	
	m_inf1
	tau_m		(ms)
	h_inf
	tau_h1		(ms)
	tcorr
	i_rec
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
 	ik = gk_max * m1^4*h1 * (v-ek)
	i_rec = ik
}

DERIVATIVE states { 
	evaluate_fct(v)

	m1'= (m_inf1-m1) / tau_m
	h1'= (h_inf-h1) / tau_h1
}

:PROCEDURE states() {
:        evaluate_fct(v)

:	m1= m1 + (1-exp(-dt/tau_m))*(m_inf1-m1)
:	h1= h1 + (1-exp(-dt/tau_h1))*(h_inf-h1)
:}

UNITSOFF
INITIAL {
	tcorr = 2.8^((celsius-23.5)/10) : EI: q from 3 to 2.8 according to Amarillo et al., 2014
	evaluate_fct(v)
	m1 = m_inf1
        h1 = h_inf
}

PROCEDURE evaluate_fct(v(mV)) {  LOCAL a,b
	tau_m = 1.0/((exp((v+35.82)/19.69)+exp(-(v+79.69)/12.7))+0.37) / tcorr
	m_inf1 = 1.0 / (1+exp(-(v+60)/8.5))
	a = 1.0/((exp((v+46.05)/5)+exp(-(v+238.4)/37.45))) / tcorr
	if (v<-63) {
		tau_h1 = a
		}
	else {
		tau_h1 = 19.0/tcorr
		}
	h_inf = 1.0/(1+exp((v+78)/6))
}
UNITSON






