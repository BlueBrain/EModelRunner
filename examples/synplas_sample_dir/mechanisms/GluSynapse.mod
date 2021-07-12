COMMENT
/**
 * @file GluSynapse.mod
 * @brief Probabilistic synapse featuring long-term plasticity
 * @author king, chindemi, rossert
 * @date 2019-09-20
 * @version 1.0.0
 * @remark Copyright BBP/EPFL 2005-2019; All rights reserved.
           Do not distribute without further notice.
 */
 Glutamatergic synapse model featuring:
1) AMPA receptor with a dual-exponential conductance profile.
2) NMDA receptor  with a dual-exponential conductance profile and magnesium
   block as described in Jahr and Stevens 1990.
3) Tsodyks-Markram presynaptic short-term plasticity as Barros et al. 2019.
   Implementation based on the work of Eilif Muller, Michael Reimann and
   Srikanth Ramaswamy (Blue Brain Project, August 2011), who introduced the
   2-state Markov model of vesicle release. The new model is an extension of
   Fuhrmann et al. 2002, motivated by the following constraints:
        a) No consumption on failure
        b) No release until recovery
        c) Same ensemble averaged trace as canonical Tsodyks-Markram using same
           parameters determined from experiment.
   For a pre-synaptic spike or external spontaneous release trigger event, the
   synapse will only release if it is in the recovered state, and with
   probability u (which follows facilitation dynamics). If it releases, it will
   transition to the unrecovered state. Recovery is as a Poisson process with
   rate 1/Dep.
   John Rahmon and Giuseppe Chindemi introduced multi-vesicular release as an
   extension of the 2-state Markov model of vesicle release described above
   (Blue Brain Project, February 2017).
4) NMDAR-mediated calcium current. Fractional calcium current Pf_NMDA from
   Schneggenburger et al. 1993. Fractional NMDAR conductance treated as a
   calcium-only permeable channel with Erev = 40 mV independent of extracellular
   calcium concentration (see Jahr and Stevens 1993). Implemented by Christian
   Rossert and Giuseppe Chindemi (Blue Brain Project, 2016).
5) Spine volume.
6) VDCC.
7) Postsynaptic calcium dynamics.
8) Long-term synaptic plasticity. Calcium-based STDP model based on Graupner and
   Brunel 2012.
Model implementation, optimization and simulation curated by James King (Blue
Brain Project, 2019).
ENDCOMMENT

TITLE Glutamatergic synapse

NEURON {
    THREADSAFE
    POINT_PROCESS GluSynapse
    : AMPA Receptor
    GLOBAL tau_r_AMPA, E_AMPA
    RANGE tau_d_AMPA, gmax0_AMPA, gmax_d_AMPA, gmax_p_AMPA, g_AMPA
    : NMDA Receptor
    GLOBAL mgo_NMDA, scale_NMDA, slope_NMDA
    GLOBAL tau_r_NMDA, tau_d_NMDA, E_NMDA
    RANGE gmax_NMDA, g_NMDA
    : Stochastic Tsodyks-Markram Multi-Vesicular Release
    RANGE Use0_TM, Dep_TM, Fac_TM, Nrrp_TM
    RANGE Use_d_TM, Use_p_TM
    BBCOREPOINTER rng_TM
    : NMDAR-mediated calcium current
    RANGE ica_NMDA
    : Spine
    RANGE volume_CR
    : VDCC (R-type)
    GLOBAL ljp_VDCC, vhm_VDCC, km_VDCC, mtau_VDCC, vhh_VDCC, kh_VDCC, htau_VDCC, gca_bar_VDCC
    RANGE ica_VDCC
    : Postsynaptic Ca2+ dynamics
    GLOBAL gamma_ca_CR, tau_ca_CR, min_ca_CR, cao_CR
    : Long-term synaptic plasticity
    GLOBAL rho_star_GB, tau_ind_GB, tau_exp_GB, tau_effca_GB
    GLOBAL gamma_d_GB, gamma_p_GB
    RANGE theta_d_GB, theta_p_GB, rho0_GB, dep_GB, pot_GB
    : Misc
    RANGE vsyn, synapseID, selected_for_report, verbose
    NONSPECIFIC_CURRENT i
}


