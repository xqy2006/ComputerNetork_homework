#pragma once

#include <opencv2/opencv.hpp>
#include <filesystem>
#include <iostream>
#include <string>

namespace utils {

template <typename Encoder>
inline void send(int msg, const std::string& path, Encoder encode) {
    std::filesystem::path p(path);
    if (p.has_parent_path()) {
        std::filesystem::create_directories(p.parent_path());
    }
    cv::Mat img(200, 200, CV_8UC3, encode(msg));
    cv::imwrite(path, img);
}

template <typename Decoder>
inline int receive(const std::string& path, Decoder decode) {
    cv::Mat img = cv::imread(path);
    if (img.empty()) {
        std::cerr << "utils::receive: failed to read " << path << "\n";
        return -1;
    }
    cv::Scalar mean_bgr = cv::mean(img);
    return decode(mean_bgr);
}

} // namespace utils
