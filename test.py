import ctypes
from ctypes import wintypes
import win32gui

user32 = ctypes.windll.user32  # type: ignore[attr-defined]
GetRawInputData = user32.GetRawInputData  # type: ignore[attr-defined]
GetRawInputDeviceInfoW = user32.GetRawInputDeviceInfoW  # type: ignore[attr-defined]
RegisterRawInputDevices = user32.RegisterRawInputDevices  # type: ignore[attr-defined]

WM_INPUT = 0x00FF
RID_INPUT = 0x10000003
RIDEV_INPUTSINK = 0x00000100
RIDI_DEVICENAME = 0x20000007
RIM_TYPEKEYBOARD = 1


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("keyboard", RAWKEYBOARD),
    ]


def wndproc(window_handle, msg, wparam, lparam):
    if msg == WM_INPUT:
        size = wintypes.UINT()
        GetRawInputData(
            lparam, RID_INPUT, None, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)
        )

        if size.value:
            buffer = ctypes.create_string_buffer(size.value)
            if GetRawInputData(
                lparam, RID_INPUT, buffer, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)
            ) > 0:
                raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents
                if raw.header.dwType == RIM_TYPEKEYBOARD:
                    hdevice = raw.header.hDevice
                    print(f"VKey={raw.keyboard.VKey} | DeviceHandle={hdevice}")
        return 0

    return win32gui.DefWindowProc(window_handle, msg, wparam, lparam)


wc = win32gui.WNDCLASS()  # type: ignore[assignment]
wc.lpszClassName = "KeyboardMap"  # type: ignore[attr-defined]
wc.lpfnWndProc = wndproc  # type: ignore[attr-defined]
class_atom = win32gui.RegisterClass(wc)

window_handle = win32gui.CreateWindow(
    class_atom, "KeyboardMap", 0, 0, 0, 0, 0, 0, 0, 0, None
)

rid = RAWINPUTDEVICE()
rid.usUsagePage = 0x01
rid.usUsage = 0x06
rid.dwFlags = RIDEV_INPUTSINK
rid.hwndTarget = window_handle

if not RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE)):
    raise ctypes.WinError()

print("Warte auf Tastatureingaben...")
win32gui.PumpMessages()