UNITS {
    (nA)    = (nanoamp)
    (mV)    = (millivolt)
    (uS)    = (microsiemens)
    (nS)    = (nanosiemens)
    (pS)    = (picosiemens)
    (umho)  = (micromho)
    (um)    = (micrometers)
    (mM)    = (milli/liter)
    (uM)    = (micro/liter)
    FARADAY = (faraday) (coulomb)
    PI      = (pi)      (1)
    R       = (k-mole)  (joule/degC)
}


PARAMETER {
    celsius                     (degC)
    : AMPA Receptor
    tau_r_AMPA      = 0.2       (ms)        : Tau rise, dual-exponential conductance profile
    tau_d_AMPA      = 1.7       (ms)        : Tau decay, IMPORTANT: tau_r < tau_d
    E_AMPA          = 0         (mV)        : Reversal potential
    gmax0_AMPA      = 1.0       (nS)        : Initial peak conductance
    gmax_d_AMPA     = 1.0       (nS)        : Peak conductance in the depressed state
    gmax_p_AMPA     = 2.0       (nS)        : Peak conductance in the potentitated state
    : NMDA Receptor
    mgo_NMDA        = 1         (mM)        : Extracellular magnesium concentration
    scale_NMDA      = 2.552     (mM)        : Scale of the mg block (Vargas-Caballero and Robinson 2003)
    slope_NMDA      = 0.072     (/mV)       : Slope of the ma block (Vargas-Caballero and Robinson 2003)
    tau_r_NMDA      = 0.29      (ms)        : Tau rise, dual-exponential conductance profile
    tau_d_NMDA      = 70        (ms)        : Tau decay, IMPORTANT: tau_r < tau_d
    E_NMDA          = -3        (mV)        : Reversal potential (Vargas-Caballero and Robinson 2003)
    gmax_NMDA       = 0.55      (nS)        : Peak conductance
    : Stochastic Tsodyks-Markram Multi-Vesicular Release
    Use0_TM         = 0.5       (1)         : Initial utilization of synaptic efficacy
    Dep_TM          = 100       (ms)        : Relaxation time constant from depression
    Fac_TM          = 10        (ms)        : Relaxation time constant from facilitation
    Nrrp_TM         = 1         (1)         : Number of release sites for given contact
    Use_d_TM        = 0.2       (1)         : Depressed Use
    Use_p_TM        = 0.8       (1)         : Potentiated Use
    : Spine
    volume_CR       = 0.087     (um3)       : From spine data by Ruth Benavides-Piccione (unpublished)
    : VDCC (R-type)
    gca_bar_VDCC    = 0.0744    (nS/um2)    : Density spines: 20 um-2 (Sabatini 2000), unitary conductance VGCC 3.72 pS (Bartol 2015)
    ljp_VDCC        = 0         (mV)
    vhm_VDCC        = -5.9      (mV)        : v 1/2 for act, Magee and Johnston 1995 (corrected for m*m)
    km_VDCC         = 9.5       (mV)        : act slope, Magee and Johnston 1995 (corrected for m*m)
    vhh_VDCC        = -39       (mV)        : v 1/2 for inact, Magee and Johnston 1995
    kh_VDCC         = -9.2      (mV)        : inact, Magee and Johnston 1995
    mtau_VDCC       = 1         (ms)        : max time constant (guess)
    htau_VDCC       = 27        (ms)        : max time constant 100*0.27
    : Postsynaptic Ca2+ dynamics
    gamma_ca_CR     = 0.04      (1)         : Percent of free calcium (not buffered), Sabatini et al 2002: kappa_e = 24+-11 (also 14 (2-31) or 22 (18-33))
    tau_ca_CR       = 12        (ms)        : Rate of removal of calcium, Sabatini et al 2002: 14ms (12-20ms)
    min_ca_CR       = 70e-6     (mM)        : Sabatini et al 2002: 70+-29 nM, per AP: 1.1 (0.6-8.2) uM = 1100 e-6 mM = 1100 nM
    cao_CR          = 2.0       (mM)        : Extracellular calcium concentration in slices
    : Long-term synaptic plasticity
    rho_star_GB     = 0.5       (1)
    tau_ind_GB      = 70        (s)
    tau_exp_GB      = 100       (s)
    tau_effca_GB    = 200       (ms)
    gamma_d_GB      = 100       (1)
    gamma_p_GB      = 450       (1)
    theta_d_GB      = 0.006     (us/liter)
    theta_p_GB      = 0.001     (us/liter)
    rho0_GB         = 0         (1)
    : Misc
    synapseID       = 0
    verbose         = 0
    selected_for_report = 0
}

