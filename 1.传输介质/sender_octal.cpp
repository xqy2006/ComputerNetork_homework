#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>

static cv::Scalar color_for_digit(int d) {
    switch (d) {
        case 0: return cv::Scalar(0, 0, 0);       // black
        case 1: return cv::Scalar(255, 255, 255); // white
        case 2: return cv::Scalar(0, 0, 255);     // red
        case 3: return cv::Scalar(255, 0, 0);     // blue
        case 4: return cv::Scalar(0, 255, 0);     // green
        case 5: return cv::Scalar(255, 0, 255);   // purple (magenta)
        case 6: return cv::Scalar(0, 255, 255);   // yellow
        case 7: return cv::Scalar(255, 255, 0);   // cyan
        default: return cv::Scalar(0, 0, 0);
    }
}

int main() {
    const std::string win = "Optical Sender (Octal)";
    cv::namedWindow(win, cv::WINDOW_NORMAL);
    cv::setWindowProperty(win, cv::WND_PROP_FULLSCREEN, cv::WINDOW_FULLSCREEN);

    int digit = 0;
    bool auto_mode = false;
    int symbol_ms = 200;
    std::vector<int> sequence;
    size_t seq_index = 0;
    int64 last_tick = cv::getTickCount();
    double tick_freq = cv::getTickFrequency();

    auto build_sequence = []() {
        std::vector<int> preamble = {0,7,0,7,0,7,0,7};
        std::vector<int> start = {3,3,3};
        std::vector<int> payload = {0,1,2,3,4,5,6,7};
        std::vector<int> seq;
        seq.insert(seq.end(), preamble.begin(), preamble.end());
        seq.insert(seq.end(), start.begin(), start.end());
        seq.insert(seq.end(), payload.begin(), payload.end());
        return seq;
    };

    std::cout << "Sender Octal:\n";
    std::cout << "  0..7: set digit (manual)\n";
    std::cout << "  t: toggle auto sequence (preamble+start+payload)\n";
    std::cout << "  +/-: change symbol duration (ms)\n";
    std::cout << "  q/ESC: quit\n";

    while (true) {
        if (auto_mode) {
            int64 now = cv::getTickCount();
            double elapsed_ms = (now - last_tick) * 1000.0 / tick_freq;
            if (elapsed_ms >= symbol_ms) {
                last_tick = now;
                if (sequence.empty()) sequence = build_sequence();
                digit = sequence[seq_index];
                seq_index = (seq_index + 1) % sequence.size();
            }
        }

        cv::Scalar color = color_for_digit(digit);
        cv::Mat frame(480, 640, CV_8UC3, color);

        cv::putText(frame, "DIGIT " + std::to_string(digit), {20, 50},
                    cv::FONT_HERSHEY_SIMPLEX, 1.2, cv::Scalar(0, 0, 0), 2);
        cv::putText(frame, "DIGIT " + std::to_string(digit), {20, 50},
                    cv::FONT_HERSHEY_SIMPLEX, 1.2, cv::Scalar(255, 255, 255), 1);
        cv::putText(frame, auto_mode ? "AUTO" : "MANUAL", {20, 90},
                    cv::FONT_HERSHEY_SIMPLEX, 0.9, cv::Scalar(0, 0, 0), 2);
        cv::putText(frame, auto_mode ? "AUTO" : "MANUAL", {20, 90},
                    cv::FONT_HERSHEY_SIMPLEX, 0.9, cv::Scalar(255, 255, 255), 1);
        cv::putText(frame, "T=" + std::to_string(symbol_ms) + "ms", {20, 130},
                    cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0, 0, 0), 2);
        cv::putText(frame, "T=" + std::to_string(symbol_ms) + "ms", {20, 130},
                    cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 255, 255), 1);

        cv::imshow(win, frame);
        int key = cv::waitKey(30);
        if (key == 'q' || key == 27) {
            break;
        } else if (key >= '0' && key <= '7') {
            auto_mode = false;
            digit = key - '0';
        } else if (key == 't' || key == 'T') {
            auto_mode = !auto_mode;
            sequence = build_sequence();
            seq_index = 0;
            last_tick = cv::getTickCount();
        } else if (key == '+' || key == '=') {
            symbol_ms = std::min(1000, symbol_ms + 50);
        } else if (key == '-' || key == '_') {
            symbol_ms = std::max(50, symbol_ms - 50);
        }
    }
    return 0;
}
