#include <fstream>
#include <iostream>
#include <vector>

#include "csma_cd_sim.hpp"

int main(void)
{
    const std::vector<StationPlan> plans = {
        { "A", 2, 3u, 0 },
        { "B", 2, 7u, 0 },
        { "C", 1, 11u, 1 }
    };
    SimulationResult result = run_csma_cd_simulation(plans, 3, 128);
    std::ofstream output("csma_cd_demo_output.txt");

    if (!output) {
        std::cerr << "Failed to write output file.\n";
        return 1;
    }

    output << "completed: " << (result.completed ? "yes" : "no") << "\n";
    output << "total slots: " << result.total_slots << "\n";
    output << "collision events: " << result.collision_events << "\n";
    output << "logs:\n";
    for (size_t i = 0; i < result.log.size(); ++i) {
        output << "  " << result.log[i] << "\n";
    }
    output << "station summary:\n";
    for (size_t i = 0; i < result.stations.size(); ++i) {
        output << "  " << result.stations[i].name
               << " sent=" << result.stations[i].frames_sent
               << " attempts=" << result.stations[i].attempts
               << " collisions=" << result.stations[i].collisions << "\n";
    }

    std::cout << "CSMA/CD simulation finished. See csma_cd_demo_output.txt\n";
    return 0;
}
