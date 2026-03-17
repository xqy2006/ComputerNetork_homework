#pragma once

#include <opencv2/opencv.hpp>
#include <vector>

#include "utils.hpp"

namespace octal {

inline cv::Scalar encode(int msg) {
    switch (msg & 7) {
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

inline int decode(cv::Scalar color) {
    cv::Mat bgr(1, 1, CV_8UC3);
    bgr.at<cv::Vec3b>(0, 0) = cv::Vec3b(
        static_cast<uchar>(color[0]),
        static_cast<uchar>(color[1]),
        static_cast<uchar>(color[2]));
    cv::Mat hsv;
    cv::cvtColor(bgr, hsv, cv::COLOR_BGR2HSV);
    cv::Vec3b v = hsv.at<cv::Vec3b>(0, 0);
    int h = v[0];
    int s = v[1];
    int val = v[2];

    if (val < 50) return 0;            // black
    if (s < 30 && val > 200) return 1; // white

    struct HueClass { int digit; int hue_center; };
    const std::vector<HueClass> classes = {
        {2, 0},    // red
        {6, 30},   // yellow
        {4, 60},   // green
        {7, 90},   // cyan
        {3, 120},  // blue
        {5, 150},  // purple
    };

    int best_digit = 2;
    int best_dist = 999;
    for (const auto& c : classes) {
        int d = std::abs(h - c.hue_center);
        d = std::min(d, 180 - d);
        if (d < best_dist) {
            best_dist = d;
            best_digit = c.digit;
        }
    }
    return best_digit;
}

inline void send(int msg) {
    utils::send(msg, "out/octal_msg.png", encode);
}

inline int receive() {
    return utils::receive("out/octal_msg.png", decode);
}

} // namespace octal
