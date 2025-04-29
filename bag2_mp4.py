import rclpy
from rclpy.serialization import deserialize_message
from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import argparse

def create_video_from_ros2_bag(bag_path, image_topic, output_path):

    reader = SequentialReader()
    storage_options = StorageOptions(uri=bag_path, storage_id='sqlite3')
    converter_options = ConverterOptions(input_serialization_format='cdr', output_serialization_format='cdr')
    reader.open(storage_options, converter_options)

    bridge = CvBridge()
    video_writer = None
    frame_size = None
    frame_rate = 10  

    topic_types = reader.get_all_topics_and_types()
    type_dict = {topic.name: topic.type for topic in topic_types}

    if image_topic not in type_dict:
        print(f"Topic '{image_topic}' not found in the bag file.")
        return

    while reader.has_next():
        topic, data, t = reader.read_next()
        if topic == image_topic:
            try:
                msg = deserialize_message(data, Image)
                frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            except Exception as e:
                print(f"Error converting message: {e}")
                continue

            if frame_size is None:
                frame_size = (frame.shape[1], frame.shape[0])
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(output_path, fourcc, frame_rate, frame_size)

            video_writer.write(frame)

    if video_writer:
        video_writer.release()
        print(f"Video saved to {output_path}")
    else:
        print("No frames written; video was not created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert ROS 2 bag image topic to MP4 video")
    parser.add_argument("bag_path", help="Path to the ROS 2 bag folder (with metadata.yaml)")
    parser.add_argument("image_topic", help="Image topic to extract from the bag file")
    parser.add_argument("output_video", help="Output MP4 video file path")
    args = parser.parse_args()

    rclpy.init()
    create_video_from_ros2_bag(args.bag_path, args.image_topic, args.output_video)
    rclpy.shutdown()

