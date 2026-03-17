#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>

int main() {
    const std::string win = "Optical Sender (BW)";
    cv::namedWindow(win, cv::WINDOW_NORMAL);
    cv::setWindowProperty(win, cv::WND_PROP_FULLSCREEN, cv::WINDOW_FULLSCREEN);

    int bit = 0;
    bool auto_mode = false;
    int symbol_ms = 200;
    std::vector<int> sequence;
    size_t seq_index = 0;
    int64 last_tick = cv::getTickCount();
    double tick_freq = cv::getTickFrequency();

    auto build_sequence = []() {
        std::vector<int> preamble = {1,0,1,0,1,0,1,0};
        std::vector<int> start = {1,1,1,0,0,0};
        std::vector<int> payload = {1,0,1,1,0,0,1,1};
        std::vector<int> seq;
        seq.insert(seq.end(), preamble.begin(), preamble.end());
        seq.insert(seq.end(), start.begin(), start.end());
        seq.insert(seq.end(), payload.begin(), payload.end());
        return seq;
    };

    std::cout << "Sender BW:\n";
    std::cout << "  0/1: set bit (manual)\n";
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
                bit = sequence[seq_index];
                seq_index = (seq_index + 1) % sequence.size();
            }
        }

        cv::Scalar color = (bit == 0) ? cv::Scalar(255, 255, 255)
                                      : cv::Scalar(0, 0, 0);
        cv::Mat frame(480, 640, CV_8UC3, color);

        cv::putText(frame, "BIT " + std::to_string(bit), {20, 50},
                    cv::FONT_HERSHEY_SIMPLEX, 1.2, cv::Scalar(0, 0, 255), 2);
        cv::putText(frame, auto_mode ? "AUTO" : "MANUAL", {20, 90},
                    cv::FONT_HERSHEY_SIMPLEX, 0.9, cv::Scalar(0, 0, 255), 2);
        cv::putText(frame, "T=" + std::to_string(symbol_ms) + "ms", {20, 130},
                    cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0, 0, 255), 2);

        cv::imshow(win, frame);
        int key = cv::waitKey(30);
        if (key == 'q' || key == 27) {
            break;
        } else if (key == '0') {
            auto_mode = false;
            bit = 0;
        } else if (key == '1') {
            auto_mode = false;
            bit = 1;
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
