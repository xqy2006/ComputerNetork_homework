#include <iostream>

#include "nyquist_reconstruct.hpp"

int main()
{
    const double duration = 0.1;
    const double reference_rate = 2000.0;
    const double good_rate = 150.0;
    const double bad_rate = 80.0;

    const double good_mse = mean_squared_error(duration, reference_rate, good_rate, demo_signal);
    const double bad_mse = mean_squared_error(duration, reference_rate, bad_rate, demo_signal);

    write_csv("nyquist_good.csv", duration, reference_rate, good_rate, demo_signal);
    write_csv("nyquist_bad.csv", duration, reference_rate, bad_rate, demo_signal);

    std::cout << "highest useful frequency: 60 Hz\n";
    std::cout << "good sample rate: " << good_rate << " Hz, mse=" << good_mse << "\n";
    std::cout << "bad sample rate: " << bad_rate << " Hz, mse=" << bad_mse << "\n";
    std::cout << "csv: nyquist_good.csv, nyquist_bad.csv\n";
    return 0;
}
