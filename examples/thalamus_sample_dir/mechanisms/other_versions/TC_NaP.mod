TITLE  Na persistent channel

: EI, Downloaded from ModelDB (Accession: 20212), CA1 pyramidal neuron, modified according to Amarillo et al., 2014

NEURON {
	SUFFIX TC_NaP
	USEION na READ ena WRITE ina
        RANGE  gNaP_max, i_rec

}

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(S)  = (siemens)

}

:INDEPENDENT {t FROM 0 TO 1 WITH 100 (ms)}

PARAMETER {                         
        :ena = 45                (mV)     :EI: moved in assigned
	gNaP_max = 5.5e-6       (S/cm2) : default value in Amarillo et al., 2014
	celsius 		(degC)
	Q10 = 3			: Assumed, according to Amarillo et al., 2014
}

ASSIGNED {
	ina (mA/cm2)
	v	(mV)
	ena	(mV)
	tcorr   		:Added temperature correction
	mInf
	hInf
	hTau
	i_rec
}	

STATE { m h }

BREAKPOINT {
	SOLVE states METHOD cnexp
	ina = gNaP_max*mInf*h*(v-ena)
	i_rec = ina
}

DERIVATIVE states	{
	rates()
	h' = (hInf-h)/hTau
}

INITIAL {
	states()
	h = hInf
	m = mInf
	tcorr = Q10^((celsius-23)/10)
}



PROCEDURE rates() {     

        mInf = 1 / (1 + exp(-(v+57.9)/6.4))
	hInf = 1 / (1 + exp((v+58.7)/14.2))
	hTau = 1000 + 10000/ (1 + exp((v+60)/10)) / tcorr
}





















