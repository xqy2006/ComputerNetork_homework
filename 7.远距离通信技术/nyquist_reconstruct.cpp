#include "nyquist_reconstruct.hpp"

#include <cmath>
#include <fstream>
#include <iomanip>

namespace {

const double PI = 3.14159265358979323846;

double sinc(double x)
{
    if (std::abs(x) < 1e-12) {
        return 1.0;
    }
    return std::sin(PI * x) / (PI * x);
}

}  // namespace

double demo_signal(double t)
{
    return std::sin(2.0 * PI * 20.0 * t) + 0.6 * std::sin(2.0 * PI * 60.0 * t);
}

std::vector<Sample> sample_signal(double duration, double sample_rate, const SignalFunction &signal)
{
    const int count = static_cast<int>(duration * sample_rate) + 1;
    std::vector<Sample> samples;
    samples.reserve(static_cast<std::size_t>(count));

    for (int i = 0; i < count; ++i) {
        const double t = static_cast<double>(i) / sample_rate;
        samples.push_back({t, signal(t)});
    }

    return samples;
}

double reconstruct_value(const std::vector<Sample> &samples, double sample_rate, double t)
{
    double value = 0.0;
    for (std::size_t i = 0; i < samples.size(); ++i) {
        value += samples[i].value * sinc(sample_rate * (t - samples[i].time));
    }
    return value;
}

double mean_squared_error(
    double duration,
    double reference_rate,
    double sample_rate,
    const SignalFunction &signal
)
{
    const std::vector<Sample> samples = sample_signal(duration, sample_rate, signal);
    const int points = static_cast<int>(duration * reference_rate);
    double error = 0.0;

    for (int i = 0; i < points; ++i) {
        const double t = static_cast<double>(i) / reference_rate;
        const double expected = signal(t);
        const double reconstructed = reconstruct_value(samples, sample_rate, t);
        const double diff = expected - reconstructed;
        error += diff * diff;
    }

    return error / static_cast<double>(points);
}

void write_csv(
    const std::string &path,
    double duration,
    double reference_rate,
    double sample_rate,
    const SignalFunction &signal
)
{
    const std::vector<Sample> samples = sample_signal(duration, sample_rate, signal);
    const int points = static_cast<int>(duration * reference_rate);
    std::ofstream out(path.c_str());
    out << "time,original,reconstructed\n";
    out << std::fixed << std::setprecision(6);
    for (int i = 0; i < points; ++i) {
        const double t = static_cast<double>(i) / reference_rate;
        out << t << "," << signal(t) << "," << reconstruct_value(samples, sample_rate, t) << "\n";
    }
}