VERBATIM
/**
 * This Verbatim block is needed to generate random numbers from a uniform
 * distribution U(0, 1).
 */
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "nrnran123.h"
double nrn_random_pick(void* r);
void* nrn_random_arg(int argpos);
ENDVERBATIM

ASSIGNED {
    : AMPA Receptor
    g_AMPA          (uS)
    : NMDA Receptor
    g_NMDA          (uS)
    : Stochastic Tsodyks-Markram Multi-Vesicular Release
    rng_TM                  : Random Number Generator
    usingR123               : TEMPORARY until mcellran4 completely deprecated
    : NMDAR-mediated calcium current
    ica_NMDA        (nA)
    : VDCC (R-type)
    ica_VDCC        (nA)
    : Long-term synaptic plasticity
    dep_GB          (1)
    pot_GB          (1)
    : Misc
    v               (mV)
    vsyn            (mV)
    i               (nA)
}

STATE {
    : AMPA Receptor
    A_AMPA      (1)
    B_AMPA      (1)
    gmax_AMPA   (nS)
    : NMDA Receptor
    A_NMDA      (1)
    B_NMDA      (1)
    : Stochastic Tsodyks-Markram Multi-Vesicular Release
    Use_TM      (1)
    : VDCC (R-type)
    m_VDCC      (1)
    h_VDCC      (1)
    : Postsynaptic Ca2+ dynamics
    cai_CR      (mM)        <1e-6>
    : Long-term synaptic plasticity
    rho_GB      (1)
    effcai_GB   (us/liter)  <1e-3>
}

INITIAL{
    : AMPA Receptor
    A_AMPA      = 0
    B_AMPA      = 0
    gmax_AMPA   = gmax0_AMPA
    : NMDA Receptor
    A_NMDA      = 0
    B_NMDA      = 0
    : Stochastic Tsodyks-Markram Multi-Vesicular Release
    Use_TM      = Use0_TM
    : Postsynaptic Ca2+ dynamics
    cai_CR      = min_ca_CR
    : Long-term synaptic plasticity
    rho_GB      = rho0_GB
    effcai_GB   = 0
    dep_GB      = 0
    pot_GB      = 0
    : Initialize watchers
    net_send(0, 1)
}

