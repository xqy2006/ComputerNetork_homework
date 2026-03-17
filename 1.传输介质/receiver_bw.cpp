#include <opencv2/opencv.hpp>
#include <iostream>
#include <deque>
#include <vector>

static double luma(const cv::Scalar& bgr) {
    return 0.114 * bgr[0] + 0.587 * bgr[1] + 0.299 * bgr[2];
}

static cv::Scalar mean_rect(const cv::Mat& frame, const cv::Rect& r) {
    cv::Rect rr = r & cv::Rect(0, 0, frame.cols, frame.rows);
    return cv::mean(frame(rr));
}

static cv::Scalar ambient_mean(const cv::Mat& frame) {
    int w = frame.cols;
    int h = frame.rows;
    int size = std::min(w, h) / 8;
    cv::Rect tl(0, 0, size, size);
    cv::Rect tr(w - size, 0, size, size);
    cv::Rect bl(0, h - size, size, size);
    cv::Rect br(w - size, h - size, size, size);
    cv::Scalar a = mean_rect(frame, tl);
    cv::Scalar b = mean_rect(frame, tr);
    cv::Scalar c = mean_rect(frame, bl);
    cv::Scalar d = mean_rect(frame, br);
    return (a + b + c + d) * 0.25;
}

int main() {
    cv::VideoCapture cap(0);
    if (!cap.isOpened()) {
        std::cerr << "Failed to open camera.\n";
        return 1;
    }

    const std::string win = "Optical Receiver (BW)";
    cv::namedWindow(win, cv::WINDOW_NORMAL);

    int last_bit = -1;
    int symbol_frames = 6;
    int frame_count = 0;
    double accum_signal = 0.0;
    bool synced = false;

    bool have_black = false;
    bool have_white = false;
    double black_sig = 0.0;
    double white_sig = 255.0;

    bool auto_cal = false;
    int auto_cal_frames = 0;
    int auto_cal_total = 60;
    double auto_min = 1e9;
    double auto_max = -1e9;

    std::deque<int> history;
    std::vector<int> preamble = {1,0,1,0,1,0,1,0};
    std::vector<int> start = {1,1,1,0,0,0};
    std::vector<int> sync_seq;
    sync_seq.insert(sync_seq.end(), preamble.begin(), preamble.end());
    sync_seq.insert(sync_seq.end(), start.begin(), start.end());

    std::cout << "Receiver BW:\n";
    std::cout << "  b: capture BLACK, w: capture WHITE\n";
    std::cout << "  c: auto-calibrate (2s, show black then white)\n";
    std::cout << "  +/-: change symbol frames\n";
    std::cout << "  q/ESC: quit\n";

    while (true) {
        cv::Mat frame;
        if (!cap.read(frame) || frame.empty()) {
            std::cerr << "Failed to read frame.\n";
            break;
        }

        int w = frame.cols;
        int h = frame.rows;
        int size = std::min(w, h) / 4;
        cv::Rect roi((w - size) / 2, (h - size) / 2, size, size);
        cv::Mat center = frame(roi);

        cv::Scalar mean_bgr = cv::mean(center);
        cv::Scalar amb_bgr = ambient_mean(frame);
        double signal = luma(mean_bgr) - luma(amb_bgr);

        if (auto_cal) {
            auto_min = std::min(auto_min, signal);
            auto_max = std::max(auto_max, signal);
            auto_cal_frames++;
            if (auto_cal_frames >= auto_cal_total) {
                auto_cal = false;
                black_sig = auto_min;
                white_sig = auto_max;
                if (white_sig < black_sig) std::swap(white_sig, black_sig);
                have_black = true;
                have_white = true;
                std::cout << "Auto-cal done. black=" << black_sig
                          << " white=" << white_sig << "\n";
            }
        }

        accum_signal += signal;
        frame_count++;
        int bit = last_bit;
        if (frame_count >= symbol_frames) {
            double avg_signal = accum_signal / frame_count;
            frame_count = 0;
            accum_signal = 0.0;

            double threshold = 20.0;
            if (have_black && have_white) {
                threshold = 0.5 * (black_sig + white_sig);
            }
            bit = (avg_signal > threshold) ? 0 : 1;  // white -> 0, black -> 1

            history.push_back(bit);
            while (history.size() > sync_seq.size()) history.pop_front();

            if (!synced && history.size() == sync_seq.size()) {
                bool match = true;
                for (size_t i = 0; i < sync_seq.size(); ++i) {
                    if (history[i] != sync_seq[i]) {
                        match = false;
                        break;
                    }
                }
                if (match) {
                    synced = true;
                    std::cout << "Synced.\n";
                }
            }

            if (synced) {
                std::cout << "Detected bit: " << bit << "\n";
                last_bit = bit;
            }
        }

        cv::rectangle(frame, roi, cv::Scalar(0, 255, 0), 2);
        cv::putText(frame, "BIT " + std::to_string(bit), {20, 50},
                    cv::FONT_HERSHEY_SIMPLEX, 1.2, cv::Scalar(0, 0, 255), 2);
        cv::putText(frame, synced ? "SYNC" : "UNSYNC", {20, 90},
                    cv::FONT_HERSHEY_SIMPLEX, 0.9, cv::Scalar(0, 0, 255), 2);
        cv::putText(frame, "F=" + std::to_string(symbol_frames), {20, 130},
                    cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0, 0, 255), 2);

        cv::imshow(win, frame);
        int key = cv::waitKey(1);
        if (key == 'q' || key == 27) {
            break;
        } else if (key == 'b' || key == 'B') {
            black_sig = signal;
            have_black = true;
            std::cout << "Captured BLACK signal: " << black_sig << "\n";
        } else if (key == 'w' || key == 'W') {
            white_sig = signal;
            have_white = true;
            std::cout << "Captured WHITE signal: " << white_sig << "\n";
        } else if (key == 'c' || key == 'C') {
            auto_cal = true;
            auto_cal_frames = 0;
            auto_min = 1e9;
            auto_max = -1e9;
            std::cout << "Auto-cal start: show BLACK then WHITE within ~2s.\n";
        } else if (key == '+' || key == '=') {
            symbol_frames = std::min(30, symbol_frames + 1);
        } else if (key == '-' || key == '_') {
            symbol_frames = std::max(2, symbol_frames - 1);
        }
    }

    return 0;
}
