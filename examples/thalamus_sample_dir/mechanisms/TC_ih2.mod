TITLE I-h channel for Thalamic neurons from McCormick and Pape (1990)

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
}

PARAMETER {
        v 		(mV)
        eh = -45  	(mV)        
        celsius 	(degC)
        ghbar=.00005 	(mho/cm2)
        vhalft=-80   	(mV)
        a0t=0.0005      	(/ms)
        zetat=0.2    	(1)
        gmt=.65   	(1)
        q10=4.5
        shift=0   (mV)
}


NEURON {
        SUFFIX TC_ih2
        NONSPECIFIC_CURRENT ih
        RANGE ghbar, eh, irec
	THREADSAFE
        GLOBAL linf,taul,shift
}

STATE {
        l
}

ASSIGNED {
        ih (mA/cm2)
	irec (mA/cm2)
        linf      
        taul
}

INITIAL {
	rate(v)
	l=linf
}


BREAKPOINT {
	SOLVE states METHOD cnexp
	ih = ghbar*l*(v-eh)
	irec = ih
}


FUNCTION alpt(v(mV)) {
  alpt = exp(zetat*(v-vhalft+shift)) 
}

FUNCTION bett(v(mV)) {
  bett = exp(zetat*gmt*(v-vhalft+shift)) 
}

DERIVATIVE states {     : exact when v held constant; integrates over dt step
        rate(v)
        l' =  (linf - l)/taul
}

PROCEDURE rate(v (mV)) { :callable from hoc
        LOCAL qt
        qt=q10^((celsius-36)/10)
        linf = 1/(1+ exp((v+75+shift)/5.5))
        taul = bett(v)/(qt*a0t*(1+alpt(v)))
}





