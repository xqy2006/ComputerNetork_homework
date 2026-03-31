#include "csma_cd_sim.hpp"

#include <algorithm>
#include <condition_variable>
#include <mutex>
#include <random>
#include <sstream>
#include <thread>

namespace {

enum SlotOutcome {
    SLOT_IDLE = 0,
    SLOT_DEFER = 1,
    SLOT_SUCCESS = 2,
    SLOT_COLLISION = 3
};

struct SharedState {
    explicit SharedState(int count)
        : station_count(count),
          phase(0),
          current_slot(-1),
          slot_idle_at_start(true),
          stop(false),
          submitted(0),
          resolved(0),
          attempts(count, false),
          outcomes(count, SLOT_IDLE),
          frames_sent(count, 0),
          busy_remaining(0),
          transmitter(-1),
          collision_events(0) {
    }

    int station_count;
    int phase;
    int current_slot;
    bool slot_idle_at_start;
    bool stop;
    int submitted;
    int resolved;
    std::vector<bool> attempts;
    std::vector<SlotOutcome> outcomes;
    std::vector<int> frames_sent;
    int busy_remaining;
    int transmitter;
    int collision_events;
    std::vector<std::string> log;
    std::mutex mutex;
    std::condition_variable cv;
};

void station_worker(
    int id,
    const StationPlan &plan,
    SharedState &shared,
    std::vector<StationSummary> &summaries
)
{
    std::minstd_rand rng(plan.seed);
    int frames_left = plan.frames_to_send;
    int next_ready_slot = plan.initial_ready_slot;
    int collision_count_for_frame = 0;
    int seen_slot = -1;

    while (true) {
        int slot;
        int phase;
        bool idle_at_start;
        bool attempt = false;
        SlotOutcome outcome;

        {
            std::unique_lock<std::mutex> lock(shared.mutex);
            shared.cv.wait(lock, [&] { return shared.stop || shared.current_slot != seen_slot; });
            if (shared.stop) {
                break;
            }

            slot = shared.current_slot;
            phase = shared.phase;
            idle_at_start = shared.slot_idle_at_start;

            if (phase != 1) {
                attempt = frames_left > 0 && idle_at_start && slot >= next_ready_slot;
                shared.attempts[id] = attempt;
                ++shared.submitted;
                if (shared.submitted == shared.station_count) {
                    shared.cv.notify_all();
                }

                shared.cv.wait(lock, [&] { return shared.stop || (shared.current_slot == slot && shared.phase == 1); });
                if (shared.stop) {
                    break;
                }
            }

            outcome = shared.outcomes[id];
            seen_slot = slot;

            if (outcome == SLOT_SUCCESS) {
                --frames_left;
                ++summaries[id].frames_sent;
                ++summaries[id].attempts;
                shared.frames_sent[id] = summaries[id].frames_sent;
                collision_count_for_frame = 0;
                next_ready_slot = slot + 1 + std::max(shared.busy_remaining, 0);
            } else if (outcome == SLOT_COLLISION) {
                int backoff_window;
                int random_slots;

                ++summaries[id].attempts;
                ++summaries[id].collisions;
                ++collision_count_for_frame;
                backoff_window = 1 << std::min(collision_count_for_frame, 10);
                random_slots = (int) (rng() % backoff_window);
                next_ready_slot = slot + 1 + random_slots;
            }

            ++shared.resolved;
            if (shared.resolved == shared.station_count) {
                shared.cv.notify_all();
            }
        }
    }
}

} // namespace

SimulationResult run_csma_cd_simulation(
    const std::vector<StationPlan> &plans,
    int frame_slots,
    int max_slots
)
{
    SharedState shared((int) plans.size());
    std::vector<StationSummary> summaries(plans.size());
    std::vector<std::thread> threads;
    SimulationResult result = {};
    int slot;

    if (plans.empty() || frame_slots <= 0 || max_slots <= 0) {
        result.completed = false;
        return result;
    }

    for (size_t i = 0; i < plans.size(); ++i) {
        summaries[i].name = plans[i].name;
        summaries[i].frames_sent = 0;
        summaries[i].attempts = 0;
        summaries[i].collisions = 0;
        threads.emplace_back(station_worker, (int) i, std::cref(plans[i]), std::ref(shared), std::ref(summaries));
    }

    for (slot = 0; slot < max_slots; ++slot) {
        std::unique_lock<std::mutex> lock(shared.mutex);
        int i;
        int finished = 0;

        for (i = 0; i < (int) plans.size(); ++i) {
            if (shared.frames_sent[i] >= plans[i].frames_to_send) {
                ++finished;
            }
        }
        if (finished == (int) plans.size() && shared.busy_remaining == 0) {
            result.completed = true;
            break;
        }

        shared.current_slot = slot;
        shared.phase = 0;
        shared.slot_idle_at_start = (shared.busy_remaining == 0);
        shared.submitted = 0;
        shared.resolved = 0;
        std::fill(shared.attempts.begin(), shared.attempts.end(), false);
        std::fill(shared.outcomes.begin(), shared.outcomes.end(), SLOT_DEFER);
        shared.cv.notify_all();

        shared.cv.wait(lock, [&] { return shared.submitted == shared.station_count; });

        if (shared.busy_remaining > 0) {
            std::fill(shared.outcomes.begin(), shared.outcomes.end(), SLOT_DEFER);
            --shared.busy_remaining;
            if (shared.busy_remaining == 0) {
                shared.transmitter = -1;
            }
        } else {
            std::vector<int> contenders;
            std::ostringstream oss;

            for (i = 0; i < shared.station_count; ++i) {
                if (shared.attempts[i]) {
                    contenders.push_back(i);
                }
            }

            std::fill(shared.outcomes.begin(), shared.outcomes.end(), SLOT_IDLE);

            if (contenders.size() == 1) {
                int winner = contenders.front();
                shared.outcomes[winner] = SLOT_SUCCESS;
                shared.transmitter = winner;
                shared.busy_remaining = frame_slots - 1;

                oss << "slot " << slot << ": " << plans[winner].name
                    << " starts transmitting frame " << (summaries[winner].frames_sent + 1);
                shared.log.push_back(oss.str());
            } else if (contenders.size() > 1) {
                shared.collision_events++;
                oss << "slot " << slot << ": collision among";
                for (size_t k = 0; k < contenders.size(); ++k) {
                    shared.outcomes[contenders[k]] = SLOT_COLLISION;
                    oss << (k == 0 ? " " : ", ") << plans[contenders[k]].name;
                }
                shared.log.push_back(oss.str());
            }
        }

        shared.phase = 1;
        shared.cv.notify_all();
        shared.cv.wait(lock, [&] { return shared.resolved == shared.station_count; });
    }

    {
        std::lock_guard<std::mutex> lock(shared.mutex);
        shared.stop = true;
        shared.cv.notify_all();
    }

    for (size_t i = 0; i < threads.size(); ++i) {
        threads[i].join();
    }

    result.completed = result.completed || (slot < max_slots);
    result.total_slots = slot;
    result.collision_events = shared.collision_events;
    result.stations = summaries;
    result.log = shared.log;
    return result;
}
