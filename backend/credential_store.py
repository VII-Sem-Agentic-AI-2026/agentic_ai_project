"""Windows current-user DPAPI encryption for this local development deployment."""
import ctypes,os
from ctypes import wintypes

class Blob(ctypes.Structure):
 _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def transform(raw,encrypt):
 if os.name!='nt':raise ValueError('Portal credential storage requires Windows DPAPI on this deployment')
 buffer=ctypes.create_string_buffer(raw)
 source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
 crypt=ctypes.WinDLL('crypt32',use_last_error=True)
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 fn=crypt.CryptProtectData if encrypt else crypt.CryptUnprotectData
 fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
 fn.restype=wintypes.BOOL
 kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
 if not fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):
  raise ValueError('Unable to access encrypted credentials for this Windows account')
 try:return ctypes.string_at(target.data,target.size)
 finally:kernel.LocalFree(target.data)

def save(path,payload):
 encrypted=transform(payload,True)
 path.parent.mkdir(parents=True,exist_ok=True)
 temporary=path.with_suffix('.tmp')
 try:
  temporary.write_bytes(encrypted);os.replace(temporary,path)
 finally:
  if temporary.exists():temporary.unlink()

def read(path):return transform(path.read_bytes(),False)
