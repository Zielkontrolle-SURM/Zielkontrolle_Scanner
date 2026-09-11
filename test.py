import ctypes
from ctypes import wintypes
import win32con
import win32gui

user32 = ctypes.windll.user32

# ----------------------------------------------------------------------
# Raw Input Strukturen
# ----------------------------------------------------------------------

RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003

WM_INPUT = 0x00FF

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


# ----------------------------------------------------------------------
# Hilfsfunktion: GerÃ¤tename ermitteln
# ----------------------------------------------------------------------

def get_device_name(hdevice):
    size = wintypes.UINT(0)

    user32.GetRawInputDeviceInfoW(
        hdevice,
        0x20000007,  # RIDI_DEVICENAME
        None,
        ctypes.byref(size)
    )

    buf = ctypes.create_unicode_buffer(size.value)

    user32.GetRawInputDeviceInfoW(
        hdevice,
        0x20000007,
        buf,
        ctypes.byref(size)
    )

    return buf.value


# Cache für Gerätenamen
device_cache = {}


# ----------------------------------------------------------------------
# Fensterprozedur
# ----------------------------------------------------------------------

def wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_INPUT:

        dw_size = wintypes.UINT(0)

        user32.GetRawInputData(
            lparam,
            RID_INPUT,
            None,
            ctypes.byref(dw_size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        buffer = ctypes.create_string_buffer(dw_size.value)

        user32.GetRawInputData(
            lparam,
            RID_INPUT,
            buffer,
            ctypes.byref(dw_size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        raw = ctypes.cast(
            buffer,
            ctypes.POINTER(RAWINPUT)
        ).contents

        if raw.header.dwType == RIM_TYPEKEYBOARD:

            hdevice = raw.header.hDevice

            if hdevice not in device_cache:
                device_cache[hdevice] = get_device_name(hdevice)

            key = raw.keyboard.VKey

            print(
                f"Key={key:3d} "
                f"DeviceHandle={hdevice} "
                f"Device='{device_cache[hdevice]}'"
            )

        return 0

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


# ----------------------------------------------------------------------
# Verstecktes Fenster anlegen
# ----------------------------------------------------------------------

wc = win32gui.WNDCLASS()
wc.lpszClassName = "RawInputDemo"
wc.lpfnWndProc = wndproc

class_atom = win32gui.RegisterClass(wc)

hwnd = win32gui.CreateWindow(
    class_atom,
    "RawInputDemo",
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    None
)

# ----------------------------------------------------------------------
# Keyboard-RawInput registrieren
# ----------------------------------------------------------------------

rid = RAWINPUTDEVICE()
rid.usUsagePage = 0x01  # Generic Desktop Controls
rid.usUsage = 0x06      # Keyboard
rid.dwFlags = RIDEV_INPUTSINK
rid.hwndTarget = hwnd

if not user32.RegisterRawInputDevices(
        ctypes.byref(rid),
        1,
        ctypes.sizeof(RAWINPUTDEVICE)
):
    raise ctypes.WinError()

print("Warte auf Tastatureingaben...")
win32gui.PumpMessages()