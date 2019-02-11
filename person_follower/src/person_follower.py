#!/usr/bin/env python
import rospy
from std_msgs.msg import Header
from darknet_ros_msgs.msg import BoundingBoxes
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive


class PersonFollower():
    def __init__(self):
        self.person_bounding_box = None
        rospy.init_node("person_follower", anonymous=True)
        sub = rospy.Subscriber('/darknet_ros/bounding_boxes', BoundingBoxes, lambda x: self.cb(x))
        pub = rospy.Publisher('/vesc/low_level/ackermann_cmd_mux/input/teleop', AckermannDriveStamped, queue_size=10)
        rate = rospy.Rate(10)
        seq = 0
        while not rospy.is_shutdown():
            seq += 1
            header = Header(seq=seq, stamp=rospy.Time.now())
            # TODO: fix this
            bb = self.person_bounding_box
            if bb is not None:
                angle =  -2 * ((bb.xmin + bb.xmax)/2.0 / 640.0 - 0.5)
                print("angle is", angle)
                #pub.publish()
                #print "self.person_bounding_box is ", self.person_bounding_box
                pub.publish(AckermannDriveStamped(header, AckermannDrive(steering_angle=angle)))
            rate.sleep()
        rospy.spin()

    def cb(self, data):
        for bounding_box in data.bounding_boxes:
            if bounding_box.Class == "person":
                #print("Person detected! Confidence", bounding_box.probability)
                bb = bounding_box
                size = abs(bb.xmax - bb.xmin) * abs(bb.ymax - bb.ymin)
                if bounding_box.probability > 0.8 and size > 0.05 * 640 * 480:
                    self.person_bounding_box = bounding_box 
                break
        else:
            pass
            # print("No person found :( lonely robot is sad") 


if __name__ == "__main__":
    pf = PersonFollower()