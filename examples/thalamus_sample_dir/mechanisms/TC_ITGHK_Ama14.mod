TITLE Low threshold calcium current
:
:   Ca++ current responsible for low threshold spikes (LTS)
:   Differential equations
:
:   Model of Huguenard & McCormick, J Neurophysiol 68: 1373-1383, 1992.
:   The kinetics is described by Goldman-Hodgkin-Katz equations,
:   using a m2h format, according to the voltage-clamp data
:   (whole cell patch clamp) of Huguenard & Prince, J. Neurosci. 
:   12: 3804-3817, 1992.
:
:   This model is described in detail in:
:   Destexhe A, Neubig M, Ulrich D and Huguenard JR.  
:   Dendritic low-threshold calcium currents in thalamic relay cells.  
:   Journal of Neuroscience 18: 3574-3588, 1998.
:   (a postscript version of this paper, including figures, is available on
:   the Internet at http://cns.fmed.ulaval.ca)
:
:    - shift parameter for screening charge
:    - empirical correction for contamination by inactivation (Huguenard)
:    - GHK equations
:
:
:   Written by Alain Destexhe, Laval University, 1995
:

: EI: downloaded from ModelDB, with modifications with data from Amarillo et al., 2014 
: EI: 16/08/2017 Correction of equation 14 according to Amarillo e-mail.

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX TC_iT_Ama14
	USEION ca READ cai,cao WRITE ica
	RANGE pcabar, m_inf, tau_m, h_inf, tau_h
	RANGE i_rec
	:GLOBAL qm, qh
}

UNITS {
	(molar) = (1/liter)
	(mV) =	(millivolt)
	(mA) =	(milliamp)
	(mM) =	(millimolar)

	FARADAY = (faraday) (coulomb)
	R = (k-mole) (joule/degC)
}

PARAMETER {
	v		(mV)
	celsius		(degC)
	pcabar	= 5e-4	(cm/s)	: Maximum Permeability, default in Amarillo. It is half pcabar_L (McCormick & Huguenard, 1992)
	:cai	= 2.4e-4 (mM)	: adjusted for eca=120 mV
	cai	= 5e-5 (mM)	: EI: From Amarillo et al., 2014
	cao	= 2	(mM)
	:qm	= 5		: q10's for activation and inactivation
	:qh	= 3		: from Coulter et al., J Physiol 414: 587, 1989
	qm = 2.5
	qh = 2.5		: from Amarillo et al, 2014 (refers to Destexhe, 1998)
}

STATE {
	m h
}

ASSIGNED {
	ica	(mA/cm2)
	m_inf
	tau_m	(ms)
	h_inf
	tau_h	(ms)
	phi_m
	phi_h
	i_rec   (mA/cm2)
}

BREAKPOINT {
	SOLVE castate METHOD cnexp
	ica = pcabar * m*m*h * ghk(v, cai, cao)
	i_rec = ica
}

DERIVATIVE castate {
	evaluate_fct(v)
	m' = (m_inf - m) / tau_m
	h' = (h_inf - h) / tau_h
}


UNITSOFF
INITIAL {
	phi_m = qm ^ ((celsius-24)/10)
	phi_h = qh ^ ((celsius-24)/10)

	evaluate_fct(v)

	m = m_inf
	h = h_inf
}

PROCEDURE evaluate_fct(v(mV)) {
:
:   The kinetic functions are taken as described in the model of 
:   Huguenard & McCormick, and corresponds to a temperature of 23-25 deg.
:   Transformation to 36 deg assuming Q10 of 5 and 3 for m and h
:   (as in Coulter et al., J Physiol 414: 587, 1989).
:
:   The activation functions were estimated by John Huguenard.
:   The V_1/2 were of -57 and -81 in the vclamp simulations, 
:   and -60 and -84 in the current clamp simulations.
:
:   The activation function were empirically corrected in order to account
:   for the contamination of inactivation.  Therefore the simulations 
:   using these values reproduce more closely the voltage clamp experiments.
:   (cfr. Huguenard & McCormick, J Neurophysiol, 1992).
:
	m_inf = 1.0 / ( 1 + exp(-(v+53)/6.2)) : This and following modified from original, according to Amarillo et al., 2014
	h_inf = 1.0 / ( 1 + exp((v+75)/4.0) ) 

	tau_m = ( 0.612 + 1.0 / ( exp(-(v+128)/16.7) + exp((v+12.8)/18.2) ) ) / phi_m
	if( v < -75) {
		tau_h = exp((v+461)/66.6) / phi_h
	} else {
		tau_h = ( 28 + exp(-(v+16)/10.5)) / phi_h 
	}
}

FUNCTION ghk(v(mV), ci(mM), co(mM)) (.001 coul/cm3) {
	LOCAL z, eci, eco
	z = (1e-3)*2*FARADAY*v/(R*(celsius+273.15))
	eco = co*efun(z)
	eci = ci*efun(-z)
	:high cao charge moves inward
	:negative potential charge moves inward
	ghk = (.001)*2*FARADAY*(eci - eco)
}

FUNCTION efun(z) {
	if (fabs(z) < 1e-4) {
		efun = 1 - z/2
	}else{
		efun = z/(exp(z) - 1)
	}
}
FUNCTION nongat(v,cai,cao) {	: non gated current
	nongat = pcabar * ghk(v, cai, cao)
}
UNITSON