BREAKPOINT {
    LOCAL Eca_syn, mggate, i_AMPA, i_NMDA, Pf_NMDA, gca_bar_abs_VDCC, gca_VDCC
    SOLVE state METHOD derivimplicit
    : AMPA Receptor
    g_AMPA = (1e-3)*gmax_AMPA*(B_AMPA - A_AMPA)
    i_AMPA = g_AMPA*(v-E_AMPA)
    : NMDA Receptor
    mggate = 1 / (1 + exp(-slope_NMDA*v) * (mgo_NMDA/scale_NMDA))
    g_NMDA = (1e-3)*gmax_NMDA*mggate*(B_NMDA - A_NMDA)
    i_NMDA = g_NMDA*(v - E_NMDA)
    : NMDAR-mediated calcium current
    Pf_NMDA  = (4*cao_CR) / (4*cao_CR + (1/1.38) * 120 (mM)) * 0.6
    ica_NMDA = Pf_NMDA*g_NMDA*(v-40.0)
    : VDCC (R-type), assuming sphere for spine head
    gca_bar_abs_VDCC = gca_bar_VDCC * 4(um2)*PI*(3(1/um3)/4*volume_CR*1/PI)^(2/3)
    gca_VDCC = (1e-3) * gca_bar_abs_VDCC * m_VDCC * m_VDCC * h_VDCC
    Eca_syn = nernst(cai_CR, cao_CR, 2)
    ica_VDCC = gca_VDCC*(v-Eca_syn)
    : Update synaptic voltage (for recording convenience)
    vsyn = v
    : Update current
    i = i_AMPA + i_NMDA + ica_VDCC
}

DERIVATIVE state {
    LOCAL minf_VDCC, hinf_VDCC
    : AMPA Receptor
    A_AMPA'      = - A_AMPA/tau_r_AMPA
    B_AMPA'      = - B_AMPA/tau_d_AMPA
    gmax_AMPA'   = (gmax_d_AMPA + rho_GB*(gmax_p_AMPA - gmax_d_AMPA) - gmax_AMPA) / ((1e3)*tau_exp_GB)
    : NMDA Receptor
    A_NMDA'      = - A_NMDA/tau_r_NMDA
    B_NMDA'      = - B_NMDA/tau_d_NMDA
    : Stochastic Tsodyks-Markram Multi-Vesicular Release
    Use_TM'      = (Use_d_TM + rho_GB*(Use_p_TM - Use_d_TM) - Use_TM) / ((1e3)*tau_exp_GB)
    : VDCC (R-type)
    minf_VDCC    = 1 / (1 + exp(((vhm_VDCC - ljp_VDCC) - v) / km_VDCC))
    hinf_VDCC    = 1 / (1 + exp(((vhh_VDCC - ljp_VDCC) - v) / kh_VDCC))
    m_VDCC'      = (minf_VDCC-m_VDCC)/mtau_VDCC
    h_VDCC'      = (hinf_VDCC-h_VDCC)/htau_VDCC
    : Postsynaptic Ca2+ dynamics
    cai_CR'      = - (1e-9)*(ica_NMDA + ica_VDCC)*gamma_ca_CR/((1e-15)*volume_CR*2*FARADAY)
                   - (cai_CR - min_ca_CR)/tau_ca_CR
    : Long-term synaptic plasticity
    effcai_GB'   = - effcai_GB/tau_effca_GB + (cai_CR - min_ca_CR)
    rho_GB'      = ( - rho_GB*(1 - rho_GB)*(rho_star_GB - rho_GB)
                     + pot_GB*gamma_p_GB*(1 - rho_GB)
                     - dep_GB*gamma_d_GB*rho_GB ) / ((1e3)*tau_ind_GB)
}

