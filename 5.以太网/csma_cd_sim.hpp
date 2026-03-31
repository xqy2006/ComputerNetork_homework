#ifndef CSMA_CD_SIM_HPP
#define CSMA_CD_SIM_HPP

#include <string>
#include <vector>

struct StationPlan {
    std::string name;
    int frames_to_send;
    unsigned int seed;
    int initial_ready_slot;
};

struct StationSummary {
    std::string name;
    int frames_sent;
    int attempts;
    int collisions;
};

struct SimulationResult {
    bool completed;
    int total_slots;
    int collision_events;
    std::vector<StationSummary> stations;
    std::vector<std::string> log;
};

SimulationResult run_csma_cd_simulation(
    const std::vector<StationPlan> &plans,
    int frame_slots,
    int max_slots
);

#endif
