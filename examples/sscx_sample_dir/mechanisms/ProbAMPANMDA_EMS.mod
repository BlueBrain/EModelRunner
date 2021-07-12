COMMENT
/**
 * @file ProbAMPANMDA_EMS.mod
 * @brief
 * @author king, muller, reimann, ramaswamy
 * @date 2011-08-17
 * @remark Copyright © BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT

TITLE Probabilistic AMPA and NMDA receptor with presynaptic short-term plasticity


COMMENT
AMPA and NMDA receptor conductance using a dual-exponential profile
presynaptic short-term plasticity as in Fuhrmann et al. 2002

_EMS (Eilif Michael Srikanth)
Modification of ProbAMPANMDA: 2-State model by Eilif Muller, Michael Reimann, Srikanth Ramaswamy, Blue Brain Project, August 2011
This new model was motivated by the following constraints:

1) No consumption on failure.
2) No release just after release until recovery.
3) Same ensemble averaged trace as deterministic/canonical Tsodyks-Markram
   using same parameters determined from experiment.
4) Same quantal size as present production probabilistic model.

To satisfy these constaints, the synapse is implemented as a
uni-vesicular (generalization to multi-vesicular should be
straight-forward) 2-state Markov process.  The states are
{1=recovered, 0=unrecovered}.

For a pre-synaptic spike or external spontaneous release trigger
event, the synapse will only release if it is in the recovered state,
and with probability u (which follows facilitation dynamics).  If it
releases, it will transition to the unrecovered state.  Recovery is as
a Poisson process with rate 1/Dep.

This model satisys all of (1)-(4).


ENDCOMMENT


NEURON {
    THREADSAFE
    POINT_PROCESS ProbAMPANMDA_EMS

    GLOBAL tau_r_AMPA
    RANGE tau_d_AMPA, g_AMPA, i_AMPA

    GLOBAL tau_r_NMDA, tau_d_NMDA
    RANGE g_NMDA, i_NMDA

    RANGE Use, u, Dep, Fac, u0, mg, tsyn
    RANGE unoccupied, occupied, Nrrp

    RANGE g, NMDA_ratio
    RANGE A_AMPA_step, B_AMPA_step, A_NMDA_step, B_NMDA_step
    GLOBAL e
    NONSPECIFIC_CURRENT i
    BBCOREPOINTER rng
    RANGE synapseID, selected_for_report, verboseLevel
}

PARAMETER {
        tau_r_AMPA = 0.2   (ms)  : dual-exponential conductance profile
        tau_d_AMPA = 1.7    (ms)  : IMPORTANT: tau_r < tau_d
        tau_r_NMDA = 0.29   (ms) : dual-exponential conductance profile
        tau_d_NMDA = 43     (ms) : IMPORTANT: tau_r < tau_d
        Use = 1.0   (1)   : Utilization of synaptic efficacy (just initial values! Use, Dep and Fac are overwritten by BlueBuilder assigned values)
        Dep = 100   (ms)  : relaxation time constant from depression
        Fac = 10   (ms)  :  relaxation time constant from facilitation
        e = 0     (mV)  : AMPA and NMDA reversal potential
        mg = 1   (mM)  : initial concentration of mg2+
        gmax = .001 (uS) : weight conversion factor (from nS to uS)
        u0 = 0 :initial value of u, which is the running value of release probability
        Nrrp = 1 (1)  : Number of total release sites for given contact
        synapseID = 0
        verboseLevel = 0
        selected_for_report = 0
        NMDA_ratio = 0.71 (1) : The ratio of NMDA to AMPA
}

COMMENT
The Verbatim block is needed to generate random nos. from a uniform distribution between 0 and 1
for comparison with Pr to decide whether to activate the synapse or not
ENDCOMMENT

VERBATIM

#include<stdlib.h>
#include<stdio.h>
#include<math.h>
#include "nrnran123.h"

double nrn_random_pick(void* r);
void* nrn_random_arg(int argpos);

ENDVERBATIM


ASSIGNED {

        v (mV)
        i (nA)
        i_AMPA (nA)
        i_NMDA (nA)
        g_AMPA (uS)
        g_NMDA (uS)
        g (uS)
        factor_AMPA
        factor_NMDA
        A_AMPA_step
        B_AMPA_step
        A_NMDA_step
        B_NMDA_step
        rng
        mggate
        usingR123            : TEMPORARY until mcellran4 completely deprecated

        : MVR
        unoccupied (1) : no. of unoccupied sites following release event
        occupied   (1) : no. of occupied sites following one epoch of recovery
        tsyn (ms) : the time of the last spike
        u (1) : running release probability
}


STATE {

        A_AMPA       : AMPA state variable to construct the dual-exponential profile - decays with conductance tau_r_AMPA
        B_AMPA       : AMPA state variable to construct the dual-exponential profile - decays with conductance tau_d_AMPA
        A_NMDA       : NMDA state variable to construct the dual-exponential profile - decays with conductance tau_r_NMDA
        B_NMDA       : NMDA state variable to construct the dual-exponential profile - decays with conductance tau_d_NMDA
}


INITIAL {
        LOCAL tp_AMPA, tp_NMDA

        tsyn = 0
        u=u0

        : MVR
        unoccupied = 0
        occupied = Nrrp

        A_AMPA = 0
        B_AMPA = 0

        A_NMDA = 0
        B_NMDA = 0

        tp_AMPA = (tau_r_AMPA*tau_d_AMPA)/(tau_d_AMPA-tau_r_AMPA)*log(tau_d_AMPA/tau_r_AMPA) :time to peak of the conductance
        tp_NMDA = (tau_r_NMDA*tau_d_NMDA)/(tau_d_NMDA-tau_r_NMDA)*log(tau_d_NMDA/tau_r_NMDA) :time to peak of the conductance

        factor_AMPA = -exp(-tp_AMPA/tau_r_AMPA)+exp(-tp_AMPA/tau_d_AMPA) :AMPA Normalization factor - so that when t = tp_AMPA, gsyn = gpeak
        factor_AMPA = 1/factor_AMPA

        factor_NMDA = -exp(-tp_NMDA/tau_r_NMDA)+exp(-tp_NMDA/tau_d_NMDA) :NMDA Normalization factor - so that when t = tp_NMDA, gsyn = gpeak
        factor_NMDA = 1/factor_NMDA

        A_AMPA_step = exp(dt*(( - 1.0 ) / tau_r_AMPA))
        B_AMPA_step = exp(dt*(( - 1.0 ) / tau_d_AMPA))
        A_NMDA_step = exp(dt*(( - 1.0 ) / tau_r_NMDA))
        B_NMDA_step = exp(dt*(( - 1.0 ) / tau_d_NMDA))

        VERBATIM
        if( usingR123 ) {
            nrnran123_setseq((nrnran123_State*)_p_rng, 0, 0);
        }
        ENDVERBATIM
}

BREAKPOINT {

        SOLVE state
        mggate = 1 / (1 + exp(0.062 (/mV) * -(v)) * (mg / 3.57 (mM))) :mggate kinetics - Jahr & Stevens 1990
        g_AMPA = gmax*(B_AMPA-A_AMPA) :compute time varying conductance as the difference of state variables B_AMPA and A_AMPA
        g_NMDA = gmax*(B_NMDA-A_NMDA) * mggate :compute time varying conductance as the difference of state variables B_NMDA and A_NMDA and mggate kinetics
        g = g_AMPA + g_NMDA
        i_AMPA = g_AMPA*(v-e) :compute the AMPA driving force based on the time varying conductance, membrane potential, and AMPA reversal
        i_NMDA = g_NMDA*(v-e) :compute the NMDA driving force based on the time varying conductance, membrane potential, and NMDA reversal
        i = i_AMPA + i_NMDA
}

PROCEDURE state() {
        A_AMPA = A_AMPA*A_AMPA_step
        B_AMPA = B_AMPA*B_AMPA_step
        A_NMDA = A_NMDA*A_NMDA_step
        B_NMDA = B_NMDA*B_NMDA_step
}


NET_RECEIVE (weight,weight_AMPA, weight_NMDA, Psurv) {
    LOCAL result, ves, occu
    weight_AMPA = weight
    weight_NMDA = weight * NMDA_ratio
    : Locals:
    : Psurv - survival probability of unrecovered state

    INITIAL {
    }

    : Do not perform any calculations if the synapse (netcon) is deactivated. This avoids drawing from
    : random number stream. Also, disable in case of t < 0 (in case of ForwardSkip) which causes numerical
    : instability if synapses are activated.
    if(  weight <= 0 || t < 0 ) {
    VERBATIM
        return;
    ENDVERBATIM
    }

    : calc u at event-
    if (Fac > 0) {
        u = u*exp(-(t - tsyn)/Fac) :update facilitation variable if Fac>0 Eq. 2 in Fuhrmann et al.
    } else {
        u = Use
    }
    if(Fac > 0){
        u = u + Use*(1-u) :update facilitation variable if Fac>0 Eq. 2 in Fuhrmann et al.
    }

    : recovery
    FROM counter = 0 TO (unoccupied - 1) {
        : Iterate over all unoccupied sites and compute how many recover
        Psurv = exp(-(t-tsyn)/Dep)
        result = urand()
        if (result>Psurv) {
            occupied = occupied + 1     : recover a previously unoccupied site
            if( verboseLevel > 0 ) {
                UNITSOFF
                printf( "Recovered! %f at time %g: Psurv = %g, urand=%g\n", synapseID, t, Psurv, result )
                UNITSON
            }
        }
    }

    ves = 0                  : Initialize the number of released vesicles to 0
    occu = occupied - 1  : Store the number of occupied sites in a local variable

    FROM counter = 0 TO occu {
        : iterate over all occupied sites and compute how many release
        result = urand()
        if (result<u) {
            : release a single site!
            occupied = occupied - 1  : decrease the number of occupied sites by 1
            ves = ves + 1            : increase number of relesed vesicles by 1
        }
    }

    : Update number of unoccupied sites
    unoccupied = Nrrp - occupied

    : Update tsyn
    : tsyn knows about all spikes, not only those that released
    : i.e. each spike can increase the u, regardless of recovered state.
    :      and each spike trigger an evaluation of recovery
    tsyn = t

    if (ves > 0) { :no need to evaluate unless we have vesicle release
        A_AMPA = A_AMPA + ves/Nrrp*weight_AMPA*factor_AMPA
        B_AMPA = B_AMPA + ves/Nrrp*weight_AMPA*factor_AMPA
        A_NMDA = A_NMDA + ves/Nrrp*weight_NMDA*factor_NMDA
        B_NMDA = B_NMDA + ves/Nrrp*weight_NMDA*factor_NMDA

        if ( verboseLevel > 0 ) {
            UNITSOFF
            printf( "Release! %f at time %g: vals %g %g %g %g\n", synapseID, t, A_AMPA, weight_AMPA, factor_AMPA, weight )
            UNITSON
        }

    } else {
        : total release failure
        if ( verboseLevel > 0 ) {
            UNITSOFF
            printf( " || SYN_ID: %f, release failure || ", synapseID )
            UNITSON
        }
    }
}


PROCEDURE setRNG() {
VERBATIM
    #ifndef CORENEURON_BUILD
    // For compatibility, allow for either MCellRan4 or Random123
    // Distinguish by the arg types
    // Object => MCellRan4, seeds (double) => Random123
    usingR123 = 0;
    if( ifarg(1) && hoc_is_double_arg(1) ) {
        nrnran123_State** pv = (nrnran123_State**)(&_p_rng);
        uint32_t a2 = 0;
        uint32_t a3 = 0;

        if (*pv) {
            nrnran123_deletestream(*pv);
            *pv = (nrnran123_State*)0;
        }
        if (ifarg(2)) {
            a2 = (uint32_t)*getarg(2);
        }
        if (ifarg(3)) {
            a3 = (uint32_t)*getarg(3);
        }
        *pv = nrnran123_newstream3((uint32_t)*getarg(1), a2, a3);
        usingR123 = 1;
    } else if( ifarg(1) ) {   // not a double, so assume hoc object type
        void** pv = (void**)(&_p_rng);
        *pv = nrn_random_arg(1);
    } else {  // no arg, so clear pointer
        void** pv = (void**)(&_p_rng);
        *pv = (void*)0;
    }
    #endif
ENDVERBATIM
}


FUNCTION urand() {
VERBATIM
    double value = 0.0;
    if ( usingR123 ) {
        value = nrnran123_dblpick((nrnran123_State*)_p_rng);
    } else if (_p_rng) {
        #ifndef CORENEURON_BUILD
        value = nrn_random_pick(_p_rng);
        #endif
    } else {
        // Note: prior versions used scop_random(1), but since we never use this model without configuring the rng.  Maybe should throw error?
        value = 0.0;
    }
    _lurand = value;
ENDVERBATIM
}


FUNCTION bbsavestate() {
        bbsavestate = 0
VERBATIM
#ifndef CORENEURON_BUILD
        /* first arg is direction (0 save, 1 restore), second is array*/
        /* if first arg is -1, fill xdir with the size of the array */
        double *xdir, *xval, *hoc_pgetarg();
        long nrn_get_random_sequence(void* r);
        void nrn_set_random_sequence(void* r, int val);
        xdir = hoc_pgetarg(1);
        xval = hoc_pgetarg(2);
        if (_p_rng) {
            // tell how many items need saving
            if (*xdir == -1) {  // count items
                if( usingR123 ) {
                    *xdir = 2.0;
                } else {
                    *xdir = 1.0;
                }
                return 0.0;
            } else if(*xdir ==0 ) {  // save
                if( usingR123 ) {
                    uint32_t seq;
                    char which;
                    nrnran123_getseq( (nrnran123_State*)_p_rng, &seq, &which );
                    xval[0] = (double) seq;
                    xval[1] = (double) which;
                } else {
                    xval[0] = (double)nrn_get_random_sequence(_p_rng);
                }
            } else {  // restore
                if( usingR123 ) {
                    nrnran123_setseq( (nrnran123_State*)_p_rng, (uint32_t)xval[0], (char)xval[1] );
                } else {
                    nrn_set_random_sequence(_p_rng, (long)(xval[0]));
                }
            }
        }
#endif
ENDVERBATIM
}

FUNCTION toggleVerbose() {
    verboseLevel = 1-verboseLevel
}


VERBATIM
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
  if (d) {
    uint32_t* di = ((uint32_t*)d) + *offset;
    nrnran123_State** pv = (nrnran123_State**)(&_p_rng);
    nrnran123_getids3(*pv, di, di+1, di+2);

    unsigned char which;
    nrnran123_getseq(*pv, di+3, &which);
    di[4] = (int)which;
    //printf("ProbAMPANMDA_EMS bbcore_write %d %d %d\n", di[0], di[1], di[2]);
    }
  *offset += 5;
}

static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
  assert(!_p_rng);
  uint32_t* di = ((uint32_t*)d) + *offset;
  if (di[0] != 0 || di[1] != 0 || di[2] != 0) {
      nrnran123_State** pv = (nrnran123_State**)(&_p_rng);
      *pv = nrnran123_newstream3(di[0], di[1], di[2]);
      char which = (char)di[4];
      nrnran123_setseq(*pv, di[3], which);
  }
  //printf("ProbAMPANMDA_EMS bbcore_read %d %d %d\n", di[0], di[1], di[2]);
  *offset += 5;
}
ENDVERBATIM

