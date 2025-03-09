"""
Extended audio utilities for Windows Core Audio access.

Extends pycaw's AudioUtilities to provide additional functionality
for accessing specific audio devices by ID. This module is particularly
useful for controlling individual audio endpoints in Windows.
"""

from pycaw.pycaw import AudioUtilities
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import (
    AudioUtilities,
    IAudioEndpointVolume,
    CLSID_MMDeviceEnumerator,
    IMMDeviceEnumerator,
    EDataFlow,
    ERole,
)
from ctypes import POINTER, cast


class MyAudioUtilities(AudioUtilities):
    """
    Extended audio utilities with device-specific controls.
    
    Extends pycaw's AudioUtilities class to add functionality for
    getting specific audio devices by their ID.
    """
    
    @staticmethod
    def GetSpeaker(id_=None):
        """
        Get speaker device by ID or default speaker.
        
        Args:
            id_ (str, optional): Device ID to retrieve. If None, returns
                               default audio endpoint.
        
        Returns:
            Speaker device interface
        """
        device_enumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, comtypes.CLSCTX_INPROC_SERVER
        )
        if id_ is not None:
            speakers = device_enumerator.GetDevice(id_)
        else:
            speakers = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)
        return speakers