NET_RECEIVE (weight, u, tsyn (ms), recovered, unrecovered) {
    LOCAL p_rec, released, tp, factor
    INITIAL {
        weight = 1
        u = 0
        tsyn = 0 (ms)
        recovered = Nrrp_TM
        unrecovered = 0
    }
    if(verbose > 0){ UNITSOFF printf("Time = %g ms, incoming spike at synapse %g\n", t, synapseID) UNITSON }
    if(flag == 0) {
        if(weight <= 0){
            : Do not perform any calculations if the synapse (netcon) is deactivated.
            : This avoids drawing from the random stream
            : WARNING In this model *weight* is only used to activate/deactivate the
            :         synapse. The conductance is stored in gmax_AMPA and gmax_NMDA.
            if(verbose > 0){ printf("Inactive synapse, weight = %g\n", weight) }
        } else {
            : Flag 0: Regular spike
            if(verbose > 0){ printf("Flag 0, Regular spike\n") }
            : Update facilitation variable as Eq. 2 in Fuhrmann et al. 2002
            u = Use_TM + u*(1 - Use_TM)*exp(-(t - tsyn)/Fac_TM)
            if ( verbose > 0 ) { printf("\tVesicle release probability = %g\n", u) }
            : Recovery
            p_rec = 1 - exp(-(t - tsyn)/Dep_TM)
            if ( verbose > 0 ) { printf("\tVesicle recovery probability = %g\n", p_rec) }
            if ( verbose > 0 ) { printf("\tVesicle available before recovery = %g\n", recovered) }
            recovered = recovered + brand(unrecovered, p_rec)
            if ( verbose > 0 ) { printf("\tVesicles available after recovery = %g\n", recovered) }
            : Release
            released = brand(recovered, u)
            if ( verbose > 0 ) { printf("\tReleased %g vesicles out of %g\n", released, recovered) }
            : Update AMPA variables
            tp = (tau_r_AMPA*tau_d_AMPA)/(tau_d_AMPA-tau_r_AMPA)*log(tau_d_AMPA/tau_r_AMPA)  : Time to peak
            factor = 1 / (-exp(-tp/tau_r_AMPA)+exp(-tp/tau_d_AMPA))  : Normalization factor
            A_AMPA = A_AMPA + released/Nrrp_TM*factor
            B_AMPA = B_AMPA + released/Nrrp_TM*factor
            : Update NMDA variables
            tp = (tau_r_NMDA*tau_d_NMDA)/(tau_d_NMDA-tau_r_NMDA)*log(tau_d_NMDA/tau_r_NMDA)  : Time to peak
            factor = 1 / (-exp(-tp/tau_r_NMDA)+exp(-tp/tau_d_NMDA))  : Normalization factor
            A_NMDA = A_NMDA + released/Nrrp_TM*factor
            B_NMDA = B_NMDA + released/Nrrp_TM*factor
            : Update vesicle pool
            recovered = recovered - released
            unrecovered = Nrrp_TM - recovered
            if ( verbose > 0 ) { printf("\tFinal vesicle count, Recovered = %g, Unrecovered = %g, Nrrp = %g\n", recovered, unrecovered, Nrrp_TM) }
            : Update tsyn
            : tsyn knows about all spikes, not only those that released
            : i.e. each spike can increase the u, regardless of recovered state
            :      and each spike trigger an evaluation of recovery
            tsyn = t
        }
    } else if(flag == 1) {
        : Flag 1, Initialize watchers
        if(verbose > 0){ printf("Flag 1, Initialize watchers\n") }
        WATCH (effcai_GB > theta_d_GB) 2
        WATCH (effcai_GB < theta_d_GB) 3
        WATCH (effcai_GB > theta_p_GB) 4
        WATCH (effcai_GB < theta_p_GB) 5
    } else if(flag == 2) {
        : Flag 2, Activate depression mechanisms
        if(verbose > 0){ printf("Flag 2, Activate depression mechanisms\n") }
        dep_GB = 1
    } else if(flag == 3) {
        : Flag 3, Deactivate depression mechanisms
        if(verbose > 0){ printf("Flag 3, Deactivate depression mechanisms\n") }
        dep_GB = 0
    } else if(flag == 4) {
        : Flag 4, Activate potentiation mechanisms
        if(verbose > 0){ printf("Flag 4, Activate potentiation mechanisms\n") }
        pot_GB = 1
    } else if(flag == 5) {
        : Flag 5, Deactivate potentiation mechanisms
        if(verbose > 0){ printf("Flag 5, Deactivate potentiation mechanisms\n") }
        pot_GB = 0
    }
}

