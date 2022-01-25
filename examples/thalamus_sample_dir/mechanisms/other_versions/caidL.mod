TITLE Intracellular calcium dynamics caidL

:   Based on the model by Huguenard & McCormick, J Neurophysiol, 1992
:   Writen by Yimy Amarillo, 2014 (Amarillo et al., J Neurophysiol, 2014)

UNITS {
    (mA) =     (milliamp)
    (mM) =     (milli/liter)
    FARADAY =  (faraday) (coulombs)
}

NEURON {
    SUFFIX caidL
    USEION ca READ ica WRITE cai
    RANGE cai0, depth, taur, gamma : EI added gamma
}

PARAMETER {
    cai0  = 5e-5	(mM)
    depth = 100		(nm)
    gamma   = 0.05 	 (1)		: EI: percent of free calcium (not buffered), see CaDynamics_E2.mod ctx
    taur  = 1 		(ms)
}

ASSIGNED { 
    ica    (mA/cm2)
}

STATE {
    cai (mM)
}

INITIAL { cai = cai0 }

BREAKPOINT {
    SOLVE state METHOD derivimplicit
}

DERIVATIVE state {  
    cai' = -ica * gamma/depth/FARADAY/2 * (1e7) + (cai0 - cai)/taur
}

