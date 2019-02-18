#!/usr/bin/env python
import rospy
from cv_bridge import CvBridge
from std_msgs.msg import Header
from darknet_ros_msgs.msg import BoundingBoxes
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive
from sensor_msgs.msg import Joy, Image
import numpy as np

br = CvBridge()

class PersonFollower():
    def __init__(self):
        IMAGE_WIDTH = 640
        IMAGE_HEIGHT = 480
        SERVO_RANGE = 0.34
        # MAX_PERCENT_OF_FRAME = 0.27
        # MIN_PERCENT_OF_FRAME = 0.18
        MAX_DEPTH = 1500
        MIN_DEPTH = 1000
        # state from subscribers
        self.person_bounding_box = None
        self.person_depth = 0.0
	self.right_bumper = False
        # node setup
        rospy.init_node("person_follower", anonymous=True)
        sub = rospy.Subscriber('/darknet_ros/bounding_boxes', BoundingBoxes, self.bounding_box_cb)
        depth_sub = rospy.Subscriber('/camera/depth/image_rect_raw', Image, self.depth_cb)
	joy_sub = rospy.Subscriber('/vesc/joy', Joy, self.right_bump)
	pub = rospy.Publisher('/vesc/low_level/ackermann_cmd_mux/input/teleop', AckermannDriveStamped, queue_size=10)
        rate = rospy.Rate(30)
        seq = 0
        while not rospy.is_shutdown():
            seq += 1
            header = Header(seq=seq, stamp=rospy.Time.now())
            bb = self.person_bounding_box
            if bb is not None:
                boxCenter = (bb.xmin + bb.xmax) / 2.0
		ratio = boxCenter / 640.0
		angle = -1 * (-SERVO_RANGE + ratio * 2 * SERVO_RANGE)
                speed = 0
                if 0 < self.person_depth < MIN_DEPTH:
                    speed = -0.5
                    angle = -angle
                elif self.person_depth > MAX_DEPTH:
                    speed = 0.5
		# print("angle is", angle, "speed is", speed, "percent of frame is", percent_of_frame)
                if self.right_bumper:
                    pub.publish(AckermannDriveStamped(header, AckermannDrive(steering_angle=angle, speed=speed)))
            rate.sleep()
        rospy.spin()

    def right_bump(self, data):
	self.right_bumper = bool(data.buttons[5])
        
    def depth_cb(self, data):
        averaged_depth = 0.0
        image = br.imgmsg_to_cv2(data)
        bb = self.person_bounding_box
        if bb is not None:
            person_region = image[bb.xmin:bb.xmax, bb.ymin:bb.ymax]
            # averaged_depth = np.mean(person_region)
            x_avg = (bb.xmin + bb.xmax) / 2
            y_avg = (bb.ymin + bb.ymax) / 2
            # NOTE: this could be replaced with a smarter weighted average
            # (with depths in the center of the bounding box higher-weighted)
            # to smooth noise
            averaged_depth = image[y_avg, x_avg]
            print("person at", x_avg, y_avg, "has depth", averaged_depth)
            self.person_depth = averaged_depth

    def bounding_box_cb(self, data):
        for bounding_box in data.bounding_boxes:
            if bounding_box.Class == "person":
                #print("Person detected! Confidence", bounding_box.probability)
                bb = bounding_box
                size = abs(bb.xmax - bb.xmin) * abs(bb.ymax - bb.ymin)
                if bounding_box.probability > 0.8 and size > 0.03 * 640 * 480:
                    self.person_bounding_box = bounding_box 
                break
        else:
            self.person_bounding_box = None
            # print("No person found :( lonely robot is sad") 


if __name__ == "__main__":
    pf = PersonFollower()