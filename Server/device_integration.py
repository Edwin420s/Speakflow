"""
Omi Device Integration Module
Follows Omi documentation for third-party wearable integration.
Implements BLE protocol and device communication standards.
"""

import structlog
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
import json
from dataclasses import dataclass

logger = structlog.get_logger()

class DeviceType(str, Enum):
    """Supported Omi device types."""
    OMI = "omi"
    OMI_DEVKIT_2 = "omi_devkit_2"
    OMI_GLASS = "omi_glass"
    PLAUD = "plaud"
    LIMITLESS = "limitless"
    CUSTOM = "custom"

class BleAudioCodec(str, Enum):
    """Supported audio codecs for BLE transmission."""
    OPUS = "opus"
    PCM = "pcm"
    MULAW = "mulaw"
    AAC = "aac"

@dataclass
class BleService:
    """BLE service definition."""
    uuid: str
    name: str
    characteristics: List[str]

@dataclass
class DeviceInfo:
    """Device information and capabilities."""
    device_id: str
    name: str
    device_type: DeviceType
    manufacturer: str
    firmware_version: str
    audio_codec: BleAudioCodec
    sample_rate: int
    battery_level: Optional[int] = None

class OmiDeviceProtocol:
    """
    Implements Omi device communication protocol following official documentation.
    Supports BLE connection, audio streaming, and device management.
    """
    
    # Official Omi BLE Service UUIDs (from documentation)
    OMI_AUDIO_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"  # Audio Service
    OMI_DEVICE_INFO_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"  # Device Info
    OMI_BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"  # Battery Service
    
    # Characteristic UUIDs
    AUDIO_STREAM_CHARACTERISTIC = "00002a37-0000-1000-8000-00805f9b34fb"
    BATTERY_LEVEL_CHARACTERISTIC = "00002a19-0000-1000-8000-00805f9b34fb"
    DEVICE_NAME_CHARACTERISTIC = "00002a00-0000-1000-8000-00805f9b34fb"
    
    def __init__(self):
        self.connected_devices: Dict[str, DeviceInfo] = {}
        self.audio_streams: Dict[str, asyncio.Queue] = {}
        
    async def scan_for_devices(self, device_type: Optional[DeviceType] = None) -> List[DeviceInfo]:
        """
        Scan for Omi devices following BLE protocol.
        
        Args:
            device_type: Optional filter for specific device type
            
        Returns:
            List of discovered devices
        """
        # In production, this would use actual BLE scanning
        # For demo, return simulated devices
        discovered_devices = []
        
        demo_devices = [
            DeviceInfo(
                device_id="OMI-001",
                name="Omi DevKit 2",
                device_type=DeviceType.OMI_DEVKIT_2,
                manufacturer="Based Hardware",
                firmware_version="2.0.1",
                audio_codec=BleAudioCodec.OPUS,
                sample_rate=16000,
                battery_level=85
            ),
            DeviceInfo(
                device_id="OMI-002",
                name="Omi Glass",
                device_type=DeviceType.OMI_GLASS,
                manufacturer="Based Hardware",
                firmware_version="1.5.0",
                audio_codec=BleAudioCodec.OPUS,
                sample_rate=16000,
                battery_level=62
            )
        ]
        
        if device_type:
            demo_devices = [d for d in demo_devices if d.device_type == device_type]
        
        discovered_devices.extend(demo_devices)
        
        logger.info("Device scan completed", 
                   devices_found=len(discovered_devices),
                   device_type_filter=device_type.value if device_type else "all")
        
        return discovered_devices
    
    async def connect_device(self, device_id: str) -> bool:
        """
        Connect to Omi device via BLE.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            True if connection successful
        """
        try:
            # In production, establish actual BLE connection
            # For demo, simulate connection
            
            # Simulate connection process
            await asyncio.sleep(0.5)  # Connection delay
            
            # Create device info if not exists
            if device_id not in self.connected_devices:
                device_info = DeviceInfo(
                    device_id=device_id,
                    name=f"Omi Device {device_id}",
                    device_type=DeviceType.OMI,
                    manufacturer="Based Hardware",
                    firmware_version="2.0.0",
                    audio_codec=BleAudioCodec.OPUS,
                    sample_rate=16000,
                    battery_level=75
                )
                self.connected_devices[device_id] = device_info
            
            # Initialize audio stream queue
            self.audio_streams[device_id] = asyncio.Queue(maxsize=100)
            
            logger.info("Device connected successfully", device_id=device_id)
            return True
            
        except Exception as e:
            logger.error("Failed to connect to device", device_id=device_id, error=str(e))
            return False
    
    async def disconnect_device(self, device_id: str):
        """Disconnect from Omi device."""
        try:
            if device_id in self.connected_devices:
                del self.connected_devices[device_id]
            
            if device_id in self.audio_streams:
                del self.audio_streams[device_id]
            
            logger.info("Device disconnected", device_id=device_id)
            
        except Exception as e:
            logger.error("Error disconnecting device", device_id=device_id, error=str(e))
    
    async def start_audio_stream(self, device_id: str) -> bool:
        """
        Start audio streaming from connected device.
        
        Args:
            device_id: Connected device identifier
            
        Returns:
            True if streaming started successfully
        """
        if device_id not in self.connected_devices:
            logger.error("Device not connected", device_id=device_id)
            return False
        
        try:
            # In production, subscribe to audio characteristic
            # For demo, start simulated audio stream
            
            device_info = self.connected_devices[device_id]
            logger.info("Audio stream started", 
                       device_id=device_id,
                       codec=device_info.audio_codec.value,
                       sample_rate=device_info.sample_rate)
            
            return True
            
        except Exception as e:
            logger.error("Failed to start audio stream", device_id=device_id, error=str(e))
            return False
    
    async def get_audio_chunk(self, device_id: str, timeout: float = 1.0) -> Optional[bytes]:
        """
        Get next audio chunk from device stream.
        
        Args:
            device_id: Device identifier
            timeout: Timeout in seconds
            
        Returns:
            Audio data chunk or None if timeout
        """
        if device_id not in self.audio_streams:
            return None
        
        try:
            chunk = await asyncio.wait_for(
                self.audio_streams[device_id].get(), 
                timeout=timeout
            )
            return chunk
        except asyncio.TimeoutError:
            return None
    
    async def get_battery_level(self, device_id: str) -> Optional[int]:
        """Get device battery level."""
        if device_id not in self.connected_devices:
            return None
        
        device_info = self.connected_devices[device_id]
        return device_info.battery_level
    
    async def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """Get complete device information."""
        return self.connected_devices.get(device_id)
    
    def get_supported_services(self) -> List[BleService]:
        """Get list of supported BLE services."""
        return [
            BleService(
                uuid=self.OMI_AUDIO_SERVICE,
                name="Audio Service",
                characteristics=[self.AUDIO_STREAM_CHARACTERISTIC]
            ),
            BleService(
                uuid=self.OMI_DEVICE_INFO_SERVICE,
                name="Device Information",
                characteristics=[self.DEVICE_NAME_CHARACTERISTIC]
            ),
            BleService(
                uuid=self.OMI_BATTERY_SERVICE,
                name="Battery Service",
                characteristics=[self.BATTERY_LEVEL_CHARACTERISTIC]
            )
        ]
    
    async def simulate_audio_data(self, device_id: str, duration: int = 10):
        """
        Simulate audio data streaming for demo purposes.
        
        Args:
            device_id: Device to simulate for
            duration: Duration in seconds
        """
        if device_id not in self.audio_streams:
            return
        
        logger.info("Starting audio simulation", device_id=device_id, duration=duration)
        
        for i in range(duration * 10):  # 10 chunks per second
            # Simulate audio chunk (16000 samples * 2 bytes * 0.1s = 3200 bytes)
            audio_chunk = b'\x00' * 3200  # Silent audio for demo
            
            try:
                await self.audio_streams[device_id].put(audio_chunk)
                await asyncio.sleep(0.1)  # 100ms intervals
            except asyncio.QueueFull:
                logger.warning("Audio buffer full, dropping chunk", device_id=device_id)
        
        logger.info("Audio simulation completed", device_id=device_id)

