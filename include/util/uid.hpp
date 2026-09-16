#pragma once

#include <string>

namespace inst::util {
    std::string ComputeUidFromMmcCid();
    void SetCustomUid(const std::string& customUid);
}

