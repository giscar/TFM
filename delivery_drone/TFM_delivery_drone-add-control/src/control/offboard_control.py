#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
from px4_msgs.msg import TrajectorySetpoint, VehicleStatus, OffboardControlMode

class OffboardControl(Node):
    def __init__(self):
        super().__init__('offboard_control')
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_ALL,
            depth=1000
        )
        self.mode_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos)
        self.setpoint_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v2', self.status_callback, qos)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.target_position = [0.0, 0.0, -2.5]
        self.target_yaw = 0.0
        self.counter = 0
        self.get_logger().info('Offboard control node started')

    def status_callback(self, msg):
        self.get_logger().info(f'Nav: {msg.nav_state}, Armed: {msg.arming_state}', throttle_duration_sec=1)

    def timer_callback(self):
        mode_msg = OffboardControlMode()
        mode_msg.timestamp = int(self.get_clock().now().nanoseconds // 1000)
        mode_msg.position = True
        self.mode_pub.publish(mode_msg)

        sp_msg = TrajectorySetpoint()
        sp_msg.timestamp = int(self.get_clock().now().nanoseconds // 1000)
        sp_msg.position = self.target_position
        sp_msg.yaw = self.target_yaw
        self.setpoint_pub.publish(sp_msg)

        self.counter += 1
        if self.counter % 20 == 0:
            self.get_logger().info(f'Setpoint: z={self.target_position[2]}')

def main(args=None):
    rclpy.init(args=args)
    node = OffboardControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