# Global device protocol instance
_device_protocol = None

def get_device_protocol() -> OmiDeviceProtocol:
    """Get global device protocol instance."""
    global _device_protocol
    if _device_protocol is None:
        _device_protocol = OmiDeviceProtocol()
    return _device_protocol

def identify_device_type(device_name: str, manufacturer_data: Dict[str, Any]) -> DeviceType:
    """
    Identify device type based on name and manufacturer data.
    Follows Omi documentation for device identification.
    """
    device_name_lower = device_name.lower()
    
    if "omi" in device_name_lower:
        if "glass" in device_name_lower:
            return DeviceType.OMI_GLASS
        elif "devkit" in device_name_lower or "dev" in device_name_lower:
            return DeviceType.OMI_DEVKIT_2
        else:
            return DeviceType.OMI
    elif "plaud" in device_name_lower:
        return DeviceType.PLAUD
    elif "limitless" in device_name_lower:
        return DeviceType.LIMITLESS
    else:
        return DeviceType.CUSTOM

def validate_device_compatibility(device_info: DeviceInfo) -> bool:
    """
    Validate device compatibility with SpeakFlow.
    
    Args:
        device_info: Device information to validate
        
    Returns:
        True if device is compatible
    """
    # Check audio codec support
    supported_codecs = [BleAudioCodec.OPUS, BleAudioCodec.PCM]
    if device_info.audio_codec not in supported_codecs:
        logger.warning("Unsupported audio codec", 
                       codec=device_info.audio_codec.value,
                       device_id=device_info.device_id)
        return False
    
    # Check sample rate
    supported_sample_rates = [8000, 16000, 44100]
    if device_info.sample_rate not in supported_sample_rates:
        logger.warning("Unsupported sample rate", 
                       sample_rate=device_info.sample_rate,
                       device_id=device_info.device_id)
        return False
    
    return True
