#!/usr/bin/env python3
"""
Nodo de control OFFBOARD para PX4.
Publica setpoints de posición a 20Hz para mantener vuelo autónomo.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from px4_msgs.msg import TrajectorySetpoint, VehicleStatus, OffboardControlMode

class OffboardControl(Node):
    def __init__(self):
        super().__init__('offboard_control')
        
        # Configuración QoS para comunicación con PX4
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Publicadores
        self.mode_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos
        )
        self.setpoint_pub = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos
        )
        
        # Suscriptor para estado del vehículo
        self.status_sub = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status_v2', self.status_callback, qos
        )
        
        # Timer para publicar a 20Hz
        self.timer = self.create_timer(0.05, self.timer_callback)
        
        # Variables de estado
        self.target_position = [0.0, 0.0, -2.5]  # x, y, z (negativo = arriba)
        self.target_yaw = 0.0
        self.nav_state = None
        self.armed = None
        self.counter = 0
        
        self.get_logger().info('🚁 Nodo OFFBOARD iniciado')
        self.get_logger().info(f'  Objetivo: x={self.target_position[0]}, y={self.target_position[1]}, z={self.target_position[2]}')
    
    def status_callback(self, msg):
        """Actualiza estado del vehículo."""
        self.nav_state = msg.nav_state
        self.armed = msg.arming_state
        self.get_logger().info(
            f'📊 Nav: {msg.nav_state}, Armed: {msg.arming_state}', 
            throttle_duration_sec=1
        )
    
    def timer_callback(self):
        """Publica modo OFFBOARD y setpoint."""
        # Publicar modo OFFBOARD
        mode_msg = OffboardControlMode()
        mode_msg.timestamp = int(self.get_clock().now().nanoseconds // 1000)
        mode_msg.position = True
        self.mode_pub.publish(mode_msg)
        
        # Publicar setpoint de posición
        sp_msg = TrajectorySetpoint()
        sp_msg.timestamp = int(self.get_clock().now().nanoseconds // 1000)
        sp_msg.position = self.target_position
        sp_msg.yaw = self.target_yaw
        self.setpoint_pub.publish(sp_msg)
        
        self.counter += 1
        if self.counter % 20 == 0:  # Cada segundo
            self.get_logger().info(f'🎯 Setpoint: x={self.target_position[0]}, y={self.target_position[1]}, z={self.target_position[2]}')
    
    def set_target(self, x, y, z, yaw=0.0):
        """Cambia el objetivo de posición."""
        self.target_position = [x, y, z]
        self.target_yaw = yaw
        self.get_logger().info(f'🔄 Nuevo objetivo: ({x}, {y}, {z})')

def main(args=None):
    rclpy.init(args=args)
    node = OffboardControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('👋 Nodo detenido')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
