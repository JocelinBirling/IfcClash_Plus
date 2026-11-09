// IfcClash_Plus engine — element identity (SPEC_OptimisationInCPP, "Clé d'élément").
//
// Internally an element is (file_index, entity_id): the STEP instance id is
// exact, even when a GlobalId is duplicated. The GlobalId is the exchange key
// shared with Python and the .ifcview; it is carried alongside, never used to
// merge two entities.
#pragma once

#include <cstdint>
#include <string>
#include <tuple>
#include <utility>

namespace ifcclash {

struct ElementKey {
    uint32_t    file_index = 0;   // which IFC of the RuleFile
    int         entity_id  = 0;   // STEP id (#123), unique inside the file
    std::string global_id;        // exchange key (may be duplicated in a bad file)

    friend bool operator==(const ElementKey& a, const ElementKey& b) {
        return a.file_index == b.file_index && a.entity_id == b.entity_id;
    }
    friend bool operator!=(const ElementKey& a, const ElementKey& b) { return !(a == b); }

    // Deterministic order of the results: by file, then GlobalId, then id
    // (the id breaks the tie of a duplicated GlobalId).
    friend bool operator<(const ElementKey& a, const ElementKey& b) {
        return std::tie(a.file_index, a.global_id, a.entity_id) <
               std::tie(b.file_index, b.global_id, b.entity_id);
    }
};

struct ElementKeyHash {
    size_t operator()(const ElementKey& k) const noexcept {
        return (static_cast<size_t>(k.file_index) << 40) ^ static_cast<size_t>(k.entity_id);
    }
};

using KeyPair = std::pair<ElementKey, ElementKey>;

}  // namespace ifcclash
