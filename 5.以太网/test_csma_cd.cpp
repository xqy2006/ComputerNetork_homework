#include <cstdio>
#include <cstdlib>
#include <vector>

#include "csma_cd_sim.hpp"

static void expect_true(const char *name, bool condition)
{
    if (!condition) {
        std::fprintf(stderr, "%s failed\n", name);
        std::exit(1);
    }
}

static void test_simulation_completes(void)
{
    const std::vector<StationPlan> plans = {
        { "A", 1, 1u, 0 },
        { "B", 1, 2u, 0 }
    };
    SimulationResult result = run_csma_cd_simulation(plans, 2, 32);

    expect_true("simulation_completes", result.completed);
    expect_true("collision_happened", result.collision_events >= 1);
    expect_true("station_a_sent", result.stations[0].frames_sent == 1);
    expect_true("station_b_sent", result.stations[1].frames_sent == 1);
}

static void test_multiple_frames_sent(void)
{
    const std::vector<StationPlan> plans = {
        { "A", 2, 3u, 0 },
        { "B", 2, 7u, 0 },
        { "C", 1, 11u, 1 }
    };
    SimulationResult result = run_csma_cd_simulation(plans, 3, 128);

    expect_true("multiple_frames_complete", result.completed);
    expect_true("station_a_two_frames", result.stations[0].frames_sent == 2);
    expect_true("station_b_two_frames", result.stations[1].frames_sent == 2);
    expect_true("station_c_one_frame", result.stations[2].frames_sent == 1);
}

int main(void)
{
    test_simulation_completes();
    test_multiple_frames_sent();

    std::puts("All csma_cd tests passed.");
    return 0;
}
