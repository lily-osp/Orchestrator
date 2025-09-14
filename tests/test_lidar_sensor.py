"""
Unit tests for LidarSensor class.

Tests the LiDAR sensor implementation including initialization, scanning,
data parsing, obstacle detection, and MQTT communication.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Import the module under test
from hal_service.lidar_sensor import LidarSensor, LidarScan
from hal_service.config import SensorConfig, UARTConfig


class TestLidarScan:
    """Test the LidarScan data structure."""
    
    def test_lidar_scan_creation(self):
        """Test creating a LidarScan object."""
        scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[1.0, 2.0, 3.0, 0.5],
            angles=[0, 90, 180, 270],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[200, 180, 150, 220]
        )
        
        assert len(scan.ranges) == 4
        assert len(scan.angles) == 4
        assert len(scan.quality) == 4
        assert scan.min_range == 0.15
        assert scan.max_range == 12.0
    
    def test_get_closest_obstacle(self):
        """Test finding the closest obstacle."""
        scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[2.0, 0.8, 3.0, 1.5],
            angles=[0, 90, 180, 270],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[200, 180, 150, 220]
        )
        
        closest_distance, closest_angle = scan.get_closest_obstacle()
        assert closest_distance == 0.8
        assert closest_angle == 90
    
    def test_get_obstacles_in_zone(self):
        """Test finding obstacles in a specific zone."""
        scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[2.0, 0.8, 3.0, 1.5, 0.6],
            angles=[0, 90, 180, 270, 45],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[200, 180, 150, 220, 190]
        )
        
        # Look for obstacles in front zone (-45 to 45 degrees) within 1.0 meter
        front_obstacles = scan.get_obstacles_in_zone(-45, 45, 1.0)
        
        # Should find the obstacle at 45 degrees (0.6m)
        assert len(front_obstacles) == 1
        assert front_obstacles[0] == (0.6, 45)
    
    def test_empty_scan_closest_obstacle(self):
        """Test closest obstacle with no valid measurements."""
        scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[0.1, 15.0],  # Below min_range and above max_range
            angles=[0, 90],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[50, 50]
        )
        
        closest_distance, closest_angle = scan.get_closest_obstacle()
        assert closest_distance == float('inf')
        assert closest_angle == 0.0


class TestLidarSensor:
    """Test the LidarSensor class."""
    
    @pytest.fixture
    def mock_mqtt_client(self):
        """Create a mock MQTT client."""
        client = Mock()
        client.publish = Mock(return_value=True)
        client.subscribe = Mock(return_value=True)
        return client
    
    @pytest.fixture
    def sensor_config(self):
        """Create a test sensor configuration."""
        uart_config = UARTConfig(
            port="/dev/ttyUSB0",
            baudrate=115200,
            timeout=1.0
        )
        
        return SensorConfig(
            name="lidar_01",
            type="lidar",
            interface=uart_config,
            publish_rate=10.0,
            calibration={
                "min_range": 0.15,
                "max_range": 12.0,
                "angle_resolution": 1.0,
                "scan_frequency": 10.0,
                "quality_threshold": 10
            }
        )
    
    @pytest.fixture
    def lidar_sensor(self, mock_mqtt_client, sensor_config):
        """Create a LidarSensor instance for testing."""
        return LidarSensor("lidar_01", mock_mqtt_client, sensor_config)
    
    def test_lidar_sensor_creation(self, lidar_sensor):
        """Test creating a LidarSensor instance."""
        assert lidar_sensor.device_id == "lidar_01"
        assert lidar_sensor.port == "/dev/ttyUSB0"
        assert lidar_sensor.baudrate == 115200
        assert lidar_sensor.min_range == 0.15
        assert lidar_sensor.max_range == 12.0
        assert lidar_sensor.scan_frequency == 10.0
        assert not lidar_sensor.scanning
        assert lidar_sensor.serial_connection is None
    
    def test_invalid_config_raises_error(self, mock_mqtt_client):
        """Test that invalid configuration raises an error."""
        # Create config without UART interface
        invalid_config = SensorConfig(
            name="lidar_01",
            type="lidar",
            interface=Mock(),  # Not a UART config
            publish_rate=10.0
        )
        
        with pytest.raises(ValueError, match="LiDAR sensor requires UART interface"):
            LidarSensor("lidar_01", mock_mqtt_client, invalid_config)
    
    @patch('hal_service.lidar_sensor.serial')
    def test_initialization_success(self, mock_serial, lidar_sensor):
        """Test successful LiDAR initialization."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_connection.in_waiting = 10
        mock_connection.read.return_value = b'\x01\x02\x03\x04'
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        result = lidar_sensor.initialize()
        
        assert result is True
        assert lidar_sensor._initialized is True
        assert lidar_sensor.status == "ready"
        assert lidar_sensor.scanning is True
        
        # Verify serial connection was configured correctly
        mock_serial.Serial.assert_called_once_with(
            port="/dev/ttyUSB0",
            baudrate=115200,
            timeout=1.0,
            bytesize=8,
            parity='N',
            stopbits=1
        )
    
    @patch('hal_service.lidar_sensor.serial')
    def test_initialization_failure(self, mock_serial, lidar_sensor):
        """Test LiDAR initialization failure."""
        # Mock serial connection failure
        mock_serial.Serial.side_effect = Exception("Serial connection failed")
        
        # Initialize sensor
        result = lidar_sensor.initialize()
        
        assert result is False
        assert lidar_sensor._initialized is False
        assert lidar_sensor.status != "ready"
    
    @patch('hal_service.lidar_sensor.serial')
    def test_send_command(self, mock_serial, lidar_sensor):
        """Test sending commands to LiDAR."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Test sending command
        result = lidar_sensor._send_command(0x20, b'\x01\x02')
        
        assert result is True
        mock_connection.write.assert_called_with(b'\xa5\x20\x01\x02')
        mock_connection.flush.assert_called_once()
    
    @patch('hal_service.lidar_sensor.serial')
    def test_start_stop_scanning(self, mock_serial, lidar_sensor):
        """Test starting and stopping LiDAR scanning."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Scanning should start automatically during initialization
        assert lidar_sensor.scanning is True
        assert lidar_sensor.scan_thread is not None
        
        # Stop scanning
        lidar_sensor.stop_scanning()
        assert lidar_sensor.scanning is False
    
    @patch('hal_service.lidar_sensor.serial')
    def test_read_data_no_scan(self, mock_serial, lidar_sensor):
        """Test reading data when no scan is available."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor but don't start scanning
        lidar_sensor.serial_connection = mock_connection
        lidar_sensor._initialized = True
        
        # Read data
        data = lidar_sensor.read_data()
        
        assert data["scan_available"] is False
        assert "error" in data
    
    @patch('hal_service.lidar_sensor.serial')
    def test_read_data_with_scan(self, mock_serial, lidar_sensor):
        """Test reading data with available scan."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Create mock scan data
        mock_scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[1.0, 2.0, 3.0, 0.8],
            angles=[0, 90, 180, 270],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[200, 180, 150, 220]
        )
        
        # Set current scan
        with lidar_sensor._scan_lock:
            lidar_sensor.current_scan = mock_scan
        
        # Read data
        data = lidar_sensor.read_data()
        
        assert data["scan_available"] is True
        assert len(data["ranges"]) == 4
        assert len(data["angles"]) == 4
        assert data["num_points"] == 4
        assert data["closest_obstacle"]["distance"] == 0.8
        assert data["closest_obstacle"]["angle"] == 270
        assert "obstacle_zones" in data
        assert "scan_statistics" in data
    
    @patch('hal_service.lidar_sensor.serial')
    def test_obstacle_detection(self, mock_serial, lidar_sensor):
        """Test obstacle detection functionality."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Create scan with obstacle in front
        mock_scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[0.3, 2.0, 3.0, 4.0],  # Obstacle at 0 degrees (0.3m)
            angles=[0, 90, 180, 270],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[200, 180, 150, 220]
        )
        
        # Set current scan
        with lidar_sensor._scan_lock:
            lidar_sensor.current_scan = mock_scan
        
        # Test obstacle detection in front zone
        obstacle_detected = lidar_sensor.is_obstacle_detected(
            min_distance=0.5,
            angle_range=(-45, 45)
        )
        
        assert obstacle_detected is True
        
        # Test no obstacle detection in rear zone
        no_obstacle = lidar_sensor.is_obstacle_detected(
            min_distance=0.5,
            angle_range=(135, 225)
        )
        
        assert no_obstacle is False
    
    @patch('hal_service.lidar_sensor.serial')
    def test_parse_scan_data(self, mock_serial, lidar_sensor):
        """Test parsing scan data."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Test parsing with mock data
        raw_data = b'\x01\x02\x03\x04' * 100  # Mock raw data
        
        scan = lidar_sensor._parse_scan_data(raw_data)
        
        assert scan is not None
        assert isinstance(scan, LidarScan)
        assert len(scan.ranges) == 360  # 360-degree scan
        assert len(scan.angles) == 360
        assert len(scan.quality) == 360
        assert scan.min_range == lidar_sensor.min_range
        assert scan.max_range == lidar_sensor.max_range
    
    @patch('hal_service.lidar_sensor.serial')
    def test_get_status(self, mock_serial, lidar_sensor):
        """Test getting sensor status."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Get status
        status = lidar_sensor.get_status()
        
        assert status["device_id"] == "lidar_01"
        assert status["initialized"] is True
        assert status["scanning"] is True
        assert "connection" in status
        assert "config" in status
        assert status["connection"]["port"] == "/dev/ttyUSB0"
        assert status["connection"]["baudrate"] == 115200
        assert status["config"]["min_range"] == 0.15
        assert status["config"]["max_range"] == 12.0
    
    @patch('hal_service.lidar_sensor.serial')
    def test_stop_sensor(self, mock_serial, lidar_sensor):
        """Test stopping the sensor."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Stop sensor
        lidar_sensor.stop()
        
        assert lidar_sensor.scanning is False
        assert lidar_sensor.status == "stopped"
        mock_connection.close.assert_called_once()
    
    @patch('hal_service.lidar_sensor.serial')
    def test_mqtt_publishing(self, mock_serial, lidar_sensor):
        """Test MQTT data publishing."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.is_open = True
        mock_serial.Serial.return_value = mock_connection
        
        # Initialize sensor
        lidar_sensor.initialize()
        
        # Create mock scan data
        mock_scan = LidarScan(
            timestamp=datetime.now(),
            ranges=[1.0, 2.0],
            angles=[0, 90],
            min_range=0.15,
            max_range=12.0,
            scan_time=0.1,
            quality=[200, 180]
        )
        
        # Set current scan
        with lidar_sensor._scan_lock:
            lidar_sensor.current_scan = mock_scan
        
        # Publish data
        data = lidar_sensor.read_data()
        lidar_sensor.publish_data(data)
        
        # Verify MQTT publish was called
        lidar_sensor.mqtt_client.publish.assert_called()
        
        # Get the published data
        call_args = lidar_sensor.mqtt_client.publish.call_args
        topic = call_args[0][0]
        
        assert topic == "orchestrator/data/lidar_01"
    
    def test_scan_loop_error_handling(self, lidar_sensor):
        """Test error handling in scan loop."""
        # Mock a scan method that raises an exception
        lidar_sensor._read_scan_data = Mock(side_effect=Exception("Scan error"))
        lidar_sensor._initialized = True
        lidar_sensor.scanning = True
        
        # Run scan loop briefly
        thread = threading.Thread(target=lidar_sensor._scan_loop, daemon=True)
        thread.start()
        
        # Let it run briefly then stop
        time.sleep(0.1)
        lidar_sensor.scanning = False
        thread.join(timeout=1.0)
        
        # Should have incremented error count
        assert lidar_sensor.scan_errors > 0


if __name__ == "__main__":
    pytest.main([__file__])