FUNCTION nernst(ci(mM), co(mM), z) (mV) {
    nernst = (1000) * R * (celsius + 273.15) / (z*FARADAY) * log(co/ci)
    if(verbose > 1) { UNITSOFF printf("nernst:%g R:%g temperature (c):%g \n", nernst, R, celsius) UNITSON }
}

PROCEDURE setRNG() {
    VERBATIM
    #ifndef CORENEURON_BUILD
    // For compatibility, allow for either MCellRan4 or Random123
    // Distinguish by the arg types
    // Object => MCellRan4, seeds (double) => Random123
    usingR123 = 0;
    if( ifarg(1) && hoc_is_double_arg(1) ) {
        nrnran123_State** pv = (nrnran123_State**)(&_p_rng_TM);
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
        void** pv = (void**)(&_p_rng_TM);
        *pv = nrn_random_arg(1);
    } else {  // no arg, so clear pointer
        void** pv = (void**)(&_p_rng_TM);
        *pv = (void*)0;
    }
    #endif
    ENDVERBATIM
}

FUNCTION urand() {
    VERBATIM
    double value;
    if ( usingR123 ) {
        value = nrnran123_dblpick((nrnran123_State*)_p_rng_TM);
    } else if (_p_rng_TM) {
        #ifndef CORENEURON_BUILD
        value = nrn_random_pick(_p_rng_TM);
        #endif
    } else {
        value = 0.0;
    }
    _lurand = value;
    ENDVERBATIM
}

FUNCTION brand(n, p) {
    LOCAL result, count, success
    success = 0
    FROM count = 0 TO (n - 1) {
        result = urand()
        if(result <= p) {
            success = success + 1
        }
    }
    brand = success
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
        if (_p_rng_TM) {
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
                    unsigned char which;
                    nrnran123_getseq( (nrnran123_State*)_p_rng_TM, &seq, &which );
                    xval[0] = (double) seq;
                    xval[1] = (double) which;
                } else {
                    xval[0] = (double)nrn_get_random_sequence(_p_rng_TM);
                }
            } else {  // restore
                if( usingR123 ) {
                    nrnran123_setseq( (nrnran123_State*)_p_rng_TM, (uint32_t)xval[0], (char)xval[1] );
                } else {
                    nrn_set_random_sequence(_p_rng_TM, (long)(xval[0]));
                }
            }
        }
    #endif
    ENDVERBATIM
}

VERBATIM
static void bbcore_write(double* dArray, int* iArray, int* doffset, int* ioffset, _threadargsproto_) {
    // make sure offset array non-null
    if (iArray) {
        // get handle to random123 instance
        nrnran123_State** pv = (nrnran123_State**)(&_p_rng_TM);
        // get location for storing ids
        uint32_t* ia = ((uint32_t*)iArray) + *ioffset;
        // retrieve/store identifier seeds
        nrnran123_getids3(*pv, ia, ia+1, ia+2);
        // retrieve/store stream sequence
        unsigned char which;
        nrnran123_getseq(*pv, ia+3, &which);
        ia[4] = (int)which;
    }

    // increment integer offset (2 identifier), no double data
    *ioffset += 5;
    *doffset += 0;
}

static void bbcore_read(double* dArray, int* iArray, int* doffset, int* ioffset, _threadargsproto_) {
    // make sure it's not previously set
    assert(!_p_rng_TM);
    uint32_t* ia = ((uint32_t*)iArray) + *ioffset;
    // make sure non-zero identifier seeds
    if (ia[0] != 0 || ia[1] != 0 || ia[2] != 0) {
        nrnran123_State** pv = (nrnran123_State**)(&_p_rng_TM);
        // get new stream
        *pv = nrnran123_newstream3(ia[0], ia[1], ia[2]);
        // restore sequence
        nrnran123_setseq(*pv, ia[3], (char)ia[4]);
    }
    // increment intger offset (2 identifiers), no double data
    *ioffset += 5;
    *doffset += 0;
}
ENDVERBATIM

