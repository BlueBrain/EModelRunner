TITLE Slow Ca-dependent cation current
:
:   Ca++ dependent nonspecific cation current ICAN
:   Differential equations
:
:   Model based on a first order kinetic scheme
:
:      <closed> + n cai <-> <open>	(alpha,beta)
:
:   Following this model, the activation fct will be half-activated at 
:   a concentration of Cai = (beta/alpha)^(1/n) = cac (parameter)
:
:   The mod file is here written for the case n=2 (2 binding sites)
:   ---------------------------------------------
:
:   Kinetics based on: Partridge & Swandulla, TINS 11: 69-72, 1988.
:
:   This current has the following properties:
:      - inward current (non specific for cations Na, K, Ca, ...)
:      - activated by intracellular calcium
:      - NOT voltage dependent
:
:   A minimal value for the time constant has been added
:
:   Ref: Destexhe et al., J. Neurophysiology 72: 803-818, 1994.
:   See also:  http://www.cnl.salk.edu/~alain , http://cns.fmed.ulaval.ca
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX ican
	USEION n READ en WRITE in VALENCE 1
	USEION ca READ cai
        RANGE gbar, m_inf, tau_m, in
	GLOBAL beta, cac, taumin
}


UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(molar) = (1/liter)
	(mM) = (millimolar)
}


PARAMETER {
	v		(mV)
	celsius	= 36	(degC)
	en	= -20	(mV)		: reversal potential
	cai 	= 2.4e-4 (mM)		: initial [Ca]i
	gbar	= 0.00025 (mho/cm2)
	beta	= 0.002	(1/ms)		: backward rate constant
	cac	= 0.01	(mM)		: middle point of activation fct
	taumin	= 0.1	(ms)		: minimal value of time constant
}


STATE {
	m
}

ASSIGNED {
	in	(mA/cm2)
	m_inf
	tau_m	(ms)
	tadj
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	in = gbar * m*m * (v - en)
}

DERIVATIVE states { 
	evaluate_fct(v,cai)

	m' = (m_inf - m) / tau_m
}

UNITSOFF
INITIAL {
:
:  activation kinetics are assumed to be at 22 deg. C
:  Q10 is assumed to be 3
:
	tadj = 3.0 ^ ((celsius-22.0)/10)

	evaluate_fct(v,cai)
	m = m_inf
}


PROCEDURE evaluate_fct(v(mV),cai(mM)) {  LOCAL alpha2

	alpha2 = beta * (cai/cac)^2

	tau_m = 1 / (alpha2 + beta) / tadj
	m_inf = alpha2 / (alpha2 + beta)

        if(tau_m < taumin) { tau_m = taumin } 	: min value of time cst
}
UNITSON





