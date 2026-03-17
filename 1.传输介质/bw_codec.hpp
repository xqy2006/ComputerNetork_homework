#pragma once

#include <opencv2/opencv.hpp>
#include "utils.hpp"

namespace bw {

// 0 -> white, 1 -> black
inline cv::Scalar encode(int msg) {
    return (msg == 0) ? cv::Scalar(255, 255, 255) : cv::Scalar(0, 0, 0);
}

inline int decode(cv::Scalar color) {
    double brightness = 0.114 * color[0] + 0.587 * color[1] + 0.299 * color[2];
    return (brightness > 127.0) ? 0 : 1;
}

inline void send(int msg) {
    utils::send(msg, "out/bw_msg.png", encode);
}

inline int receive() {
    return utils::receive("out/bw_msg.png", decode);
}

} // namespace bw
