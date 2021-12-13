:From ModelDB, accession:3808. This should be the BK-like current (Ehling et al., 2013).
:Formulation is the same as in McCormick & Huguenard, 1992

TITLE Ca-dependent potassium current (C-current)

COMMENT
        *********************************************
        reference:      Yamada, Koch & Adams (1989) 
			Meth. in Neuronal Modeling, MIT press
        found in:       bullfrog sympathetic ganglion cells
        *********************************************
	Assembled for MyFirstNEURON by Arthur Houweling
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX TC_iC
	USEION k READ ek WRITE ik
	USEION ca READ cai
        RANGE gkbar, m_inf, tau_m, ik, i_rec
}

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mM) = (milli/liter)
}

PARAMETER {
	v		(mV)
	celsius		(degC)
        dt              (ms)
	:ek 		(mV) :EI: moved in assigned
	cai		(mM)
	gkbar= 0.0001	(mho/cm2) 
}

STATE {
	m
}

ASSIGNED {
	ik		(mA/cm2)
	i_rec		(mA/cm2)
	ek		(mV)
	tau_m		(ms)
	m_inf
	tadj
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	ik = gkbar * m * (v - ek)
	i_rec = ik
}

DERIVATIVE states { 
	rates(v,cai)

       m'= (m_inf-m) / tau_m
}

:PROCEDURE states() { 
:	rates(v,cai)

:	m= m + (1-exp(-dt/tau_m))*(m_inf-m)
:}

UNITSOFF
INITIAL {
	tadj = 3^((celsius-23.5)/10)
	rates(v,cai)
	m = m_inf
}

PROCEDURE rates( v(mV), cai(mM)) {  LOCAL a,b
	a = 250 * cai * exp(v/24)
	b = 0.1 * exp(-v/24)
	tau_m = 1/(a+b) / tadj
	m_inf = a/(a+b)
}
UNITSON






