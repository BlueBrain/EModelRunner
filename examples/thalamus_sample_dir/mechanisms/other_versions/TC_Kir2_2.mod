TITLE KIR channel
: From Amarillo et al., 2014

NEURON {
	SUFFIX TC_Kir
	USEION  k READ ek WRITE ik
	RANGE g, i_rec, gmax
	GLOBAL minf, mtau
}

CONSTANT {
	Q10 = 3 (1) : To check, recordings at room temperature, but not mention of q10
}

UNITS {
	(mA) = (milliamp)
	(uA) = (microamp)
	(mV) = (millivolt)
	(mS) = (millimho)
}

PARAMETER {
	:ek			(mV) :EI: moved in assigned
	gmax = 2.0e-5	(mho/cm2)	<0,1e9>
	m_vh = -97.9	(mV)	: half activation
	m_ve = 9.7		(mV)	: slope
	mtau_ss = 5.7 	        :To check (also see McCormick & Huguenard 1992a,b and NaP kinetics)
}

ASSIGNED {
	v	(mV)
	ek	(mV)
	g	(mho/cm2)
	ik	(mA/cm2)
	minf	(1)
	mtau	(ms)
	qt (1)
	i_rec
}

STATE {
	m
}

BREAKPOINT {
	SOLVE states METHOD cnexp
	g = gmax*m
	ik = g*(v - ek)
	i_rec = ik
}

INITIAL {
	qt = Q10^((celsius-22)/10) : Room temperature (20-23 in Nadal, Amarillo et al., 2006)
	rates(v)
	m = minf
}

DERIVATIVE states { 
	rates(v)
	m' = (minf-m)/mtau
	:m' = (minf-m)/mtau
}

:FUNCTION_TABLE tabmtau(v(mV)) (ms)

: rates() computes rate and other constants at present v
: call once from hoc to initialize inf at resting v

PROCEDURE rates(v(mV)) {
:	mtau = tabmtau(v)
	mtau = mtau_ss/qt
	minf = 1/(1 + exp((v - m_vh)/m_ve))
}







