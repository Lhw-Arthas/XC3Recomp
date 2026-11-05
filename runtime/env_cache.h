// [XC3] perf: getenv() cached per call site. Included last in files whose debug switches are read on hot paths
// (per draw / per texture check): getenv scans the whole environment each call (strchr / strncmp in ucrtbase were
// ~5 % of the render thread). The environment is only changed before the game starts (main_boot.c relaunch), so a
// value read once stays right. The race on first use is benign (both threads store the same pointer).
#pragma once
#include <stdlib.h>
#include <string.h>

static inline const char *rt_getenv_compat(const char *name) {
    if (!strncmp(name, "XCDE_", 5)) {
        char buf[64];
        buf[0] = 'X'; buf[1] = 'C'; buf[2] = '3'; buf[3] = '_';
        strncpy(buf + 4, name + 5, sizeof(buf) - 5);
        buf[sizeof(buf) - 1] = 0;
        const char *v = (getenv)(buf);
        if (v && *v) return v;
    }
    return (getenv)(name);
}

#define getenv(name) ({ static const char *env_c_v_; static volatile int env_c_i_; \
    if (!env_c_i_) { env_c_v_ = rt_getenv_compat(name); env_c_i_ = 1; } env_c_v_; })
