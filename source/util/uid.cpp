#include "util/uid.hpp"

#include <array>
#include <mutex>
#include <string>

#include <switch.h>

namespace inst::util {
    static std::string gCustomUid = "BAD1BB5900000000000000000000000000000000000000000000000000000000";

    void SetCustomUid(const std::string& customUid)
    {
        if (customUid.empty())
            return;
        std::string padded = customUid;
        if (padded.size() < 64)
            padded.append(64 - padded.size(), '0');
        gCustomUid = padded;
    }

    std::string ComputeUidFromMmcCid()
    {
        return gCustomUid;
    }
}

