#include <cstdlib>
#include <iostream>

#include "nyquist_reconstruct.hpp"

static void expect_true(const char *name, bool condition)
{
    if (!condition) {
        std::cerr << name << " failed\n";
        std::exit(1);
    }
}

int main()
{
    const double duration = 0.1;
    const double reference_rate = 2000.0;
    const double good_mse = mean_squared_error(duration, reference_rate, 150.0, demo_signal);
    const double bad_mse = mean_squared_error(duration, reference_rate, 80.0, demo_signal);

    expect_true("good_mse_small", good_mse < 0.02);
    expect_true("bad_mse_large", bad_mse > good_mse * 5.0);

    std::cout << "All nyquist reconstruction tests passed.\n";
    return 0;
}
