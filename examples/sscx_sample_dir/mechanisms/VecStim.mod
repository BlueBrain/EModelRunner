COMMENT
/**
 * @file VecStim.mod
 * @brief
 * @author king
 * @date 2011-03-16
 * @remark Copyright © BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT


: Vector stream of events
NEURON {
    THREADSAFE
    ARTIFICIAL_CELL VecStim
    RANGE ping, index, etime
}

PARAMETER {
    ping = 1 (ms)
}

ASSIGNED {
    index  : The index(+1) of the last retrieved element. See element()
    etime (ms)
    space
}


VERBATIM
#ifdef STIM_DEBUG
# define debug_printf(...) printf(__VA_ARGS__)
#else
# define debug_printf(...)
#endif
ENDVERBATIM


INITIAL {
VERBATIM
 #ifndef CORENEURON_BUILD
 // This Mechanism is not useful for CoreNeuron, since it has its own implementation
 // Therefore we should avoid even compiling it together, but for backwards compat keep guards
ENDVERBATIM
    index = 0
    if(element()) {
        net_send(etime - t, 1)
    }
    if (ping > 0) {
        net_send(ping, 2)
    }
VERBATIM
 #endif
ENDVERBATIM
}


NET_RECEIVE (w) {
    if (flag == 1) {  : deliver event
    VERBATIM
        debug_printf("[VecStim] net_event(): index=%d, etime=%g, t=%g\n", (int)index - 1, etime, t);
    ENDVERBATIM
        net_event(t)

        : schedule next event
        if (element() > 0) {
            if (etime < t) {
                printf("[VecStim] WARNING: spike time (%g ms) before current time (%g ms)\n",etime,t)
            } else {
                net_send(etime - t, 1)
            }
        }
    } else if (flag == 2) { : ping - reset index to 0
        :printf("flag=2, etime=%g, t=%g, ping=%g, index=%g\n",etime,t,ping,index)
        if (index == -2) { : play() has been called
            printf("[VecStim] Detected new time vector.\n")
            restartEvent()
        }
        net_send(ping, 2)
    }
}


COMMENT
/**
 * Resume the event delivery loop for NEURON restore.
 */
ENDCOMMENT
PROCEDURE restartEvent() {
    index = 0
VERBATIM
#ifndef CORENEURON_BUILD
    while (element(_threadargs_) && etime < t) {}  // Ignore past events
    if (index > 0) {
        // Invoke low-level artcell_net_send, since generic NMODL net_send is only
        // available in INITIAL and NET_RECEIVE blocks. It takes an ABSOLUTE time instead
        debug_printf("[VecStim] restartEvent(delay=%g): index=%d, etime=%g, t=%g\n", delay, (int)index - 1, etime, t);
        artcell_net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
    }
#endif
ENDVERBATIM
}


VERBATIM
extern double* vector_vec();
extern int vector_capacity();
extern void* vector_arg();
ENDVERBATIM


COMMENT
/**
 * \brief Retrieves an element (spike time) from the source vector, store in etime.
 *
 * \return The index+1 of the element (=~ true). Otherwise 0 (not initialized or end)
 *
 * NOTE: For back-compat index is incremented *after* the element is retrieved, making
 *   it like a base-1 indexing scheme, or representing the next elements index.
 */
ENDCOMMENT
FUNCTION element() {
VERBATIM
    const int i = (int)index;
    void* const vv = *((void**)(&space));
    int size; double* px;
    if (i < 0 || vv == NULL)
        return 0;

    size = vector_capacity(vv);
    px = vector_vec(vv);
    if (i < size) {
        etime = px[i];
        index += 1.;
        debug_printf("[VecStim] element(): index=%d, etime=%g, t=%g\n", (int)index - 1, etime, t);
        return index;
    }
    index = -1;
    return 0;
ENDVERBATIM
}


PROCEDURE play() {
VERBATIM
    #ifndef CORENEURON_BUILD
    void** vv;
    vv = (void**)(&space);
    *vv = NULL;
    if (ifarg(1)) {
        *vv = vector_arg(1);
    }
    index = -2;
    #endif
ENDVERBATIM
}

