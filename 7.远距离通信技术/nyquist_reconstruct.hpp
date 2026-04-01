#ifndef NYQUIST_RECONSTRUCT_HPP
#define NYQUIST_RECONSTRUCT_HPP

#include <functional>
#include <string>
#include <vector>

struct Sample {
    double time;
    double value;
};

typedef std::function<double(double)> SignalFunction;

std::vector<Sample> sample_signal(double duration, double sample_rate, const SignalFunction &signal);
double reconstruct_value(const std::vector<Sample> &samples, double sample_rate, double t);
double mean_squared_error(
    double duration,
    double reference_rate,
    double sample_rate,
    const SignalFunction &signal
);
void write_csv(
    const std::string &path,
    double duration,
    double reference_rate,
    double sample_rate,
    const SignalFunction &signal
);
double demo_signal(double t);

#endif
